# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging
import traceback

from odoo import api, models

from parqcast.transport.base import BaseTransport

_logger = logging.getLogger(__name__)


class ParqcastCron(models.AbstractModel):
    _name = "parqcast.cron"
    _description = "Parqcast Export Runner"

    @api.model
    def _create_transport(self) -> BaseTransport:
        """Create the configured transport instance."""
        from ..utils.transport_registry import transport_registry

        ICP = self.env["ir.config_parameter"].sudo()
        transport_type = ICP.get_param("parqcast.transport_type", "local")

        return transport_registry.build_for_cron(transport_type, self.env)

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

            # Phase separation ensures cleanup only happens in its own transaction
            # after the orchestrator successfully returns without throwing.
            self.env["parqcast.run"].action_cleanup_old()

            _logger.info("Parqcast export tick: %s", result.get("state", "done"))
            return result

        except Exception:
            _logger.error("Parqcast export failed:\n%s", traceback.format_exc())
            raise
