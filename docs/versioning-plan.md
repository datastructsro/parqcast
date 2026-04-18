# Per-Odoo-Version Type Isolation Plan

## Goal

Make Odoo version compatibility a **compile-time property** and a **hard runtime gate**:

- Every type that touches Odoo's schema/API carries a version suffix (`V19`, later `V20`, …).
- The type checker refuses to mix versions (you cannot hand a `ProductCollectorV19` to a `PipelineV20`).
- At addon install / module register, we probe the live Odoo version. If unsupported → refuse to load. No silent degradation.
- Shared machinery (transport, tracking, orchestrator, output PyArrow schemas) stays version-agnostic so we do not duplicate code we don't have to.

Low-maintenance means: when Odoo 20 lands, we add a `v20/` subpackage and a one-line registry entry. The compiler tells us everything we forgot; the runtime refuses to load until we've done it.

---

## What actually varies per Odoo version

Only these touch Odoo-version-specific surface area:

| Layer | Varies? | Why |
|---|---|---|
| SQL collectors (`parqcast-collectors`) | **Yes** | Table/column renames, JSONB vs scalar translatable fields, computed-vs-stored flips (e.g. `orderpoint.qty_on_hand` computed in 19). |
| ORM ingesters (`parqcast-ingesters`) | **Yes** | Odoo model field renames (`product_uom` → `product_uom_id`), `create()` payload shape. |
| `OdooAdapter` psycopg2 introspection | **Maybe** | `cr._cnx` path can shift across versions. |
| PyArrow **outbound** schemas (`parqcast-core/schemas/outbound.py`) | **No** | These are the contract to Snowflake. They must stay stable regardless of source version. |
| Transport, tracking (`ExportRun`/`ExportChunk`), orchestrator | **No** | Pure parqcast-internal. |
| Capabilities probe | **Partially** | Shape is stable; *what it probes for* may grow per version. |

Corollary: **only version-suffix the things that genuinely differ.** A blanket `V19` on every symbol is noise and will make diffs unreadable when v20 arrives.

---

## Design

### 1. Version tag types (phantom generics)

`packages/parqcast-core/src/parqcast/core/version.py` (new):

```python
from typing import Literal, TypeAlias

# Sentinel types — never instantiated, only used as generic parameters.
class V19: ...
# class V20: ...  # add when supported

SupportedVersionTag: TypeAlias = type[V19]       # union grows: type[V19] | type[V20]
SupportedVersionStr: TypeAlias = Literal["19"]   # likewise
```

These are *phantom* types — pure type-checker signal. Zero runtime cost. Using PEP 695 generic syntax (Python 3.12+) downstream:

```python
class Collector[V]:   # V is phantom; constrains what the pipeline accepts
    ...

class ProductCollectorV19(Collector[V19]):
    ...
```

A function typed `def run(collectors: list[Collector[V19]]) -> None` will be rejected by mypy/pyright if you pass in a `Collector[V20]`. That is the compile-time guarantee you asked for.

### 2. Per-version subpackages

Reshape `parqcast-collectors` and `parqcast-ingesters`:

```
packages/parqcast-collectors/src/parqcast/collectors/
  base.py                # CollectorBase[V]: generic abstract base (shared)
  factory.py             # deleted or flattened — replaced by per-version registries
  v19/
    __init__.py          # exports V19_COLLECTORS: list[Collector[V19]]
    product.py           # ProductCollectorV19(CollectorBase[V19])
    uom.py               # UomCollectorV19
    orderpoint.py        # OrderpointCollectorV19
    …                    # one file per current collector, class renamed with V19 suffix
```

```
packages/parqcast-ingesters/src/parqcast/ingesters/
  base.py
  v19/
    purchase_actor.py    # PurchaseActorV19
    production_actor.py  # ProductionActorV19
    …
```

Rule: **classes live in `v{N}/` iff they contain version-sensitive SQL or ORM field names.** If a collector is purely `SELECT id, create_date FROM <table>` and that's stable, it stays version-agnostic in the parent. In practice almost all collectors touch something version-sensitive, so expect ~90% to move.

### 3. Version registry

`packages/parqcast-core/src/parqcast/core/registry.py` (new):

```python
from dataclasses import dataclass
from parqcast.core.version import V19, SupportedVersionStr

@dataclass(frozen=True)
class VersionBundle[V]:
    version_str: SupportedVersionStr
    collectors: tuple[Collector[V], ...]
    ingesters: tuple[Ingester[V], ...]
    capabilities_probe: Callable[[Cursor], OdooCapabilities[V]]

# Populated at import time from each vN subpackage.
REGISTRY: dict[SupportedVersionStr, VersionBundle] = {}
```

`parqcast-collectors/v19/__init__.py` registers its bundle; adding v20 is a new `v20/__init__.py` that does the same. Orchestrator asks the registry by `SupportedVersionStr`, never constructs directly.

### 4. Runtime version gate — two layers

**Layer A — eager, on Odoo registry load (preferred):**

Add a sentinel model in `packages/parqcast/models/parqcast_version_gate.py`:

```python
class ParqcastVersionGate(models.AbstractModel):
    _name = "parqcast.version.gate"

    def _register_hook(self):
        # Runs once per DB when the registry is built.
        super()._register_hook()
        from parqcast.core.version_gate import assert_supported
        assert_supported(self.env.cr)  # raises UnsupportedOdooVersionError
```

`assert_supported(cr)`:

1. Queries `ir_module_module` for Odoo version (same query capabilities probe already uses).
2. Parses major version (e.g. `"19.0"` → `"19"`).
3. If major not in `REGISTRY` → raise `UnsupportedOdooVersionError` with message: "Parqcast {pkg_version} supports Odoo {sorted(REGISTRY)}; this DB is Odoo {detected}. Install a matching parqcast release."
4. Raising from `_register_hook` aborts module load for that DB. Exactly what you want.

**Layer B — defense in depth, at cron tick:**

In `parqcast_cron.py::run_export`, call the same `assert_supported` before `OdooAdapter(self.env)`. Cheap, catches the edge case where a multi-DB Odoo.sh instance has mixed versions and Layer A ran on the wrong one.

### 5. Manifest declares supported versions

`packages/parqcast/__manifest__.py`:

```python
"parqcast_supported_versions": ("19",),  # custom key, read by the gate
"version": "19.0.2.0.0",                 # Odoo-addon version — leading "19.0" already scopes
```

The manifest `version` field's `19.0` prefix is Odoo's own way of saying "this addon is for 19". Keep it honest. When you add v20, publish as a separate branch/release with manifest `version = "20.0.2.0.0"` and `parqcast_supported_versions = ("20",)` — **one addon, one Odoo major**, matching Odoo's certification model.

(Do not try to ship a single wheel that claims to support both 19 and 20. Odoo.sh/App Store certify per major. Two branches, two releases.)

### 6. OdooCapabilities becomes generic

`OdooCapabilities` today is a single frozen dataclass. Make it generic so downstream code keeps its version tag:

```python
@dataclass(frozen=True)
class OdooCapabilities[V]:
    odoo_version: str
    ...

def probe_v19(cr) -> OdooCapabilities[V19]: ...
```

A `CollectorV19` that takes `OdooCapabilities[V19]` cannot be handed a `OdooCapabilities[V20]`. Same pattern as collectors.

### 7. What does **not** change

- `parqcast-core/schemas/outbound.py` — PyArrow schemas stay as-is. They are the Snowflake contract; intentionally version-invariant. If Odoo 20 exposes new fields, *add columns* rather than *branch the schema*; downstream readers must keep working.
- `parqcast-core/schemas/odoo_types.py` — these are PyArrow dtype aliases (`OdooId = pa.int64()` etc.). No version coupling. Keep shared.
- `parqcast-core/tracking.py` (`ExportRun`, `ExportChunk`) — parqcast-internal, Postgres-only, unrelated to Odoo version.
- Transports — plain HTTP/S3/local FS, zero Odoo coupling.
- Orchestrator — receives a `VersionBundle`, runs it. Version-agnostic.

### 8. Tests

- Unit tests for collectors move under `tests/collectors/v19/`. Identical structure mirrors the package.
- Live-DB integration tests (`test_live_db.py`) already gate on `PARQCAST_TEST_DB`. Add a second env var `PARQCAST_TEST_ODOO_VERSION=19` and skip-on-mismatch. When v20 arrives, add `tests/collectors/v20/` that skips unless `=20`.
- Add one **gate test**: spin up `assert_supported` against a stubbed cursor that reports version `18` → expect `UnsupportedOdooVersionError`.

---

## Migration path — implemented

The plan above landed across 15 commits on branch `feat/per-version-types`
(authored 2026-04-18). All originally-listed steps are done; the summary
below points to the commit that implemented each step.

| Step | Status | Implementing commit |
|---|---|---|
| 1 | ✔ landed | `feat(core): add runtime Odoo-version gate with empty registry` |
| 2 | ✔ landed | `feat(addon): add _register_hook version gate` |
| 3 | ✔ landed | `feat(core): make OdooCapabilities generic in V; add probe_v19` |
| 4 | ✔ landed | One commit per suite (core/uom+product pilot, stock, sale, purchase, mrp, pos, enterprise) |
| 5 | ✔ landed | `feat(ingesters): migrate ingesters to v19/ with V19 suffix` |
| 6 | ✔ landed | `feat(cutover): registry replaces factory + suites; version-neutral orchestrator` |
| 7 | ✔ landed | `feat(tooling): add pyright strict type-checking config` |
| 8 | ✔ landed | This commit |

Tests: 46 pass (0 skipped without `PARQCAST_TEST_DB`), pyright strict: 0 errors.

Runtime verification still to perform: (a) install the resulting addon on
the production Odoo 19 database and confirm the cron still runs, (b) point
the addon at an Odoo 18 database and confirm `_register_hook` raises
`UnsupportedOdooVersionError`.

---

## Non-goals / explicitly rejected

- **Shared code with `if odoo_version >= 20:` branches.** This is exactly the maintenance trap the plan avoids. Version-specific logic lives in version-specific modules, period.
- **Runtime feature flags per Odoo version.** The capabilities probe already handles "module X installed / not installed" within a single version. That is orthogonal to the major-version gate and stays unchanged.
- **Supporting multiple Odoo majors from one wheel.** Odoo's own addon model is one major per release. Match it.
- **Abstracting over an "Odoo API" facade so collectors become version-free.** Tried-and-failed pattern in the Odoo ecosystem; the ORM surface is too wide and the facade rots faster than the code it wraps. Accept the duplication across v19/v20 — it is bounded (one module per Odoo major, ~50 files) and reviewable.

---

## Open questions — resolved

1. **pyright vs mypy** — **Resolved:** pyright strict. Wired into
   `pyproject.toml` with sensible suppressions for `Unknown*` diagnostics
   that stem from pyarrow and psycopg2 shipping without type stubs.
2. **v20 timeline** — **Resolved:** out of scope for this branch. The
   registry, phantom generics, and suite abstraction are shaped so that
   adding a `v20/` subpackage is a local change.
3. **Addon distribution** — **Resolved (deferred):** no change to the
   current distribution model in this branch. The manifest now advertises
   `parqcast_supported_versions = ("19",)` which reviewers can use to
   triage branch-per-major releases later.

## Erratum note

An earlier version of `docs/odoo-18-vs-19-evidence.md` §4 claimed
`mrp.routing.workcenter.time_cycle` silently changed its unit of
measurement from minutes to cycle count between v18 and v19, making it a
"dangerous semantic flip." That conclusion was wrong — the compute body
is identical in both versions; only the display label changed. The
corrected §4 is in the evidence doc and the mrp collector docstring was
fixed in the mrp-suite migration commit.
