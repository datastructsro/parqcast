# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import base64
import io
import logging
import zipfile
from datetime import timedelta

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ParqcastRun(models.Model):
    _name = "parqcast.run"
    _description = "Parqcast Export Run"
    _table = "parqcast_export_run"
    _order = "id desc"
    _auto = False

    run_uuid = fields.Char("Run UUID", readonly=True)
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("collecting", "Collecting"),
            ("uploading", "Uploading"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        readonly=True,
    )
    company_id = fields.Integer("Company ID", readonly=True)
    company_name = fields.Char("Company", readonly=True)
    odoo_version = fields.Char(readonly=True)
    export_mode = fields.Char(readonly=True)
    collector_count = fields.Integer("Collectors", readonly=True)
    manifest_json = fields.Text("Manifest", readonly=True)
    error_message = fields.Text("Error", readonly=True)
    started_at = fields.Datetime("Started", readonly=True)
    finished_at = fields.Datetime("Finished", readonly=True)
    duration_seconds = fields.Float("Duration (s)", readonly=True)
    chunk_ids = fields.One2many("parqcast.chunk", "run_id", "Chunks", readonly=True)
    attachment_count = fields.Integer("Attachments", compute="_compute_attachment_count")

    def init(self):
        """Ensure tracking tables exist before ORM accesses them."""
        from parqcast.core.tracking import ExportChunk, ExportRun

        ExportRun.ensure_table(self.env.cr)
        ExportChunk.ensure_table(self.env.cr)

    def action_cancel(self):
        """Cancel a stuck run — delete pending/created chunks, mark as error."""
        for run in self:
            if run.state in ("pending", "collecting", "uploading"):
                self.env.cr.execute(
                    "DELETE FROM parqcast_export_chunk WHERE run_id = %s AND state IN ('pending', 'created')",
                    (run.id,),
                )
                self.env.cr.execute(
                    "UPDATE parqcast_export_run SET state = 'error', error_message = 'Cancelled by user' WHERE id = %s",
                    (run.id,),
                )
                _logger.info("Cancelled parqcast run %s", run.run_uuid)

    def action_purge_blobs(self):
        """Clear blob data from uploaded chunks to free database space."""
        for run in self:
            self.env.cr.execute(
                "UPDATE parqcast_export_chunk SET data = NULL WHERE run_id = %s AND state = 'uploaded'",
                (run.id,),
            )
            _logger.info("Purged blob data for run %s", run.run_uuid)

    def action_cleanup_old(self):
        """Delete completed runs older than the configured retention period."""
        ICP = self.env["ir.config_parameter"].sudo()
        days = int(ICP.get_param("parqcast.cleanup_days", "30"))
        cutoff = fields.Datetime.now() - timedelta(days=days)
        self.env.cr.execute(
            "DELETE FROM parqcast_export_run WHERE state = 'done' AND finished_at < %s",
            (cutoff,),
        )
        _logger.info("Cleaned up parqcast runs older than %d days", days)

    def _compute_attachment_count(self):
        for run in self:
            run.attachment_count = self.env["ir.attachment"].sudo().search_count([
                ("res_model", "=", "parqcast.run"),
                ("res_id", "=", run.id),
            ])

    def action_download_zip(self):
        """Download all parquet attachments for this run as a ZIP file."""
        self.ensure_one()
        attachments = self.env["ir.attachment"].sudo().search([
            ("res_model", "=", "parqcast.run"),
            ("res_id", "=", self.id),
        ])
        if not attachments:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Parqcast",
                    "message": "No attachment files found for this export run.",
                    "type": "warning",
                    "sticky": False,
                },
            }

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for att in attachments:
                zf.writestr(att.name, base64.b64decode(att.datas))
        buf.seek(0)

        zip_att = self.env["ir.attachment"].sudo().create({
            "name": f"parqcast_export_{self.run_uuid[:8]}.zip",
            "datas": base64.b64encode(buf.read()).decode(),
            "mimetype": "application/zip",
        })
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{zip_att.id}?download=true",
            "target": "self",
        }
