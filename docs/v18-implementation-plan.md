# Odoo 18 Support — Implementation Plan for a Coding Agent

**Branch:** `feat/v18-support` (already created from `main`, ~zero commits ahead).
**Author context:** The v19 isolation work landed in PR #1 (merged). This plan mirrors that structure for v18.
**Intended reader:** A coding agent taking over without prior session context.

---

## 0. Read this first

Three files are non-optional reading before writing code:

1. [`docs/versioning-plan.md`](./versioning-plan.md) — the overall per-version isolation design. You are executing a second instance of its blueprint.
2. [`docs/odoo-18-vs-19-evidence.md`](./odoo-18-vs-19-evidence.md) — file:line citations for every known v18↔v19 schema drift. Treat this as the *starting* list, not the complete one; you must verify against the live DB (see §3).
3. [`packages/parqcast-collectors/src/parqcast/collectors/v19/bundle.py`](../packages/parqcast-collectors/src/parqcast/collectors/v19/bundle.py) — the template you are mirroring for v18. Everything `v19/` has, `v18/` will have an analogue.

The v19 bundle registers `V19`-tagged collectors, ingesters, suites, and a capabilities probe into `parqcast.core.registry.REGISTRY`. Your job is to produce the `V18` equivalent.

---

## 1. Environment — already set up

- **Repo:** `/Users/thatoleg/datastructsro/parqcast`, branch `feat/v18-support`.
- **Odoo 18 source trees:** `/Users/thatoleg/datastructsro/replenishment-investigation/community-18/` and `enterprise-18/`. These are *checked-out*, not pip-installed — reference them with `--addons-path=`.
- **Odoo 18 venv:** `/Users/thatoleg/datastructsro/replenishment-investigation/.venv/` (Python 3.12.3, Odoo 18 installed editable). Use this to run `odoo-bin` or introspect ORM models.
- **Demo database:** `parqcast_v18_demo` on `localhost:5432` as user `thatoleg` (unix socket, no password). Created with modules `mrp, sale_management, purchase, stock, point_of_sale` + demo data. 130 modules installed, 97 products, 24 SOs, 11 POs, 6 MOs.

If the demo DB is lost or you need a fresh one:

```bash
dropdb parqcast_v18_demo
createdb parqcast_v18_demo
/Users/thatoleg/datastructsro/replenishment-investigation/.venv/bin/python \
  /Users/thatoleg/datastructsro/replenishment-investigation/community-18/odoo-bin \
  -d parqcast_v18_demo \
  --init=mrp,sale_management,purchase,stock,point_of_sale \
  --stop-after-init \
  --addons-path=/Users/thatoleg/datastructsro/replenishment-investigation/community-18/addons,\
/Users/thatoleg/datastructsro/replenishment-investigation/enterprise-18 \
  --db_host=localhost --db_port=5432 --db_user=thatoleg \
  --log-level=warn
```

**Do not pass `--without-demo=False`** — Odoo parses the non-empty string "False" as "disable demo for the module named False", which disables demo entirely. Demo is the default behavior; omit the flag.

---

## 2. Scope — decide before coding

Lock these with the user *before* landing commits. Don't assume:

| Question | Options | Current answer (change if the user says otherwise) |
|---|---|---|
| Which suites to port? | All 7 (core/stock/sale/purchase/mrp/pos/enterprise), or a subset? | **Default: all 7**, mirroring v19. |
| Ingesters too? | Port all 5 actors, or export-only? | **Default: yes, all 5** (production feedback loop is likely symmetric). |
| Distribution model? | (a) Parallel `feat/v18` branch with its own addon release; (b) One addon bundling both `v18/` and `v19/`, picked at runtime by the gate. | **Default: (b) single addon, both bundles**. The registry already supports this — see `registry.py:46`. Requires bumping `parqcast_supported_versions` in the manifest from `("19",)` to `("18", "19")`. |
| Outbound Parquet schema stability? | Must be identical across v18 and v19 (it's the Snowflake contract), or version-tagged? | **Default: identical.** Fill missing columns with `NULL` / default values; never change `parqcast-core/src/parqcast/core/schemas/outbound.py`. |

If the user has not answered, ask once, then proceed with the defaults if no reply.

---

## 3. Evidence-first process (per collector)

The v18↔v19 evidence doc is your **starting hypothesis list**, not the final answer. Before writing or migrating any collector, run this three-step check against the live v18 DB:

1. **Read the v19 collector's SQL** (in `packages/parqcast-collectors/src/parqcast/collectors/v19/<name>.py`).
2. **Compare column references to the v18 schema:**
   ```bash
   psql -d parqcast_v18_demo -c "\\d <table_name>"
   ```
   For every column the v19 SQL names, confirm v18 has an identically-named column. Anything mismatched is a drift to handle.
3. **Dry-run the v19 SQL against v18** by executing it directly in psql. Three outcomes:
   - Succeeds with sensible rows → copy as-is into `v18/<name>.py`.
   - Errors on a missing column → cross-reference `community-18/addons/<module>/models/<model>.py` to find the v18 name; patch the SQL.
   - Succeeds but returns wrong data (Severity B in the evidence doc) → rewrite the SQL; add a regression test.

**Do not shortcut.** A collector that "compiles" against v18 but returns semantically wrong rows is worse than one that errors loudly — and the outbound Parquet is a contract with Snowflake.

---

## 4. Code structure (what to produce)

Mirror v19 exactly. Every file below has a v19 twin you can copy and adapt.

### New files

```
packages/parqcast-core/src/parqcast/core/
  version.py                       # add `class V18: ...`, expand SupportedVersionStr

packages/parqcast-collectors/src/parqcast/collectors/v18/
  __init__.py
  bundle.py                        # mirrors v19/bundle.py, registers via append_to_bundle("18", ...)
  uom.py                           # UomCollectorV18 — uom.category still exists in v18 (evidence §1)
  product.py                       # ProductCollectorV18
  orderpoint.py                    # OrderpointCollectorV18
  stock_*.py                       # ~12 stock collectors
  sale_order.py                    # + sale_order_line.py
  purchase_*.py                    # 3 files: order, order_line, requisition
  pricelist.py                     # PricelistCollectorV18, PricelistItemCollectorV18
  product_supplierinfo.py          # ProductSupplierinfoCollectorV18
  product_removal.py               # ProductRemovalCollectorV18
  mrp_*.py                         # bom, production, workorder
  workcenter.py                    # WorkcenterCollectorV18, WorkcenterCapacityCollectorV18
  pos_order.py                     # PosOrderCollectorV18, PosOrderLineCollectorV18
  pos_session.py                   # PosSessionCollectorV18
  mps.py                           # MpsForecastCollectorV18, MpsScheduleCollectorV18 (enterprise)
  quality.py                       # QualityCheckCollectorV18, QualityPointCollectorV18 (enterprise)

packages/parqcast-ingesters/src/parqcast/ingesters/v18/
  __init__.py
  distribution_actor.py            # DistributionActorV18
  orderpoint_actor.py              # OrderpointActorV18
  production_actor.py              # ProductionActorV18
  purchase_actor.py                # PurchaseActorV18 — watch product_uom/product_uom_id drift (evidence §2)
  reschedule_actor.py              # RescheduleActorV18
```

### Modified files

```
packages/parqcast-core/src/parqcast/core/
  version.py                       # add V18; SupportedVersionStr → Literal["18", "19"]
  registry.py:49 _bootstrap()      # add REGISTRY.setdefault("18", VersionBundle(version_str="18"))
  capabilities.py                  # add probe_v18() returning OdooCapabilities[V18]

packages/parqcast-collectors/src/parqcast/collectors/__init__.py
  # import parqcast.collectors.v18.bundle so the registry fills on import

packages/parqcast-ingesters/src/parqcast/ingesters/__init__.py
  # likewise for v18 ingesters

packages/parqcast/__manifest__.py
  # if distribution option (b): "parqcast_supported_versions": ("18", "19")
  # if distribution option (a): leave as ("19",) — this branch never merges to main

tests/test_version_gate.py
  # add cases: v18 DB → bundle resolves; v17 DB → raises
tests/test_capabilities.py
  # add a probe_v18 smoke test
```

### Untouched files (do not modify)

- `packages/parqcast-core/src/parqcast/core/schemas/outbound.py` — the Snowflake contract. Filling NULLs in collectors is correct; changing schema is not.
- `packages/parqcast-collectors/src/parqcast/collectors/base.py` — version-neutral abstract class. No change needed.
- `packages/parqcast-collectors/src/parqcast/orchestrator/__init__.py` — already bundle-driven. No change.
- `packages/parqcast/models/env_adapter.py` — psycopg2-level adapter. Version-independent.

---

## 5. Known drift from the evidence doc

The evidence doc (`docs/odoo-18-vs-19-evidence.md`) is authoritative for what it covers. Key items that affect the coding work:

| Area | v18 → v19 drift | Where it hits you |
|---|---|---|
| §1 `uom.category` | Exists in v18, removed in v19. v18 UOM collector queries `uom_category` directly (the v19 one joins `uom_uom.relative_uom_id`). | `v18/uom.py` — different SQL from v19. |
| §2 `purchase_order_line.product_uom` | v18: `product_uom`. v19: `product_uom_id`. | `v18/purchase_order_line.py` AND `ingesters/v18/purchase_actor.py` (the v19 rename bug was fixed at migration time; v18 actor must use the v18 name). |
| §3 `stock_location.scrap_location` | Exists in v18, gone in v19. `return_location` is folklore — not present in either. Grep before trusting. | `v18/stock_location.py`. |
| §4 `mrp.routing.workcenter.time_cycle` | **Erratum.** The compute body is identical in v18 and v19; only the display label changed. No SQL change needed. | No action. But read the erratum before second-guessing it. |

Everything beyond the evidence doc you must discover empirically (§3 process).

---

## 6. Commit sequence

Small commits, each individually green under pyright strict and pytest. Rough sketch — adjust as evidence demands:

| # | Commit | Verification |
|---|---|---|
| 1 | `feat(core): add V18 phantom tag + empty bundle bootstrap` | `uv run pyright` 0/0/0; tests pass |
| 2 | `feat(core): add probe_v18 capabilities function` | add `probe_v18` smoke test; pyright clean |
| 3 | `feat(collectors): pilot v18 with core suite (uom, product, partner)` | Live DB query returns rows; pyright clean |
| 4 | `feat(collectors): v18 stock suite` | Live DB export produces Parquet matching outbound schema |
| 5 | `feat(collectors): v18 sale suite` | same |
| 6 | `feat(collectors): v18 purchase suite` | same — watch `product_uom` |
| 7 | `feat(collectors): v18 mrp suite` | same |
| 8 | `feat(collectors): v18 pos suite` | same |
| 9 | `feat(collectors): v18 enterprise suite (mps, quality)` | same (only if enterprise modules installed) |
| 10 | `feat(ingesters): migrate ingesters to v18 with V18 suffix` | Writebacks round-trip through v18 demo DB |
| 11 | `feat(addon): register v18 in manifest + version gate tests` | Gate test: v18 DB accepted, v17 DB rejected |
| 12 | `docs: record v18 support in versioning plan + README` | No code change |

Do not batch commits 3-9 — each suite is its own reviewable unit and may surface drift the next one depends on.

---

## 7. Testing

Three layers, all must pass:

### 7a. Pyright strict (no regressions)

```bash
uv run pyright
# Expected: 0 errors, 0 warnings, 0 informations
```

The existing `executionEnvironments` block in `pyproject.toml` already covers `packages/parqcast-ingesters/src/parqcast/ingesters/v19` — extend `root` to match both v18 and v19 (use a glob, or duplicate the block for v18).

### 7b. Unit tests

```bash
uv run pytest tests/ -q
# Expected: 46+ passed, 1 skipped (the live-DB test skips unless env vars set)
```

Add gate tests for v18 — mirror `tests/test_version_gate.py`'s existing v19 cases.

### 7c. Live-DB integration

```bash
PARQCAST_TEST_DB=parqcast_v18_demo \
PARQCAST_TEST_ODOO_VERSION=18 \
  uv run pytest tests/test_live_db.py -q
```

If `tests/test_live_db.py` currently hard-codes v19, generalise it to parameterise on `PARQCAST_TEST_ODOO_VERSION` and look up the bundle from the registry.

### 7d. End-to-end export

Run the orchestrator against the demo DB and inspect the Parquet output:

```bash
PARQCAST_TEST_DB=parqcast_v18_demo \
  uv run python -c "
from parqcast.collectors.v18 import bundle  # triggers registration
from parqcast.core.registry import REGISTRY
from parqcast.orchestrator import Orchestrator
# ... wire up OdooEnvShim from tests/test_live_db.py and invoke Orchestrator.run()
"
```

Open the Parquet files with pyarrow and confirm schemas match v19's outputs. The Snowflake contract is the acceptance criterion.

---

## 8. Failure modes to expect

- **Field renames beyond the evidence doc.** Use `git grep -rn 'product_uom' community-18/addons/purchase/` style searches against the Odoo source trees to catch them. If a rename is not in the evidence doc, update the evidence doc as part of your commit.
- **Modules with different names.** `sale_management` exists in both, but `sale` is the actual technical module name used by capabilities. Double-check which you reference.
- **Enterprise-only modules.** `mrp_mps`, `quality_control` live under `enterprise-18/`, not `community-18/addons/`. The addons-path already includes both, but the module `_name` may differ.
- **The registry import ordering trap.** `collectors/__init__.py` must import `v18.bundle` for registration to fire — but the bundle file itself imports individual collectors, which import `parqcast.core.registry`. Keep the chain linear; don't introduce cycles. Mirror v19's pattern.
- **Pyright strict catching what runtime wouldn't.** When a v18 collector has a different SQL from v19 but the same class hierarchy, pyright may still flag type mismatches on overridden methods. Resolve the types, don't paper over with `# type: ignore`.

---

## 9. Out of scope

- **v20.** Not until Odoo 20 ships. The phantom-tag pattern makes it a local addition when it does.
- **Backporting v19-specific features to v18.** If v19's `uom.uom.parent_path` enables a query v18 simply can't serve, the v18 collector returns NULL for that column. Do not invent synthetic values.
- **Changing the outbound Parquet schema.** It's the Snowflake contract. New columns that v19 can fill and v18 can't → v18 fills NULL. Full stop.
- **Publishing the stub package at `stubs/odoo-stubs/`.** Stays project-local. If a sibling repo needs it later, promote it then — not now.

---

## 10. Done criteria

When all of the following are true, the work is ready for PR:

- [ ] `uv run pyright` → 0 errors, 0 warnings, 0 informations.
- [ ] `uv run pytest tests/ -q` → same pass count as `main` plus any new v18 tests (46+ passed).
- [ ] With `PARQCAST_TEST_DB=parqcast_v18_demo PARQCAST_TEST_ODOO_VERSION=18`, the live-DB suite passes.
- [ ] End-to-end export against the demo DB produces Parquet files whose schemas are byte-identical to v19's (same columns, same types, same order).
- [ ] `docs/versioning-plan.md` has a "Step 10" row pointing at the v18 work. `docs/odoo-18-vs-19-evidence.md` is updated for any drift encountered that wasn't already documented.
- [ ] Version gate tests cover: v18 DB → accepted; v17 DB → rejected; unknown DB → rejected.
