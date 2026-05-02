# Gemini Code Assist Context (Parqcast)

This file provides workspace context and system instructions specifically tailored for Google Gemini Code Assist and Gemini-powered agents (like Antigravity) working in the `parqcast` repository.

## 1. Universal Project Rules
Gemini must strictly adhere to the universal architectural boundaries defined in **`AGENTS.MD`**. 
* **Do not duplicate those rules here.** Always cross-reference `AGENTS.MD` for the strict package isolation rules (e.g., why `parqcast-core` cannot import `odoo`).

## 2. Gemini Context Retrieval Instructions
When asked to write code, debug, or answer architectural questions, Gemini should pull the following files into its context window:
* **Schema Inquiries:** If the user asks about available data, columns, or ML decisions, immediately reference `docs/DATA_DICTIONARY.md` and `packages/parqcast-core/src/parqcast/schemas/outbound.py`.
* **Action/Ingester Logic:** If writing code that pushes decisions back to Odoo, reference `packages/parqcast-core/src/parqcast/schemas/inbound.py`.

## 3. Gemini Coding Style & Toolchain
* **Package Manager:** We strictly use `uv`. When suggesting terminal commands to the user, always format them as `uv run <command>` (e.g., `uv run ruff check .`, `uv run pytest`). Do not suggest `pip install`.
* **Strict Pyright:** Gemini must write Python code that satisfies `pyright` strict mode. 
  * Avoid `Any` and implicit `Unknown` types.
  * Utilize PEP 695 generics (`type V18`, `type V19`) exactly as shown in the project stubs to enforce Odoo major version safety at compile time.
* **Odoo ORM Restriction:** When generating code, remember that only `parqcast-ingesters` is permitted to invoke the Odoo `env` object dynamically. `parqcast-collectors` must always use raw PostgreSQL queries via `psycopg2`.
