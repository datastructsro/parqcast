# Parqcast

Zero-computation data pipe between Odoo and cloud planning engines.

## Setup

This is a **uv workspace** with multiple packages. Uses [uv](https://docs.astral.sh/uv/) for dependency management and building.

```bash
uv sync                    # install all workspace packages + dev deps
uv run pytest              # run tests
uv run ruff check .        # lint
uv run ruff format .       # format
```

## Testing

```bash
uv run pytest tests/ -x -q                                   # all unit tests
uv run pytest tests/ -x -q --ignore=tests/test_live_db.py    # skip live DB tests
```

`test_live_db.py` requires a running PostgreSQL with an Odoo database. All other tests are self-contained.

## Workspace packages

```
packages/
  parqcast-core/        # schemas, transport, tracking, capabilities, manifest, protocols
  parqcast-collectors/  # SQL-based collectors, factory, orchestrator
  parqcast-ingesters/   # ORM-based data writers, receiver
  parqcast-odoo/        # Odoo addon: settings UI, cron job, env adapter
  parqcast-lambda/      # AWS Lambda handler, S3 transport
```

**Dependency flow:** `parqcast-core` <- `parqcast-collectors` <- `parqcast-lambda`
                     `parqcast-core` <- `parqcast-ingesters`

Uses **implicit namespace packages** — all imports start with `parqcast.*` across package boundaries. No `__init__.py` at `src/parqcast/` level in any package.

### parqcast-core (pyarrow only)
- `parqcast.core` - `__version__`, protocols (`DatabaseEnv`, `ReadCursor`, `Connection`)
- `parqcast.core.capabilities` - Odoo database introspection and feature detection
- `parqcast.core.tracking` - Export progress tracking (raw SQL, survives cron restarts)
- `parqcast.core.manifest` - Per-export manifest builder
- `parqcast.schemas` - Pure PyArrow schema definitions
- `parqcast.transport` - Pluggable upload/download (base + local filesystem)

### parqcast-collectors (depends: parqcast-core)
- `parqcast.collectors` - SQL-based data extractors (one per Odoo model group)
- `parqcast.collectors.factory` - Probes database, instantiates compatible collectors
- `parqcast.orchestrator` - Time-budgeted state machine for cron-safe execution

### parqcast-ingesters (depends: parqcast-core)
- `parqcast.ingesters` - ORM-based data writers (push planning decisions back into Odoo)
- `parqcast.receiver` - Download decisions.parquet and dispatch to ingesters

### parqcast-odoo (Odoo addon, not a workspace member)
- `models/env_adapter.py` - Wraps Odoo env into the `DatabaseEnv` protocol
- `models/parqcast_settings.py` - Settings UI (transport type, path, time budget)
- `models/parqcast_cron.py` - ir.cron scheduled action for export

### parqcast-lambda (depends: parqcast-collectors)
- `parqcast.lambda_handler` - AWS Lambda entry point
- S3 transport + direct psycopg2 `LambdaEnv` adapter

## Conventions

- Build backend: `hatchling` for workspace members, `uv_build` for root
- Python 3.13+, ruff for linting/formatting
- Collectors use raw SQL (not Odoo ORM) for read performance
- Ingesters use full Odoo ORM (env["model"])
- Parquet files use snappy compression and carry `parqcast_version` + `odoo_version` in file metadata
- The `DatabaseEnv` protocol (`parqcast.core.protocols`) decouples database access from Odoo — adapters in parqcast-odoo and parqcast-lambda satisfy it differently
