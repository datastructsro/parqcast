# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from typing import Any

from odoo import api, fields, models
from odoo.exceptions import ValidationError  # pyright: ignore[reportMissingImports]


def _transport_selection(self: Any = None) -> list[tuple[str, str]]:
    """Build transport choices dynamically — S3 only appears when installed."""
    from ..utils.transport_registry import has_s3_transport

    choices: list[tuple[str, str]] = [
        ("attachment", "Odoo Attachments"),
        ("local", "Local Filesystem"),
        ("http", "HTTP Server"),
    ]
    if has_s3_transport():
        choices.append(("s3", "AWS S3"))
    return choices


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    parqcast_transport_type = fields.Selection(
        selection=_transport_selection,
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
        config_parameter="parqcast.company_id",
    )
    parqcast_cron_active = fields.Boolean(
        string="Enable Scheduled Export",
    )
    parqcast_export_interval_hours = fields.Float(
        string="Export Interval (Hours)",
        default=24.0,
        config_parameter="parqcast.export_interval_hours",
        help="How many hours to wait after an export before starting a new one.",
    )

    # Status Block
    parqcast_odoo_version = fields.Char(string="Detected Odoo Version", compute="_compute_parqcast_status")
    parqcast_last_run_state = fields.Char(string="Last Run State", compute="_compute_parqcast_status")
    parqcast_last_run_error = fields.Text(string="Last Run Error", compute="_compute_parqcast_status")

    def _compute_parqcast_status(self):
        for rec in self:
            from parqcast.core.version_gate import _read_odoo_major  # pyright: ignore[reportPrivateUsage]

            rec.parqcast_odoo_version = _read_odoo_major(self.env.cr) or "Unknown"  # pyright: ignore[reportPrivateUsage]

            last_run = self.env["parqcast.run"].search([], limit=1, order="id desc")
            if last_run:
                state_dict = dict(last_run._fields["state"].selection)
                rec.parqcast_last_run_state = state_dict.get(last_run.state, last_run.state)
                rec.parqcast_last_run_error = last_run.error_message
            else:
                rec.parqcast_last_run_state = "No runs yet"
                rec.parqcast_last_run_error = False

    @api.constrains("parqcast_time_budget")
    def _check_time_budget(self):
        for rec in self:
            if rec.parqcast_time_budget < 30:
                raise ValidationError(self.env._("Time budget must be at least 30 seconds to allow progress."))  # pyright: ignore[reportAttributeAccessIssue]

    def _display_notification(self, title: str, message: str, msg_type: str = "success") -> dict[str, Any]:
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": msg_type,
                "sticky": False,
            },
        }

    def set_values(self) -> Any:
        res = super().set_values()
        cron = self.env.ref("parqcast.ir_cron_parqcast_export", raise_if_not_found=False)
        if cron:
            cron_sudo = cron.sudo()
            cron_sudo.active = self.parqcast_cron_active
            # Force the cron to tick every 5 minutes to advance the state machine
            cron_sudo.interval_number = 5
            cron_sudo.interval_type = "minutes"
        return res

    @api.model
    def get_values(self) -> dict[str, Any]:
        res = super().get_values()
        cron = self.env.ref("parqcast.ir_cron_parqcast_export", raise_if_not_found=False)
        res["parqcast_cron_active"] = cron.active if cron else False
        return res

    def action_run_export_now(self):
        """Manually trigger one export tick, bypassing the interval check."""
        result = self.env["parqcast.cron"].run_export(force_start=True)
        state = result.get("state", "done")
        chunks = result.get("files", [])

        msg = f"Export tick completed. State: {state}."
        if state == "error":
            msg = "Export tick failed with an error. Check Export Runs for details."
        elif chunks:
            msg = f"Export tick complete. {len(chunks)} files prepared/uploaded."

        return self._display_notification("Parqcast", msg, "danger" if state == "error" else "success")

    def action_test_connection(self):
        """Polymorphic connection test based on selected transport type."""
        from ..utils.transport_registry import transport_registry

        for rec in self:
            transport_type = rec.parqcast_transport_type
            if not transport_type:
                raise ValidationError(self.env._("Transport type is required."))  # pyright: ignore[reportAttributeAccessIssue]

            try:
                transport_registry.test_connection(transport_type, rec)
            except ValidationError:
                raise
            except Exception as e:
                raise ValidationError(self.env._("Connection failed: ") + str(e)) from e  # pyright: ignore[reportAttributeAccessIssue]

        return self._display_notification("Connection Test", "Connection is accessible and verified.")
