# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "Parqcast",
    "version": "19.0.1.2.0",
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
