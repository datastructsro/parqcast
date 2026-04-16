This module connects Odoo to cloud-based planning engines via a zero-computation
data pipe. It exports operational data (sales orders, products, inventory,
manufacturing orders, etc.) as Parquet files and uploads them through a pluggable
transport layer (local filesystem, HTTP, or AWS S3).

The export runs as a scheduled action with a configurable time budget, so it
never blocks the Odoo cron worker. A state-machine orchestrator can pause and
resume across multiple cron ticks, making it safe for large databases.
