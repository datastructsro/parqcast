# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
# pyright: reportUnusedExpression=none
# Odoo manifests are bare dict literals at module top level.
{
    "name": "Parqcast",
    # Major-agnostic version (`x.y.z`). Odoo prepends its own major at
    # discovery time, so this same manifest installs cleanly on every
    # major listed in `parqcast_supported_versions`. A pinned `19.0.x.y`
    # would be rejected by the v18 loader (which validates against
    # `18.0.x.y` or bare `x.y[.z]`).
    "version": "18.0.3.1.2",
    "category": "Supply Chain",
    "summary": "Zero-computation data pipe to cloud planning engines",
    "author": "DataStruct s.r.o., Odoo Community Association (OCA)",
    "website": "https://datastruct.tech",
    "support": "info@datastruct.tech",
    "development_status": "Beta",
    "maintainers": ["opopov-ai"],
    "license": "LGPL-3",
    "application": True,
    "depends": ["base"],
    # Parqcast certifies per Odoo major. Installs refuse on any
    # unlisted major via parqcast.core.version_gate.
    "parqcast_supported_versions": ("18", "19"),
    "external_dependencies": {
        "python": ["pyarrow"],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/defaults.xml",
        "data/ir_cron_data.xml",
        "views/parqcast_settings_views.xml",
        "views/parqcast_run_views.xml",
    ],
}
