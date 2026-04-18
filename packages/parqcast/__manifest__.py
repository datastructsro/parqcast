# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
# pyright: reportUnusedExpression=none
# Odoo manifests are bare dict literals at module top level.
{
    "name": "Parqcast",
    "version": "19.0.3.0.0",
    "category": "Supply Chain",
    "summary": "Zero-computation data pipe to cloud planning engines",
    "author": "DataStruct s.r.o.",
    "website": "https://datastruct.tech",
    "support": "info@datastruct.tech",
    "development_status": "Beta",
    "maintainers": ["opopov-ai"],
    "license": "LGPL-3",
    "installable": True,
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
