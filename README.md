# Parqcast

Zero-computation data pipe from Odoo 19 to cloud planning engines. Exports sale orders, products, inventory, purchasing, and warehouse data as Parquet files — ready for demand forecasting, MRP planning, or BI analytics.

**Author:** [DataStruct s.r.o.](https://datastruct.tech) — info@datastruct.tech

## Workspace

This repo is a `uv` workspace with four Python packages plus the Odoo addon:

| Path | Purpose |
|------|---------|
| `packages/parqcast-core/` | Schemas, transport, tracking, capabilities, manifest, protocols (pyarrow only) |
| `packages/parqcast-collectors/` | SQL-based data extractors + time-budgeted orchestrator |
| `packages/parqcast-ingesters/` | ORM-based writers (push planning decisions back into Odoo) |
| `packages/parqcast-transport-http/` | HTTP upload transport |
| `packages/parqcast/` | The Odoo 19 addon (settings UI, cron job, env adapter) — see [its README](packages/parqcast/README.rst) |

Related repos: [parqcast-server](https://github.com/datastructsro/parqcast-server) (HTTP receiver), [parqcast-lambda](https://github.com/datastructsro/parqcast-lambda) (AWS Lambda handler + S3 transport).

## Odoo version support

Parqcast certifies per Odoo major — matching Odoo's own distribution model.
Each Odoo major gets its own release branch and its own addon package; a
single parqcast install supports exactly one Odoo major.

Compile-time: all Odoo-version-specific types carry a version suffix
(`ProductCollectorV19`, `PurchaseActorV19`, …) and are parameterised by a
phantom `V19` tag via PEP 695 generics. Pyright in strict mode refuses any
attempt to mix a `V19`-tagged value where a `V20`-tagged one is expected.

Runtime: on addon install/upgrade, `parqcast.version.gate._register_hook`
reads the connected DB's `ir_module_module.latest_version` and raises
`UnsupportedOdooVersionError` if the detected major is not in the bundle
registry. The cron tick repeats the check as defense in depth.

Currently supported: Odoo 19.

## Setup

Requires Python 3.12.3 (Odoo.sh compatibility).

```bash
uv sync                    # install workspace + dev deps
uv run ruff check .        # lint
uv run ruff format .       # format
uv run pyright             # strict type check (must pass cleanly)
```

Pyright runs in `strict` mode across the whole workspace, addon
included. Odoo isn't pip-installable, so the addon's `from odoo
import …` resolves through a project-local stub package at
`stubs/odoo-stubs/` (wired via `[tool.pyright].stubPath`). The stubs
cover only what parqcast actually touches; extending them is a
two-minute change.

## Testing

```bash
uv run pytest tests/ -x -q --ignore=tests/test_live_db.py   # unit tests only
uv run pytest tests/ -x -q                                  # incl. live DB integration
```

`tests/test_live_db.py` runs against a real Odoo PostgreSQL database. Set
`PARQCAST_TEST_DB` (e.g. in `.env`) to enable it — otherwise the module is
skipped. Also honours `PARQCAST_TEST_ODOO_VERSION` (default `"19"`); the
module skips if the value is not a registered bundle.

## Development scripts

| Script | Purpose |
|--------|---------|
| `scripts/gen_readme.sh` | Regenerate `packages/parqcast/README.rst` from `readme/*.md` fragments |
| `scripts/gen_pot.sh` | Regenerate the `.pot` translation template |
| `scripts/oca_lint.sh` | Run OCA lint checks |

## License

LGPL-3.0-or-later
