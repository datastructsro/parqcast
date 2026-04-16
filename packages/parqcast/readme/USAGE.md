## Configuration

1. Go to **Settings > Parqcast** (requires System Administrator access).
2. Choose a **Transport** type:
   - **Local Filesystem** -- export to a directory on the server.
   - **HTTP Server** -- push files to a remote HTTP endpoint.
   - **AWS S3** -- upload to an S3 bucket (or S3-compatible store).
3. Set the **Time Budget** (seconds per cron tick, default 270).
4. Optionally select a specific **Export Company**.

## Running the export

The module registers a scheduled action **Parqcast: Export Data** (disabled by
default). Enable it from **Settings > Technical > Automation > Scheduled Actions**
and set your preferred interval (e.g. every 5 minutes).

## Monitoring

Go to **Settings > Parqcast > Export Runs** to see past and in-progress exports.
Each run shows its state, duration, collector count, and individual chunk details.
Stuck runs can be cancelled and old runs can be purged from the same view.
