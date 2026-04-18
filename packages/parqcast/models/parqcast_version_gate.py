# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

"""Eager version gate: refuses to load the addon on unsupported Odoo majors.

``_register_hook`` fires once per database when Odoo builds the registry for
the addon. Raising here aborts installation/upgrade with a clear error
before any parqcast code touches the ORM. The cron hook in parqcast_cron
calls the same check as defense in depth.
"""

from odoo import models


class ParqcastVersionGate(models.AbstractModel):
    _name = "parqcast.version.gate"
    _description = "Refuses to load parqcast on unsupported Odoo versions"

    def _register_hook(self):
        super()._register_hook()
        from parqcast.core.version_gate import assert_supported

        assert_supported(self.env.cr)
