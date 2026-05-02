# Settings Improvements

Date: 2026-04-27

Scope reviewed:

- Settings model and config parameters
- Settings form UI
- Cron defaults
- Retention and attachment behavior

## Recommended Changes

### 1. Make retention settings match runtime behavior

Current issue:

- The settings UI exposes `parqcast_cleanup_days` as a days-based retention policy.
- The automatic runtime path instead deletes all but the last 3 successful runs.

Relevant files:

- [packages/parqcast/models/parqcast_settings.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/models/parqcast_settings.py:66)
- [packages/parqcast/models/parqcast_run.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/models/parqcast_run.py:76)
- [packages/parqcast-core/src/parqcast/core/tracking.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-core/src/parqcast/core/tracking.py:126)
- [packages/parqcast-collectors/src/parqcast/orchestrator/__init__.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast-collectors/src/parqcast/orchestrator/__init__.py:376)

Suggestion:

- Pick one retention model and enforce it consistently.
- If the intended policy is days-based, wire `parqcast_cleanup_days` into the orchestrator cleanup path.
- If the intended policy is count-based, change the settings label and help text accordingly.

### 2. Make attachment cleanup explicit

Current issue:

- Attachment transport stores exports as `ir.attachment` rows linked to `parqcast.run`.
- SQL cleanup of old runs does not automatically clean up those attachments.

Relevant file:

- [packages/parqcast/models/transport_attachment.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/models/transport_attachment.py:36)

Suggestion:

- When deleting old runs, also delete their attachments through an Odoo-aware cleanup path.
- Add an optional “purge uploaded attachments after N days” policy if attachment transport remains the default.
- Show a short storage warning in the settings UI when `attachment` transport is selected.

### 3. Fix the schedule wording

Current issue:

- The UI says `Once daily (midnight UTC)`.
- The implementation only switches the cron interval to `1 day`; it does not actually normalize `nextcall` to midnight UTC.

Relevant files:

- [packages/parqcast/models/parqcast_settings.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/models/parqcast_settings.py:84)
- [packages/parqcast/data/ir_cron_data.xml](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/data/ir_cron_data.xml:4)

Suggestion:

- Either actually schedule the cron at midnight UTC, or rename the option to something accurate like `Every day`.
- If operators care about exact timing, expose a run time and timezone instead of hardcoding wording.

### 4. Add a status block to settings

Current issue:

- The settings page is mostly input-only.
- Operators cannot quickly see whether Parqcast is healthy without leaving the page.

Relevant file:

- [packages/parqcast/views/parqcast_settings_views.xml](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/views/parqcast_settings_views.xml:8)

Suggestion:

- Add a read-only status section showing detected Odoo major, version-gate status, selected company, transport type, next cron run, last run state, and last run error when present.

This would make misconfiguration much easier to diagnose.

### 5. Add transport validation actions

Current issue:

- The form hides and shows transport-specific fields, but it does not validate the configured destination proactively.

Relevant files:

- [packages/parqcast/views/parqcast_settings_views.xml](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/views/parqcast_settings_views.xml:51)
- [packages/parqcast/models/parqcast_cron.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/models/parqcast_cron.py:16)

Suggestion:

- Add `Test connection` / `Test write` actions for local filesystem, HTTP server, S3, and attachment transport.

- Validate required fields server-side before saving or before running the first export.
- Return actionable errors rather than waiting for cron to fail.

### 6. Improve manual run feedback

Current issue:

- `Run Export Now` always returns a generic success notification.
- It does not reflect whether the tick planned, collected, uploaded, paused, or failed.

Relevant file:

- [packages/parqcast/models/parqcast_settings.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/models/parqcast_settings.py:115)

Suggestion:

- Include the returned state in the notification.
- Include the run UUID when available.
- Surface immediate errors in the notification if the tick fails.

### 7. Add guardrails around time budget

Current issue:

- `parqcast_time_budget` is free-form.
- Very low values can make the system appear broken because planning or upload may never make visible progress.

Relevant files:

- [packages/parqcast/models/parqcast_settings.py](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/models/parqcast_settings.py:72)
- [packages/parqcast/views/parqcast_settings_views.xml](/Users/thatoleg/datastructsro/parqcast/packages/parqcast/views/parqcast_settings_views.xml:32)

Suggestion:

- Add sane minimum and recommended values in help text or validation.
- Consider presets such as `safe`, `balanced`, and `aggressive` if operators are not expected to tune raw seconds.

## Suggested Priority

Implement first:

- retention consistency
- attachment cleanup
- schedule wording fix

Implement second:

- status block
- transport validation
- better manual-run feedback

Implement later:

- time-budget guardrails
