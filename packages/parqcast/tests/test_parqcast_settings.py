# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.tests import TransactionCase


class TestParqcastSettings(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ICP = cls.env["ir.config_parameter"].sudo()

    def test_default_transport_type(self):
        """Default transport is 'attachment' (set by data/defaults.xml)."""
        value = self.ICP.get_param("parqcast.transport_type")
        self.assertEqual(value, "attachment")

    def test_default_time_budget(self):
        """Default time budget should be 270 seconds."""
        value = int(self.ICP.get_param("parqcast.time_budget", "270"))
        self.assertEqual(value, 270)

    def test_settings_set_and_get_company(self):
        """Setting export company should round-trip through config parameters."""
        company = self.env.company
        settings = self.env["res.config.settings"].create({"parqcast_company_id": company.id})
        settings.set_values()
        stored = int(self.ICP.get_param("parqcast.company_id", "0"))
        self.assertEqual(stored, company.id)

    def test_settings_get_values_returns_company(self):
        """get_values should return the stored company id."""
        company = self.env.company
        self.ICP.set_param("parqcast.company_id", str(company.id))
        settings = self.env["res.config.settings"].create({})
        values = settings.get_values()
        self.assertEqual(values.get("parqcast_company_id"), company.id)

    def test_run_model_fields(self):
        """parqcast.run model should be accessible and have expected fields."""
        Run = self.env["parqcast.run"]
        self.assertIn("run_uuid", Run._fields)
        self.assertIn("state", Run._fields)
        self.assertIn("chunk_ids", Run._fields)

    def test_chunk_model_fields(self):
        """parqcast.chunk model should be accessible and have expected fields."""
        Chunk = self.env["parqcast.chunk"]
        self.assertIn("collector", Chunk._fields)
        self.assertIn("row_count", Chunk._fields)
        self.assertIn("run_id", Chunk._fields)
