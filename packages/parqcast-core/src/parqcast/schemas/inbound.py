import pyarrow as pa

from .odoo_types import (
    OdooCode,
    OdooDatetime,
    OdooId,
    OdooName,
    OdooQuantity,
    OdooState,
    OdooText,
)

DECISIONS_SCHEMA = pa.schema(
    [
        ("decision_id", OdooCode),
        ("decision_type", OdooState),
        ("status", OdooState),
        ("item_name", OdooName),
        ("_odoo_product_id", OdooId),
        ("_odoo_uom_id", OdooId),
        ("location_name", OdooName),
        ("_odoo_location_id", OdooId),
        ("quantity", OdooQuantity),
        ("start_date", OdooDatetime),
        ("end_date", OdooDatetime),
        ("supplier_name", OdooName),
        ("_odoo_supplier_id", OdooId),
        ("_odoo_bom_id", OdooId),
        ("origin_location", OdooCode),
        ("destination_location", OdooCode),
        ("parent_reference", OdooText),
        ("workcenter_name", OdooName),
        ("_odoo_workcenter_id", OdooId),
        ("batch", OdooText),
        ("remark", OdooText),
        ("min_quantity", OdooQuantity),
        ("max_quantity", OdooQuantity),
    ]
)
