# AI Agent Rules for Parqcast Workspace

This document defines the constraints, architecture boundaries, and tooling instructions for AI coding assistants working in the `parqcast` repository. Before generating or editing code, agents must understand and adhere strictly to these rules.

## 1. Toolchain & Workspace Constraints
- **Workspace Tool**: The project uses `uv` as the workspace manager. All dependency management and command running must go through `uv` (e.g., `uv sync`, `uv run pytest`).
- **Strict Type Checking**: We use `pyright` in strict mode. All new code must pass `uv run pyright` without generating `Unknown` or `Any` leakage. Avoid casting unless interfacing with dynamic ORM attributes, and even then, rely on `pyproject.toml` suppressions where configured.
- **Linting & Formatting**: Code must pass `uv run ruff check .` and `uv run ruff format --check .`. The configured line length is 120. **Agents must ALWAYS run `uv run ruff check --fix .` and `uv run ruff format .` prior to making any commits to ensure the CI pipeline does not fail.**

## 2. Architecture Boundaries
Parqcast is strictly layered. Agents must NEVER introduce imports that violate these boundaries:
- **`packages/parqcast-core/`**: Defines data schemas, pyarrow constructs, and protocol interfaces. **Constraint:** Must NEVER import from `odoo`, `psycopg2`, or any other workspace package.
- **`packages/parqcast-collectors/`**: Executes fast raw SQL queries using `psycopg2` to build arrow arrays. **Constraint:** Must NEVER import `odoo` ORM models.
- **`packages/parqcast-ingesters/`**: Pulls data via Odoo ORM to push planning decisions back. This is the ONLY python package (outside the addon itself) permitted to use dynamic Odoo typing.
- **`packages/parqcast-transport-http/`**: Handles HTTP uploads of generated chunks.
- **`packages/parqcast/`**: The Odoo addon. It bridges the environment with the workspace packages. **Constraint:** Must pass Odoo Community Association (OCA) linting via `bash scripts/oca_lint.sh`. Must **NEVER** contain inline raw SQL queries (`cr.execute`); all tracking SQL is delegated to `packages/parqcast-core`. Transports must be decoupled and registered via `parqcast/utils/transport_registry.py`.

## 3. Odoo Versioning (PEP 695 Generics)
Parqcast certifies per Odoo major. 
- Do not use dynamic runtime version checks in core logic.
- Instead, use PEP 695 generics (`type V18`, `type V19`) to tag and enforce version-specific implementations at compile time. Pyright enforces that a `V18` component cannot be accidentally mixed with a `V19` context.
- For local type checking of Odoo symbols, use the `stubs/odoo-stubs/` local directory.

## 4. Testing
- Use `uv run pytest tests/ -x -q` to verify logic.
- Do not run `tests/test_live_db.py` without the `PARQCAST_TEST_DB` environment variable set.

## 5. Data Architecture & Schemas
When answering questions about what data is available, writing SQL extractors, or modifying PyArrow schemas, you MUST first read `docs/DATA_DICTIONARY.md`. 
* All outbound schemas are defined and strictly typed in `packages/parqcast-core/src/parqcast/schemas/outbound.py`.
