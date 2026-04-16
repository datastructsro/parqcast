"""
State-machine orchestrator with strict phase separation.

Designed for Odoo.sh cron safety:
- Each cron tick executes exactly ONE phase — never crosses phase boundaries
- Each chunk operation commits independently — progress survives cron kills
- Next cron tick resumes from current state
- Rollback before error handling to keep transactions clean

State flow (one phase per tick):
  pending    → create chunk records                → collecting
  collecting → collect batch of chunks (time-budgeted) → collecting | collected
  collected  → transition only (no work)           → uploading
  uploading  → upload batch of chunks (time-budgeted)  → uploading | done
                                                    ↘ error
"""

import io
import json
import logging
import time

import pyarrow.parquet as pq

from parqcast.collectors.factory import CollectorFactory
from parqcast.core.tracking import (
    DEFAULT_STREAMING_RATE,
    ExportChunk,
    ExportRun,
    estimate_row_count,
    get_id_range,
)
from parqcast.transport.base import BaseTransport

logger = logging.getLogger(__name__)

# Default time budget: 4.5 minutes, leaving 30s buffer for cleanup
DEFAULT_TIME_BUDGET = 270


class Orchestrator:
    def __init__(
        self,
        env,
        transport: BaseTransport,
        company: str,
        company_id: int,
        time_budget: int = DEFAULT_TIME_BUDGET,
        run_cls: type | None = None,
        chunk_cls: type | None = None,
    ):
        self.env = env
        self.transport = transport
        self.company = company
        self.company_id = company_id
        self.time_budget = time_budget
        self.run_cls = run_cls or ExportRun
        self.chunk_cls = chunk_cls or ExportChunk

    def _commit(self):
        """Commit the current transaction via the Connection protocol."""
        if not self.env.conn.autocommit:
            self.env.conn.commit()

    def _rollback(self):
        """Rollback the current transaction — call before error handling."""
        self.env.conn.rollback()

    def _time_remaining(self, t0: float) -> float:
        return self.time_budget - (time.monotonic() - t0)

    def run(self) -> dict:
        """Execute one phase of the export pipeline. Call repeatedly from cron."""
        t0 = time.monotonic()
        cr = self.env.cr

        # Ensure tracking tables exist
        self.run_cls.ensure_table(cr)
        self.chunk_cls.ensure_table(cr)
        self._commit()

        # Find or create a run
        run = self.run_cls.find_active(cr)
        if run is None:
            run = self.run_cls.create(cr, company_id=self.company_id, company_name=self.company)
            self._commit()

        # Dispatch to the current phase — exactly one phase per tick
        if run.state == "pending":
            return self._phase_plan(cr, run, t0)

        if run.state == "collecting":
            return self._phase_collect(cr, run, t0)

        if run.state == "uploading":
            return self._phase_upload(cr, run, t0)

        return {"state": run.state, "run_uuid": run.run_uuid}

    # ------------------------------------------------------------------
    # Phase 1: Plan — probe database, create chunk records
    # ------------------------------------------------------------------

    def _phase_plan(self, cr, run, t0) -> dict:
        factory = CollectorFactory(self.env)
        caps = factory.probe()
        collectors = factory.create_collectors(caps)
        ordered = factory.resolve_order(collectors)

        seq = 0
        for collector in ordered:
            if collector.primary_table:
                est = estimate_row_count(cr, collector.primary_table)
                if est > collector.max_chunk_rows:
                    min_id, max_id = get_id_range(cr, collector.primary_table)
                    if max_id > min_id:
                        n_chunks = -(-est // collector.max_chunk_rows)
                        id_step = -(-(max_id - min_id + 1) // n_chunks)
                        cur_id = min_id
                        while cur_id <= max_id:
                            next_id = min(cur_id + id_step, max_id + 1)
                            est_secs = collector.max_chunk_rows / DEFAULT_STREAMING_RATE
                            self.chunk_cls.create(
                                cr,
                                run_id=run.id,
                                collector=collector.name,
                                sequence=seq,
                                key_from=cur_id,
                                key_to=next_id,
                                estimated_seconds=est_secs,
                            )
                            seq += 1
                            cur_id = next_id
                        logger.info(
                            "  %s: ~%d rows, id %d..%d → %d keyset chunks",
                            collector.name,
                            est,
                            min_id,
                            max_id,
                            -(-est // collector.max_chunk_rows),
                        )
                        continue

            self.chunk_cls.create(cr, run_id=run.id, collector=collector.name, sequence=seq)
            seq += 1

        run.set_capabilities(cr, caps.summary(), seq)
        run.set_state(cr, "collecting")
        self._commit()

        logger.info("Run %s: planned %d chunks (mode=%s)", run.run_uuid[:8], seq, caps.mode)
        return {"state": "collecting", "run_uuid": run.run_uuid, "pending": seq}

    # ------------------------------------------------------------------
    # Phase 2: Collect — execute SQL, store parquet blobs in tracking DB
    # ------------------------------------------------------------------

    def _phase_collect(self, cr, run, t0) -> dict:
        factory = CollectorFactory(self.env)
        caps = factory.probe()
        collectors = factory.create_collectors(caps)
        collectors_by_name = {c.name: c for c in collectors}

        pending = self.chunk_cls.find_by_state(cr, run.id, "pending")
        logger.info("Run %s: %d pending chunks to collect", run.run_uuid[:8], len(pending))

        for chunk_rec in pending:
            remaining = self._time_remaining(t0)
            est = chunk_rec.estimated_seconds
            needed = est * 1.3 if est > 5 else 15
            if remaining < needed:
                logger.info(
                    "  Pausing: %s needs ~%.0fs, only %.0fs remaining",
                    chunk_rec.collector,
                    needed,
                    remaining,
                )
                still = self.chunk_cls.count_by_state(cr, run.id, "pending")
                return {"state": "collecting", "run_uuid": run.run_uuid, "pending": still}

            collector = collectors_by_name.get(chunk_rec.collector)
            if not collector:
                chunk_rec.set_error(cr, f"Collector '{chunk_rec.collector}' not found")
                self._commit()
                continue

            try:
                tc = time.monotonic()
                table = collector.collect(
                    key_from=chunk_rec.key_from,
                    key_to=chunk_rec.key_to,
                )
                buf = io.BytesIO()
                pq.write_table(table, buf, compression="snappy")
                data = buf.getvalue()
                rows = table.num_rows

                duration = round(time.monotonic() - tc, 3)
                chunk_rec.store_blob(cr, data, rows, duration)
                self._commit()

                key_info = f" id={chunk_rec.key_from}..{chunk_rec.key_to}" if chunk_rec.key_from > 0 else ""
                logger.info(
                    "  %s: %d rows, %.1f KB in %.3fs%s",
                    collector.name,
                    rows,
                    len(data) / 1024,
                    duration,
                    key_info,
                )
            except Exception as e:
                self._rollback()
                chunk_rec.set_error(cr, str(e))
                self._commit()
                logger.error("  %s: FAILED - %s", collector.name, e)

        # All pending chunks processed — transition to uploading
        # But DON'T start uploading in this tick
        still_pending = self.chunk_cls.count_by_state(cr, run.id, "pending")
        if still_pending == 0:
            run.set_state(cr, "uploading")
            self._commit()
            logger.info("Run %s: all chunks collected, ready to upload", run.run_uuid[:8])
            return {"state": "uploading", "run_uuid": run.run_uuid}

        return {"state": "collecting", "run_uuid": run.run_uuid, "pending": still_pending}

    # ------------------------------------------------------------------
    # Phase 3: Upload — stream blobs from tracking DB to transport
    # ------------------------------------------------------------------

    def _phase_upload(self, cr, run, t0) -> dict:
        created = self.chunk_cls.find_by_state(cr, run.id, "created")
        logger.info("Run %s: %d chunks to upload", run.run_uuid[:8], len(created))

        prefix = f"outbound/{run.run_uuid}"

        for chunk_rec in created:
            remaining = self._time_remaining(t0)
            if remaining < 15:
                logger.info("  Time budget exhausted during upload, pausing")
                return {"state": "uploading", "run_uuid": run.run_uuid}

            try:
                data = chunk_rec.get_blob(cr)
                meta = chunk_rec.get_metadata(cr)
                self.transport.upload_file(prefix, meta["file"], io.BytesIO(data))
                chunk_rec.set_uploaded(cr)
                self._commit()
                logger.info("  uploaded %s (%d rows)", meta["file"], meta["rows"])
            except Exception as e:
                self._rollback()
                chunk_rec.set_error(cr, str(e))
                self._commit()
                logger.error("  upload FAILED %s: %s", chunk_rec.collector, e)

        # Check if all uploads complete
        still_created = self.chunk_cls.count_by_state(cr, run.id, "created")
        if still_created > 0:
            return {"state": "uploading", "run_uuid": run.run_uuid, "remaining": still_created}

        # All uploaded — build and upload manifest, finalize
        return self._finalize(cr, run, prefix, t0)

    # ------------------------------------------------------------------
    # Finalize — build manifest, mark done
    # ------------------------------------------------------------------

    def _finalize(self, cr, run, prefix, t0) -> dict:
        from parqcast.core.manifest import build_manifest

        # Gather metadata from all uploaded chunks
        uploaded = self.chunk_cls.find_by_state(cr, run.id, "uploaded")
        file_metas = [chunk_rec.get_metadata(cr) for chunk_rec in uploaded]

        errors = [f"{c.collector}: {c.state}" for c in self.chunk_cls.find_by_state(cr, run.id, "error")]

        # Re-probe for capabilities (needed for manifest)
        factory = CollectorFactory(self.env)
        caps = factory.probe()

        manifest = build_manifest(
            files=file_metas,
            company=self.company,
            company_id=self.company_id,
            total_duration=round(time.monotonic() - t0, 3),
            errors=errors,
            warnings=[],
        )
        manifest["capabilities"] = caps.summary()
        manifest["run_uuid"] = run.run_uuid

        manifest_bytes = json.dumps(manifest, default=str).encode()
        self.transport.upload_file(prefix, "manifest.json", io.BytesIO(manifest_bytes))

        run.set_manifest(cr, manifest)
        run.set_state(cr, "done")
        self._commit()

        self.run_cls.cleanup_old(cr)
        self._commit()

        logger.info(
            "Run %s complete: %d files, %d errors",
            run.run_uuid[:8],
            len(file_metas),
            len(errors),
        )

        return manifest
