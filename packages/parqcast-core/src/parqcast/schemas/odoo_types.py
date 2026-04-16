"""
Named PyArrow types matching Odoo's type system.

Odoo field types -> PyArrow types, declared once and reused across all schemas.
This ensures consistency and makes the mapping from Odoo's ORM to Parquet explicit.

Usage in schemas:
    from parqcast.schemas.odoo_types import OdooId, OdooFloat, OdooName, ...

    PRODUCT_SCHEMA = pa.schema([
        ("_odoo_product_id", OdooId),
        ("name", OdooName),
        ("list_price", OdooMonetary),
        ...
    ])
"""

import pyarrow as pa

# --- Odoo Integer fields ---

OdooId = pa.int64()
"""Many2one FK, Integer PK, or any Odoo integer field.
Maps to: fields.Many2one, fields.Integer, fields.Id"""

OdooSequence = pa.int64()
"""Ordering/priority fields (sequence, priority).
Maps to: fields.Integer used for ordering"""

# --- Odoo Float/Numeric fields ---

OdooFloat = pa.float64()
"""Generic float field (quantity, factor, duration, etc).
Maps to: fields.Float"""

OdooMonetary = pa.float64()
"""Currency-denominated values (prices, costs).
Maps to: fields.Monetary — always paired with a currency_id column"""

OdooQuantity = pa.float64()
"""Product quantities (on-hand, demand, reserved, ordered).
Maps to: fields.Float with digits='Product Unit'"""

OdooDuration = pa.float64()
"""Time durations in minutes (workcenter cycles, expected durations).
Maps to: fields.Float used for time"""

OdooFactor = pa.float64()
"""UoM conversion factors (uom.factor, relative_factor).
Maps to: fields.Float used for unit conversion ratios"""

# --- Odoo String fields ---

OdooName = pa.string()
"""Translatable name fields. In Odoo 19 these are JSONB in the DB
but we extract ->>'en_US' as plain string.
Maps to: fields.Char, fields.Text, JSONB name fields"""

OdooCode = pa.string()
"""Internal reference codes (default_code, warehouse code, currency code).
Maps to: fields.Char used as business identifiers"""

OdooState = pa.string()
"""Selection fields representing workflow state (draft/confirmed/done/cancel).
Maps to: fields.Selection"""

OdooType = pa.string()
"""Selection fields representing entity type (product type, BOM type, location usage).
Maps to: fields.Selection for type classification"""

OdooText = pa.string()
"""Free-text fields (origin, remarks, descriptions).
Maps to: fields.Text, fields.Char for free-form text"""

OdooIdList = pa.string()
"""Comma-separated ID lists for Many2many relations serialized to string.
E.g., move_orig_ids = '42,55,78'. Not a native Odoo type — our serialization.
Maps to: fields.Many2many (serialized)"""

OdooPath = pa.string()
"""Hierarchical path fields (parent_path on UoM, location).
Maps to: fields.Char for parent_path index"""

# --- Odoo Boolean fields ---

OdooBoolean = pa.bool_()
"""Any boolean field.
Maps to: fields.Boolean"""

# --- Odoo Date/Datetime fields ---

OdooDatetime = pa.timestamp("us", tz="UTC")
"""Datetime fields, always stored as UTC in Odoo.
Maps to: fields.Datetime"""

OdooDate = pa.timestamp("us", tz="UTC")
"""Date fields (stored without time, but we use timestamp for consistency).
Maps to: fields.Date — exported as midnight UTC"""
