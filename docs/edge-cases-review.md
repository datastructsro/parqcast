# Edge Cases Review

Date: 2026-04-27

Scope reviewed:

- Version gate and bundle registry
- Orchestrator finalization and retention paths
- Inbound receiver / ingester dispatch
- Live-DB test coverage for the new v18 path

Verification performed:

- `uv run pytest tests/test_version_gate.py tests/test_capabilities.py tests/test_schemas.py tests/test_manifest.py -q`
- Result: `46 passed`

Not performed:

- No live DB test run against `PARQCAST_TEST_DB`
- No Odoo addon install/upgrade test

## Findings

### 1. Receiver still hardcodes v19 ingesters, so v18 inbound writeback can dispatch through the wrong actor

Severity: high

The receiver loads ingesters from `ALL_INGESTERS`, and that map is still pinned to v19 classes only. The code comment explicitly says it is kept v19-keyed, and `Receiver.run()` does not resolve the active Odoo major before choosing an ingester class. [packages/parqcast-ingesters/src/parqcast/ingesters/__init__.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-ingesters/src/parqcast/ingesters/__init__.py:15) [packages/parqcast-ingesters/src/parqcast/receiver/__init__.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-ingesters/src/parqcast/receiver/__init__.py:55)

This is no longer safe after adding v18. The concrete proof point is purchase-order writeback: `PurchaseActorV18` writes `product_uom`, while `PurchaseActorV19` writes `product_uom_id`. If the receiver is pointed at an Odoo 18 database, the current dispatch path will still instantiate the v19 actor for `"PO"` decisions. [packages/parqcast-ingesters/src/parqcast/ingesters/v18/purchase_actor.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-ingesters/src/parqcast/ingesters/v18/purchase_actor.py:53) [packages/parqcast-ingesters/src/parqcast/ingesters/v19/purchase_actor.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-ingesters/src/parqcast/ingesters/v19/purchase_actor.py:53)

Recommended direction:

- Make the receiver version-aware by resolving the current major from `env.cr` and building its dispatch table from `REGISTRY[version].ingesters`.
- If cross-version manifests are expected to be replayed elsewhere, include the source Odoo major in the receiver contract and validate it before dispatch.

### 2. Automatic cleanup bypasses the configured retention policy and can orphan attachment payloads

Severity: high

The addon UI exposes `parqcast_cleanup_days`, and the model-level cleanup action deletes runs older than that cutoff. [packages/parqcast/models/parqcast_settings.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/models/parqcast_settings.py:66) [packages/parqcast/models/parqcast_run.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/models/parqcast_run.py:76)

But the actual automatic path in the orchestrator does something different: every successful run calls the core SQL helper `ExportRun.cleanup_old()` with its default `keep_last=3`, so retention is really "keep the last 3 done runs", not "delete after N days". [packages/parqcast-collectors/src/parqcast/orchestrator/__init__.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-collectors/src/parqcast/orchestrator/__init__.py:376) [packages/parqcast-core/src/parqcast/core/tracking.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-core/src/parqcast/core/tracking.py:126)

That would already be a policy mismatch, but it gets worse with the default attachment transport. Export files are stored as `ir.attachment` rows tied to `parqcast.run` via `res_model` / `res_id`. The SQL cleanup only deletes from `parqcast_export_run`; it does not touch attachments. That means successful exports can leave behind orphaned attachment rows and binary payloads once their run rows are deleted. [packages/parqcast/models/transport_attachment.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/models/transport_attachment.py:36)

Recommended direction:

- Pick one retention model and enforce it in one place.
- If attachment transport stays the default, cleanup must go through an Odoo-aware path that also deletes related attachments.

### 3. Manifest metadata falls back to `odoo_version="17.0"` instead of the actual exporting database version

Severity: medium

`build_manifest()` defaults the top-level `odoo_version` to `"17.0"`. The orchestrator's `_finalize()` call does not pass `caps.odoo_version`, even though it re-probes capabilities immediately before building the manifest. The exported manifest therefore carries the wrong top-level Odoo version metadata for both v18 and v19 runs. [packages/parqcast-core/src/parqcast/core/manifest.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-core/src/parqcast/core/manifest.py:14) [packages/parqcast-collectors/src/parqcast/orchestrator/__init__.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-collectors/src/parqcast/orchestrator/__init__.py:354)

There is a partial workaround because `manifest["capabilities"]` is filled afterwards, but any downstream reader using the manifest's top-level `odoo_version` field will see incorrect data.

Recommended direction:

- Pass the actual `caps.odoo_version` into `build_manifest()`.
- Remove the misleading default, or make it explicit that callers must provide it.

### 4. Finalized manifests lose the actual chunk failure reason

Severity: medium

Chunk errors are stored with a real `error_message` when collection or upload fails. [packages/parqcast-core/src/parqcast/core/tracking.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-core/src/parqcast/core/tracking.py:283)

During finalization, however, the manifest error list is built as `f"{c.collector}: {c.state}"`. Since `c.state` is always just `"error"` for failed chunks, operators lose the actual exception text in the exported manifest. [packages/parqcast-collectors/src/parqcast/orchestrator/__init__.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-collectors/src/parqcast/orchestrator/__init__.py:352)

Impact:

- Post-mortem debugging from `manifest.json` becomes much harder.
- Remote systems consuming manifests cannot distinguish schema failures, permission failures, transport failures, or data-quality failures.

Recommended direction:

- Include `error_message` in the finalized manifest.
- Consider separating collection errors from upload errors if downstream automation needs to react differently.

### 5. The live-DB test file is only partially version-parameterized

Severity: medium

Most of `tests/test_live_db.py` is bundle-aware: `_probe_and_build()` resolves `REGISTRY[TEST_ODOO_VERSION]` and calls that bundle's `probe_capabilities`. [tests/test_live_db.py](/Users/thatoleg/datastructsro/parqcast/tests/test_live_db.py:36)

But `test_probe_capabilities()` still imports and calls `probe_v19()` directly. So a run with `PARQCAST_TEST_ODOO_VERSION=18` does not fully exercise the v18-specific probe entrypoint even though the surrounding test module suggests it does. [tests/test_live_db.py](/Users/thatoleg/datastructsro/parqcast/tests/test_live_db.py:27) [tests/test_live_db.py](/Users/thatoleg/datastructsro/parqcast/tests/test_live_db.py:115)

This is a test gap rather than a runtime bug, but it matters because the branch's main risk surface is exactly the version split.

Recommended direction:

- Replace the direct `probe_v19()` call with `bundle.probe_capabilities(...)` or parametrize the test over both wrappers.

## Watch List

### Bundle bootstrap makes the install-time gate weaker than it looks

`assert_supported()` accepts a major if it exists in `REGISTRY`, and `REGISTRY` is pre-bootstrapped with empty v18/v19 bundles before the version-specific subpackages are imported. The addon `_register_hook()` therefore proves only that the major is listed, not that the corresponding bundle was imported successfully or is complete. [packages/parqcast-core/src/parqcast/core/registry.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-core/src/parqcast/core/registry.py:49) [packages/parqcast-core/src/parqcast/core/version_gate.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-core/src/parqcast/core/version_gate.py:41) [packages/parqcast/models/parqcast_version_gate.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/models/parqcast_version_gate.py:19)

That is acceptable during staged migrations, but it is a weak fit for a production install/upgrade guard. A broken import in a version bundle would still let installation proceed and only fail later when the cron path hits `_resolve_bundle()`.

### Keyset pagination assumes collectors do not already define their own `ORDER BY`

`BaseCollector.collect()` appends `ORDER BY {pk_column}` whenever keyset bounds are applied. That is fine for the current collector set, but it will break as soon as a future collector ships SQL with its own trailing `ORDER BY`. [packages/parqcast-collectors/src/parqcast/collectors/base.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-collectors/src/parqcast/collectors/base.py:101)

This is not a current regression, but it is a good invariance to encode in tests if more complex collectors get added.
