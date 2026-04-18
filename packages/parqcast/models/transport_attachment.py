# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

"""Odoo Attachment transport — stores parquet files as ir.attachment records.

This is the default transport for single-instance deployments where both
parqcast and foreqcast run inside the same Odoo. No filesystem paths, no
external servers — exported parquet files live in Odoo's attachment store
and foreqcast reads them directly.
"""

import base64
import logging
from typing import Any, BinaryIO

from parqcast.transport.base import BaseTransport

_logger = logging.getLogger(__name__)


class AttachmentTransport(BaseTransport):
    """Store exported parquet files as ir.attachment on the export run record."""

    def __init__(self, env: Any) -> None:
        self._env: Any = env

    def _resolve_run_id(self, prefix: str) -> int:
        run_uuid = prefix.rsplit("/", 1)[-1]
        self._env.cr.execute(
            "SELECT id FROM parqcast_export_run WHERE run_uuid = %s",
            (run_uuid,),
        )
        row = self._env.cr.fetchone()
        return int(row[0]) if row else 0

    def upload_file(self, prefix: str, filename: str, data: BinaryIO) -> None:
        run_id = self._resolve_run_id(prefix)
        content = data.read()
        self._env["ir.attachment"].sudo().create({
            "name": filename,
            "datas": base64.b64encode(content).decode(),
            "res_model": "parqcast.run",
            "res_id": run_id,
            "mimetype": "application/octet-stream",
        })
        _logger.debug("Stored attachment %s for run %s (%d bytes)", filename, prefix, len(content))

    def download_file(self, prefix: str, filename: str) -> bytes:
        run_id = self._resolve_run_id(prefix)
        att = self._env["ir.attachment"].sudo().search([
            ("res_model", "=", "parqcast.run"),
            ("res_id", "=", run_id),
            ("name", "=", filename),
        ], limit=1)
        if not att:
            raise FileNotFoundError(f"Attachment not found: {filename} (run {prefix})")
        return base64.b64decode(att.datas)

    def list_files(self, prefix: str) -> list[str]:
        run_id = self._resolve_run_id(prefix)
        atts = self._env["ir.attachment"].sudo().search([
            ("res_model", "=", "parqcast.run"),
            ("res_id", "=", run_id),
        ])
        return [a.name for a in atts]
