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

## Setup

Requires Python 3.12.3 (Odoo.sh compatibility).

```bash
uv sync                    # install workspace + dev deps
uv run ruff check .        # lint
uv run ruff format .       # format
```

## Testing

```bash
uv run pytest tests/ -x -q --ignore=tests/test_live_db.py   # unit tests only
uv run pytest tests/ -x -q                                  # incl. live DB integration
```

`tests/test_live_db.py` runs against a real Odoo PostgreSQL database. Set `PARQCAST_TEST_DB` (e.g. in `.env`) to enable it — otherwise the module is skipped.

## Development scripts

| Script | Purpose |
|--------|---------|
| `scripts/gen_readme.sh` | Regenerate `packages/parqcast/README.rst` from `readme/*.md` fragments |
| `scripts/gen_pot.sh` | Regenerate the `.pot` translation template |
| `scripts/oca_lint.sh` | Run OCA lint checks |

## License

LGPL-3.0-or-later
