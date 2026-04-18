# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging
import traceback

from odoo import api, models

_logger = logging.getLogger(__name__)


class ParqcastCron(models.AbstractModel):
    _name = "parqcast.cron"
    _description = "Parqcast Export Runner"

    @api.model
    def _create_transport(self):
        """Create the configured transport instance."""
        ICP = self.env["ir.config_parameter"].sudo()
        transport_type = ICP.get_param("parqcast.transport_type", "local")

        if transport_type == "local":
            from pathlib import Path

            from parqcast.transport.local_fs import LocalFSTransport

            path = ICP.get_param("parqcast.local_path", "/tmp/parqcast_export")
            return LocalFSTransport(Path(path))

        if transport_type == "http":
            from parqcast.transport_http import HttpTransport

            return HttpTransport(
                server_url=ICP.get_param("parqcast.server_url", ""),
                api_key=ICP.get_param("parqcast.api_key", ""),
                namespace=ICP.get_param("parqcast.namespace", "parqcast"),
            )

        if transport_type == "s3":
            from parqcast.transport_s3 import S3Transport

            return S3Transport(
                bucket=ICP.get_param("parqcast.s3_bucket", ""),
                prefix=ICP.get_param("parqcast.s3_prefix", "parqcast"),
                endpoint_url=ICP.get_param("parqcast.s3_endpoint_url") or None,
                aws_access_key_id=ICP.get_param("parqcast.s3_access_key_id") or None,
                aws_secret_access_key=ICP.get_param("parqcast.s3_secret_access_key") or None,
                region_name=ICP.get_param("parqcast.s3_region") or None,
            )

        if transport_type == "attachment":
            from .transport_attachment import AttachmentTransport

            return AttachmentTransport(self.env)

        raise ValueError(f"Unknown transport type: {transport_type}")

    @api.model
    def _get_company(self):
        """Get the configured export company, falling back to current company."""
        ICP = self.env["ir.config_parameter"].sudo()
        company_id = int(ICP.get_param("parqcast.company_id", "0"))
        if company_id:
            company = self.env["res.company"].browse(company_id).exists()
            if company:
                return company
        return self.env.company

    @api.model
    def run_export(self):
        """Called by ir.cron to run one tick of the export pipeline."""
        try:
            from parqcast.core.version_gate import assert_supported
            from parqcast.orchestrator import Orchestrator

            from .env_adapter import OdooAdapter

            assert_supported(self.env.cr)

            ICP = self.env["ir.config_parameter"].sudo()
            time_budget = int(ICP.get_param("parqcast.time_budget", "270"))
            company = self._get_company()

            adapter = OdooAdapter(self.env)
            transport = self._create_transport()
            orch = Orchestrator(
                env=adapter,
                transport=transport,
                company=company.name,
                company_id=company.id,
                time_budget=time_budget,
            )

            result = orch.run()
            _logger.info("Parqcast export tick: %s", result.get("state", "done"))
            return result

        except Exception:
            _logger.error("Parqcast export failed:\n%s", traceback.format_exc())
            raise
