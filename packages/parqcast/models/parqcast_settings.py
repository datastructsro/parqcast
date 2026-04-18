# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from typing import Any

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    parqcast_transport_type = fields.Selection(
        [("attachment", "Odoo Attachments"), ("local", "Local Filesystem"), ("http", "HTTP Server"), ("s3", "AWS S3")],
        string="Transport",
        default="attachment",
        config_parameter="parqcast.transport_type",
    )
    # Local
    parqcast_local_path = fields.Char(
        string="Local Export Path",
        default="/tmp/parqcast_export",
        config_parameter="parqcast.local_path",
    )
    # HTTP
    parqcast_server_url = fields.Char(
        string="Server URL",
        config_parameter="parqcast.server_url",
    )
    parqcast_api_key = fields.Char(
        string="API Key",
        config_parameter="parqcast.api_key",
    )
    parqcast_namespace = fields.Char(
        string="Namespace",
        default="parqcast",
        config_parameter="parqcast.namespace",
    )
    # S3
    parqcast_s3_access_key_id = fields.Char(
        string="AWS Access Key ID",
        config_parameter="parqcast.s3_access_key_id",
    )
    parqcast_s3_secret_access_key = fields.Char(
        string="AWS Secret Access Key",
        config_parameter="parqcast.s3_secret_access_key",
    )
    parqcast_s3_region = fields.Char(
        string="AWS Region",
        config_parameter="parqcast.s3_region",
    )
    parqcast_s3_bucket = fields.Char(
        string="S3 Bucket",
        config_parameter="parqcast.s3_bucket",
    )
    parqcast_s3_prefix = fields.Char(
        string="S3 Prefix",
        default="parqcast",
        config_parameter="parqcast.s3_prefix",
    )
    parqcast_s3_endpoint_url = fields.Char(
        string="S3 Endpoint URL",
        help="For S3-compatible stores (MinIO, LocalStack). Leave empty for AWS.",
        config_parameter="parqcast.s3_endpoint_url",
    )
    # Maintenance
    parqcast_cleanup_days = fields.Integer(
        string="Cleanup After (days)",
        default=30,
        config_parameter="parqcast.cleanup_days",
    )
    # Common
    parqcast_time_budget = fields.Integer(
        string="Time Budget (seconds)",
        default=270,
        config_parameter="parqcast.time_budget",
    )
    parqcast_company_id = fields.Many2one(
        "res.company",
        string="Export Company",
    )
    parqcast_cron_active = fields.Boolean(
        string="Enable Scheduled Export",
    )
    parqcast_schedule_mode = fields.Selection(
        [("daily", "Once daily (midnight UTC)"), ("continuous", "Continuous (every 5 minutes)")],
        string="Schedule",
        default="daily",
        config_parameter="parqcast.schedule_mode",
    )

    def set_values(self) -> Any:
        res = super().set_values()
        self.env["ir.config_parameter"].sudo().set_param("parqcast.company_id", str(self.parqcast_company_id.id or 0))
        cron = self.env.ref("parqcast.ir_cron_parqcast_export", raise_if_not_found=False)
        if cron:
            cron_sudo = cron.sudo()
            cron_sudo.active = self.parqcast_cron_active
            if self.parqcast_schedule_mode == "continuous":
                cron_sudo.interval_number = 5
                cron_sudo.interval_type = "minutes"
            else:
                cron_sudo.interval_number = 1
                cron_sudo.interval_type = "days"
        return res

    @api.model
    def get_values(self) -> dict[str, Any]:
        res = super().get_values()
        cid = int(self.env["ir.config_parameter"].sudo().get_param("parqcast.company_id", "0"))
        res["parqcast_company_id"] = cid or False
        cron = self.env.ref("parqcast.ir_cron_parqcast_export", raise_if_not_found=False)
        res["parqcast_cron_active"] = cron.active if cron else False
        return res

    def action_run_export_now(self):
        """Manually trigger one export tick."""
        self.env["parqcast.cron"].run_export()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Parqcast",
                "message": "Export tick completed. Check Export Runs for results.",
                "type": "success",
                "sticky": False,
            },
        }
