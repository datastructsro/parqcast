# Copyright 2025 DataStruct s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ParqcastChunk(models.Model):
    _name = "parqcast.chunk"
    _description = "Parqcast Export Chunk"
    _table = "parqcast_export_chunk"
    _order = "sequence"
    _auto = False

    run_id = fields.Many2one("parqcast.run", readonly=True, ondelete="cascade")
    collector = fields.Char(readonly=True)
    sequence = fields.Integer(readonly=True)
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("created", "Created"),
            ("uploaded", "Uploaded"),
            ("error", "Error"),
        ],
        readonly=True,
    )
    key_from = fields.Integer(readonly=True)
    key_to = fields.Integer(readonly=True)
    row_count = fields.Integer("Rows", readonly=True)
    byte_count = fields.Integer("Bytes", readonly=True)
    duration_seconds = fields.Float("Duration (s)", readonly=True)
    error_message = fields.Text("Error", readonly=True)
    checksum = fields.Char(readonly=True)
