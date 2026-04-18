"""
Export run tracking tables.

Standalone SQL-based implementation. Tracks export progress so that
interrupted cron jobs can resume from the last committed chunk.

Converts cleanly to Odoo ORM models (parqcast.export.run / parqcast.export.chunk)
when packaged as an Odoo module.
"""

from __future__ import annotations

import json
import uuid as _uuid
from datetime import UTC, datetime
from hashlib import sha256

from parqcast.core.protocols import ChunkMetadata, JsonDict


class ExportRun:
    """Tracks an export run via the parqcast_export_run table."""

    STATES = ("pending", "collecting", "uploading", "done", "error")

    def __init__(self, id: int, run_uuid: str, state: str, company_id: int | None = None):
        self.id = id
        self.run_uuid = run_uuid
        self.state = state
        self.company_id = company_id

    @classmethod
    def ensure_table(cls, cr):
        cr.execute("""
            CREATE TABLE IF NOT EXISTS parqcast_export_run (
                id SERIAL PRIMARY KEY,
                run_uuid VARCHAR(36) NOT NULL,
                state VARCHAR(20) NOT NULL DEFAULT 'pending',
                company_id INTEGER,
                company_name VARCHAR(256),
                odoo_version VARCHAR(64),
                export_mode VARCHAR(64),
                capabilities_json TEXT,
                collector_count INTEGER DEFAULT 0,
                manifest_json TEXT,
                error_message TEXT,
                started_at TIMESTAMP WITH TIME ZONE,
                finished_at TIMESTAMP WITH TIME ZONE,
                duration_seconds FLOAT
            )
        """)

    @classmethod
    def create(cls, cr, company_id: int | None = None, company_name: str = "", **kwargs) -> ExportRun:
        run_uuid = str(_uuid.uuid4())
        cr.execute(
            """
            INSERT INTO parqcast_export_run (run_uuid, state, company_id, company_name, started_at)
            VALUES (%s, 'pending', %s, %s, %s)
            RETURNING id
            """,
            (run_uuid, company_id, company_name, datetime.now(UTC)),
        )
        run_id = cr.fetchone()[0]
        return cls(id=run_id, run_uuid=run_uuid, state="pending", company_id=company_id)

    @classmethod
    def find_active(cls, cr) -> ExportRun | None:
        cr.execute("""
            SELECT id, run_uuid, state, company_id
            FROM parqcast_export_run
            WHERE state NOT IN ('done', 'error')
            ORDER BY id DESC LIMIT 1
        """)
        row = cr.fetchone()
        if row:
            return cls(id=row[0], run_uuid=row[1], state=row[2], company_id=row[3])
        return None

    def set_state(self, cr, state: str):
        self.state = state
        cr.execute("UPDATE parqcast_export_run SET state = %s WHERE id = %s", (state, self.id))

    def set_capabilities(self, cr, caps_summary: JsonDict, collector_count: int):
        cr.execute(
            """
            UPDATE parqcast_export_run
            SET capabilities_json = %s, odoo_version = %s, export_mode = %s, collector_count = %s
            WHERE id = %s
            """,
            (
                json.dumps(caps_summary, default=str),
                caps_summary.get("odoo_version", ""),
                caps_summary.get("mode", ""),
                collector_count,
                self.id,
            ),
        )

    def set_manifest(self, cr, manifest: JsonDict):
        cr.execute(
            """
            UPDATE parqcast_export_run
            SET manifest_json = %s, finished_at = %s, duration_seconds = %s
            WHERE id = %s
            """,
            (
                json.dumps(manifest, default=str),
                datetime.now(UTC),
                manifest.get("total_duration_seconds", 0),
                self.id,
            ),
        )

    def set_error(self, cr, message: str):
        self.state = "error"
        cr.execute(
            "UPDATE parqcast_export_run SET state = 'error', error_message = %s WHERE id = %s",
            (message, self.id),
        )

    @classmethod
    def cleanup_old(cls, cr, keep_last: int = 3):
        """Delete completed runs older than the most recent `keep_last`."""
        cr.execute(
            """
            DELETE FROM parqcast_export_run
            WHERE state = 'done'
              AND id NOT IN (
                  SELECT id FROM parqcast_export_run
                  WHERE state = 'done'
                  ORDER BY id DESC LIMIT %s
              )
            """,
            (keep_last,),
        )


class ExportChunk:
    """Tracks a single chunk of a collector's parquet output."""

    STATES = ("pending", "created", "uploaded", "error")

    def __init__(
        self,
        id: int,
        run_id: int,
        collector: str,
        sequence: int,
        state: str = "pending",
        key_from: int = 0,
        key_to: int = 0,
        estimated_seconds: float = 0,
    ):
        self.id = id
        self.run_id = run_id
        self.collector = collector
        self.sequence = sequence
        self.state = state
        self.key_from = key_from
        self.key_to = key_to
        self.estimated_seconds = estimated_seconds

    @classmethod
    def ensure_table(cls, cr):
        cr.execute("""
            CREATE TABLE IF NOT EXISTS parqcast_export_chunk (
                id SERIAL PRIMARY KEY,
                run_id INTEGER NOT NULL REFERENCES parqcast_export_run(id) ON DELETE CASCADE,
                collector VARCHAR(64) NOT NULL,
                sequence INTEGER NOT NULL DEFAULT 0,
                state VARCHAR(20) NOT NULL DEFAULT 'pending',
                key_from BIGINT NOT NULL DEFAULT 0,
                key_to BIGINT NOT NULL DEFAULT 0,
                estimated_seconds FLOAT NOT NULL DEFAULT 0,
                data BYTEA,
                row_count INTEGER DEFAULT 0,
                byte_count INTEGER DEFAULT 0,
                checksum VARCHAR(80),
                duration_seconds FLOAT DEFAULT 0,
                error_message TEXT
            )
        """)

    @classmethod
    def create(
        cls,
        cr,
        run_id: int,
        collector: str,
        sequence: int,
        key_from: int = 0,
        key_to: int = 0,
        estimated_seconds: float = 0,
    ) -> ExportChunk:
        cr.execute(
            """
            INSERT INTO parqcast_export_chunk
                (run_id, collector, sequence, state, key_from, key_to, estimated_seconds)
            VALUES (%s, %s, %s, 'pending', %s, %s, %s)
            RETURNING id
            """,
            (run_id, collector, sequence, key_from, key_to, estimated_seconds),
        )
        chunk_id = cr.fetchone()[0]
        return cls(
            id=chunk_id,
            run_id=run_id,
            collector=collector,
            sequence=sequence,
            key_from=key_from,
            key_to=key_to,
            estimated_seconds=estimated_seconds,
        )

    @classmethod
    def find_by_state(cls, cr, run_id: int, state: str) -> list[ExportChunk]:
        cr.execute(
            """
            SELECT id, run_id, collector, sequence, state, key_from, key_to, estimated_seconds
            FROM parqcast_export_chunk
            WHERE run_id = %s AND state = %s
            ORDER BY sequence
            """,
            (run_id, state),
        )
        return [
            cls(
                id=r[0],
                run_id=r[1],
                collector=r[2],
                sequence=r[3],
                state=r[4],
                key_from=r[5],
                key_to=r[6],
                estimated_seconds=r[7],
            )
            for r in cr.fetchall()
        ]

    @classmethod
    def count_by_state(cls, cr, run_id: int, state: str) -> int:
        cr.execute(
            "SELECT COUNT(*) FROM parqcast_export_chunk WHERE run_id = %s AND state = %s",
            (run_id, state),
        )
        return cr.fetchone()[0]

    def store_blob(self, cr, data: bytes, row_count: int, duration: float):
        checksum = f"sha256:{sha256(data).hexdigest()}"
        self.state = "created"
        cr.execute(
            """
            UPDATE parqcast_export_chunk
            SET state = 'created', data = %s, row_count = %s, byte_count = %s,
                checksum = %s, duration_seconds = %s
            WHERE id = %s
            """,
            (data, row_count, len(data), checksum, duration, self.id),
        )

    def get_blob(self, cr) -> bytes:
        cr.execute("SELECT data FROM parqcast_export_chunk WHERE id = %s", (self.id,))
        row = cr.fetchone()
        if row and row[0]:
            data = row[0]
            return bytes(data) if isinstance(data, memoryview) else data
        return b""

    def set_uploaded(self, cr):
        self.state = "uploaded"
        cr.execute(
            "UPDATE parqcast_export_chunk SET state = 'uploaded', data = NULL WHERE id = %s",
            (self.id,),
        )

    def set_error(self, cr, message: str):
        self.state = "error"
        cr.execute(
            "UPDATE parqcast_export_chunk SET state = 'error', error_message = %s WHERE id = %s",
            (message, self.id),
        )

    def get_metadata(self, cr) -> ChunkMetadata:
        cr.execute(
            """
            SELECT collector, row_count, byte_count, checksum, duration_seconds, key_from
            FROM parqcast_export_chunk WHERE id = %s
            """,
            (self.id,),
        )
        r = cr.fetchone()
        suffix = f"_{r[5]}" if r[5] > 0 else ""
        return {
            "file": f"{r[0]}{suffix}.parquet",
            "rows": r[1],
            "bytes": r[2],
            "checksum": r[3],
            "duration_seconds": r[4],
            "collector": r[0],
        }


def estimate_row_count(cr, table_name: str) -> int:
    """Fast approximate row count using pg_class statistics."""
    cr.execute("SELECT reltuples::bigint FROM pg_class WHERE relname = %s", (table_name,))
    row = cr.fetchone()
    if row and row[0] and row[0] > 0:
        return row[0]
    return 0


def get_id_range(cr, table_name: str) -> tuple[int, int]:
    """Get MIN(id) and MAX(id) for a table. Returns (0, 0) if empty."""
    cr.execute(f"SELECT COALESCE(MIN(id), 0), COALESCE(MAX(id), 0) FROM {table_name}")
    row = cr.fetchone()
    return (row[0], row[1]) if row else (0, 0)


# Default throughput rates for time estimation (rows/second)
DEFAULT_STREAMING_RATE = 25_000  # conservative, based on SO-line benchmark
DEFAULT_INMEMORY_RATE = 100_000
