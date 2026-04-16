"""
PyArrow schemas for all outbound parquet files.
Targeting Odoo 19+ schema. Uses named types from odoo_types.
"""

import pyarrow as pa

from .odoo_types import (
    OdooBoolean,
    OdooCode,
    OdooDate,
    OdooDatetime,
    OdooDuration,
    OdooFactor,
    OdooFloat,
    OdooId,
    OdooIdList,
    OdooMonetary,
    OdooName,
    OdooPath,
    OdooQuantity,
    OdooSequence,
    OdooState,
    OdooText,
    OdooType,
)

PRODUCT_SCHEMA = pa.schema(
    [
        ("_odoo_product_id", OdooId),
        ("_odoo_template_id", OdooId),
        ("name", OdooName),
        ("name_lang2", OdooName),
        ("name_lang3", OdooName),
        ("default_code", OdooCode),
        ("barcode", OdooCode),
        ("display_name", OdooName),
        ("_odoo_uom_id", OdooId),
        ("uom_name", OdooName),
        ("uom_factor", OdooFactor),
        ("list_price", OdooMonetary),
        ("standard_price", OdooMonetary),
        ("weight", OdooFloat),
        ("volume", OdooFloat),
        ("_odoo_categ_id", OdooId),
        ("category_name", OdooName),
        ("purchase_ok", OdooBoolean),
        ("sale_ok", OdooBoolean),
        ("is_storable", OdooBoolean),
        ("active", OdooBoolean),
        ("product_type", OdooType),
        ("description_sale", OdooText),
        ("invoice_policy", OdooType),
        ("purchase_method", OdooType),
        ("use_expiration_date", OdooBoolean),
        ("service_tracking", OdooType),
        ("sale_delay", OdooDuration),
        ("route_ids", OdooIdList),
        ("route_names", OdooText),
        ("expiration_time", OdooDuration),
        ("tracking", OdooType),
        ("_odoo_company_id", OdooId),
    ]
)

PRODUCT_SUPPLIERINFO_SCHEMA = pa.schema(
    [
        ("_odoo_supplierinfo_id", OdooId),
        ("_odoo_template_id", OdooId),
        ("_odoo_product_id", OdooId),
        ("_odoo_partner_id", OdooId),
        ("partner_name", OdooName),
        ("delay", OdooSequence),
        ("min_qty", OdooQuantity),
        ("price", OdooMonetary),
        ("_odoo_currency_id", OdooId),
        ("currency_name", OdooCode),
        ("sequence", OdooSequence),
        ("date_start", OdooDate),
        ("date_end", OdooDate),
        ("batching_window", OdooSequence),
        ("is_subcontractor", OdooBoolean),
    ]
)

STOCK_QUANT_SCHEMA = pa.schema(
    [
        ("_odoo_quant_id", OdooId),
        ("_odoo_product_id", OdooId),
        ("product_name", OdooName),
        ("product_code", OdooCode),
        ("_odoo_location_id", OdooId),
        ("location_name", OdooName),
        ("location_usage", OdooType),
        ("_odoo_warehouse_id", OdooId),
        ("warehouse_code", OdooCode),
        ("quantity", OdooQuantity),
        ("reserved_quantity", OdooQuantity),
        ("_odoo_lot_id", OdooId),
        ("lot_name", OdooName),
        ("expiry_date", OdooDatetime),
        ("_odoo_package_id", OdooId),
        ("package_name", OdooName),
        ("_odoo_owner_id", OdooId),
        ("owner_name", OdooName),
        ("in_date", OdooDatetime),
        ("_odoo_company_id", OdooId),
    ]
)

STOCK_MOVE_SCHEMA = pa.schema(
    [
        ("_odoo_move_id", OdooId),
        ("_odoo_product_id", OdooId),
        ("product_name", OdooName),
        ("product_uom_qty", OdooQuantity),
        ("quantity", OdooQuantity),
        ("_odoo_uom_id", OdooId),
        ("state", OdooState),
        ("priority", OdooType),
        ("_odoo_picking_id", OdooId),
        ("picking_name", OdooName),
        ("_odoo_location_id", OdooId),
        ("_odoo_location_dest_id", OdooId),
        ("_odoo_warehouse_id", OdooId),
        ("_odoo_production_id", OdooId),
        ("_odoo_sale_line_id", OdooId),
        ("_odoo_purchase_line_id", OdooId),
        ("origin", OdooText),
        ("date", OdooDatetime),
        ("date_deadline", OdooDatetime),
        ("delay_alert_date", OdooDatetime),
        ("procure_method", OdooType),
        ("move_orig_ids", OdooIdList),
        ("move_dest_ids", OdooIdList),
        ("is_subcontract", OdooBoolean),
    ]
)

STOCK_LOCATION_SCHEMA = pa.schema(
    [
        ("_odoo_location_id", OdooId),
        ("name", OdooName),
        ("complete_name", OdooName),
        ("usage", OdooType),
        ("_odoo_parent_id", OdooId),
        ("_odoo_warehouse_id", OdooId),
        ("warehouse_code", OdooCode),
        ("removal_strategy", OdooType),
        ("_odoo_storage_category_id", OdooId),
        ("storage_category_name", OdooName),
        ("active", OdooBoolean),
        ("_odoo_company_id", OdooId),
    ]
)

SALE_ORDER_LINE_SCHEMA = pa.schema(
    [
        ("_odoo_sol_id", OdooId),
        ("_odoo_so_id", OdooId),
        ("so_name", OdooName),
        ("_odoo_product_id", OdooId),
        ("product_name", OdooName),
        ("product_uom_qty", OdooQuantity),
        ("qty_delivered", OdooQuantity),
        ("qty_invoiced", OdooQuantity),
        ("_odoo_uom_id", OdooId),
        ("uom_name", OdooName),
        ("price_unit", OdooMonetary),
        ("discount", OdooFloat),
        ("price_subtotal", OdooMonetary),
        ("customer_lead", OdooFloat),
        ("_odoo_partner_id", OdooId),
        ("partner_name", OdooName),
        ("is_company", OdooBoolean),
        ("commitment_date", OdooDatetime),
        ("date_order", OdooDatetime),
        ("so_state", OdooState),
        ("sol_state", OdooState),
        ("_odoo_warehouse_id", OdooId),
        ("warehouse_code", OdooCode),
        ("picking_policy", OdooType),
    ]
)

PURCHASE_ORDER_LINE_SCHEMA = pa.schema(
    [
        ("_odoo_pol_id", OdooId),
        ("_odoo_po_id", OdooId),
        ("po_name", OdooName),
        ("po_state", OdooState),
        ("receipt_status", OdooState),
        ("_odoo_product_id", OdooId),
        ("product_name", OdooName),
        ("product_qty", OdooQuantity),
        ("qty_received", OdooQuantity),
        ("_odoo_uom_id", OdooId),
        ("uom_name", OdooName),
        ("price_unit", OdooMonetary),
        ("_odoo_currency_id", OdooId),
        ("date_order", OdooDatetime),
        ("date_planned", OdooDatetime),
        ("_odoo_partner_id", OdooId),
        ("partner_name", OdooName),
        ("_odoo_warehouse_id", OdooId),
        ("origin", OdooText),
        ("_odoo_sale_line_id", OdooId),
        ("_odoo_orderpoint_id", OdooId),
        ("_odoo_company_id", OdooId),
    ]
)

MRP_PRODUCTION_SCHEMA = pa.schema(
    [
        ("_odoo_mo_id", OdooId),
        ("name", OdooName),
        ("_odoo_product_id", OdooId),
        ("product_name", OdooName),
        ("_odoo_bom_id", OdooId),
        ("product_qty", OdooQuantity),
        ("qty_producing", OdooQuantity),
        ("_odoo_uom_id", OdooId),
        ("state", OdooState),
        ("priority", OdooType),
        ("reservation_state", OdooState),
        ("date_start", OdooDatetime),
        ("date_finished", OdooDatetime),
        ("date_deadline", OdooDatetime),
        ("_odoo_location_src_id", OdooId),
        ("_odoo_location_dest_id", OdooId),
        ("_odoo_picking_type_id", OdooId),
        ("origin", OdooText),
        ("_odoo_company_id", OdooId),
    ]
)

MRP_WORKORDER_SCHEMA = pa.schema(
    [
        ("_odoo_wo_id", OdooId),
        ("_odoo_mo_id", OdooId),
        ("display_name", OdooName),
        ("_odoo_workcenter_id", OdooId),
        ("workcenter_name", OdooName),
        ("_odoo_operation_id", OdooId),
        ("state", OdooState),
        ("date_start", OdooDatetime),
        ("date_finished", OdooDatetime),
        ("duration_expected", OdooDuration),
        ("duration_unit", OdooDuration),
        ("is_user_working", OdooBoolean),
        ("employee_costs_hour", OdooMonetary),
    ]
)

BOM_SCHEMA = pa.schema(
    [
        ("_odoo_bom_id", OdooId),
        ("_odoo_product_tmpl_id", OdooId),
        ("_odoo_product_id", OdooId),
        ("product_name", OdooName),
        ("bom_type", OdooType),
        ("product_qty", OdooQuantity),
        ("_odoo_uom_id", OdooId),
        ("uom_name", OdooName),
        ("product_qty_multiple", OdooQuantity),
        ("produce_delay", OdooDuration),
        ("days_to_prepare_mo", OdooDuration),
        ("sequence", OdooSequence),
        ("code", OdooCode),
        ("_odoo_company_id", OdooId),
    ]
)

BOM_LINES_SCHEMA = pa.schema(
    [
        ("_odoo_bom_line_id", OdooId),
        ("_odoo_bom_id", OdooId),
        ("_odoo_product_id", OdooId),
        ("product_name", OdooName),
        ("product_qty", OdooQuantity),
        ("_odoo_uom_id", OdooId),
        ("uom_name", OdooName),
        ("_odoo_operation_id", OdooId),
        ("operation_name", OdooName),
        ("bom_product_template_attribute_value_ids", OdooIdList),
    ]
)

BOM_OPERATIONS_SCHEMA = pa.schema(
    [
        ("_odoo_operation_id", OdooId),
        ("_odoo_bom_id", OdooId),
        ("name", OdooName),
        ("sequence", OdooSequence),
        ("_odoo_workcenter_id", OdooId),
        ("workcenter_name", OdooName),
        ("time_cycle", OdooDuration),
        ("workcenter_quantity", OdooSequence),
        ("search_mode", OdooType),
        ("_odoo_skill_id", OdooId),
        ("skill_name", OdooName),
        ("post_operation_time", OdooDuration),
    ]
)

BOM_BYPRODUCT_SCHEMA = pa.schema(
    [
        ("_odoo_byproduct_id", OdooId),
        ("_odoo_bom_id", OdooId),
        ("_odoo_product_id", OdooId),
        ("product_qty", OdooQuantity),
        ("_odoo_product_uom_id", OdooId),
        ("cost_share", OdooFloat),
        ("_odoo_company_id", OdooId),
    ]
)

WORKCENTER_SCHEMA = pa.schema(
    [
        ("_odoo_workcenter_id", OdooId),
        ("name", OdooName),
        ("_odoo_resource_id", OdooId),
        ("default_capacity", OdooQuantity),
        ("time_efficiency", OdooFloat),
        ("is_tool", OdooBoolean),
        ("is_constrained", OdooBoolean),
        ("_odoo_owner_id", OdooId),
        ("owner_name", OdooName),
        ("_odoo_calendar_id", OdooId),
        ("calendar_name", OdooName),
        ("post_operation_time", OdooDuration),
        ("employee_costs_hour", OdooMonetary),
        ("_odoo_company_id", OdooId),
    ]
)

WORKCENTER_CAPACITY_SCHEMA = pa.schema(
    [
        ("_odoo_capacity_id", OdooId),
        ("_odoo_workcenter_id", OdooId),
        ("_odoo_product_id", OdooId),
        ("capacity", OdooQuantity),
        ("time_start", OdooDuration),
        ("time_stop", OdooDuration),
    ]
)

CALENDAR_SCHEMA = pa.schema(
    [
        ("_odoo_calendar_id", OdooId),
        ("calendar_name", OdooName),
        ("timezone", OdooCode),
        ("_odoo_attendance_id", OdooId),
        ("is_working", OdooBoolean),
        ("day_of_week", OdooSequence),
        ("hour_from", OdooDuration),
        ("hour_to", OdooDuration),
        ("duration_days", OdooDuration),
        ("duration_hours", OdooDuration),
        ("week_type", OdooType),
        ("day_period", OdooType),
    ]
)

CALENDAR_LEAVES_SCHEMA = pa.schema(
    [
        ("_odoo_leave_id", OdooId),
        ("name", OdooName),
        ("date_from", OdooDatetime),
        ("date_to", OdooDatetime),
        ("_odoo_resource_id", OdooId),
        ("_odoo_calendar_id", OdooId),
        ("time_type", OdooType),
        ("_odoo_company_id", OdooId),
    ]
)

ORDERPOINT_SCHEMA = pa.schema(
    [
        ("_odoo_orderpoint_id", OdooId),
        ("_odoo_product_id", OdooId),
        ("product_name", OdooName),
        ("_odoo_warehouse_id", OdooId),
        ("warehouse_code", OdooCode),
        ("_odoo_location_id", OdooId),
        ("location_name", OdooName),
        ("product_min_qty", OdooQuantity),
        ("product_max_qty", OdooQuantity),
        ("trigger", OdooType),
        ("active", OdooBoolean),
        ("snoozed_until", OdooDate),
        ("_odoo_route_id", OdooId),
        ("route_name", OdooName),
        ("deadline_date", OdooDate),
        ("_odoo_replenishment_uom_id", OdooId),
        ("qty_to_order_computed", OdooQuantity),
        ("qty_to_order_manual", OdooQuantity),
        ("_odoo_supplier_id", OdooId),
        ("_odoo_company_id", OdooId),
    ]
)

UOM_SCHEMA = pa.schema(
    [
        ("_odoo_uom_id", OdooId),
        ("name", OdooName),
        ("_odoo_relative_uom_id", OdooId),
        ("parent_path", OdooPath),
        ("factor", OdooFactor),
        ("relative_factor", OdooFactor),
        ("active", OdooBoolean),
    ]
)

PARTNER_SCHEMA = pa.schema(
    [
        ("_odoo_partner_id", OdooId),
        ("name", OdooName),
        ("ref", OdooCode),
        ("is_company", OdooBoolean),
        ("_odoo_parent_id", OdooId),
        ("parent_name", OdooName),
        ("_odoo_country_id", OdooId),
        ("customer_rank", OdooSequence),
        ("supplier_rank", OdooSequence),
        ("active", OdooBoolean),
        ("_odoo_company_id", OdooId),
    ]
)

COMPANY_SCHEMA = pa.schema(
    [
        ("_odoo_company_id", OdooId),
        ("name", OdooName),
        ("_odoo_currency_id", OdooId),
        ("_odoo_parent_id", OdooId),
        ("security_lead", OdooFloat),
        ("active", OdooBoolean),
    ]
)

CURRENCY_SCHEMA = pa.schema(
    [
        ("_odoo_currency_id", OdooId),
        ("name", OdooCode),
        ("symbol", OdooCode),
        ("decimal_places", OdooSequence),
        ("rounding", OdooFloat),
        ("active", OdooBoolean),
        ("_odoo_rate_id", OdooId),
        ("rate", OdooFloat),
        ("rate_date", OdooDate),
        ("_odoo_rate_company_id", OdooId),
    ]
)

STOCK_WAREHOUSE_SCHEMA = pa.schema(
    [
        ("_odoo_warehouse_id", OdooId),
        ("name", OdooName),
        ("code", OdooCode),
        ("_odoo_lot_stock_id", OdooId),
        ("_odoo_wh_input_stock_loc_id", OdooId),
        ("_odoo_wh_output_stock_loc_id", OdooId),
        ("reception_steps", OdooType),
        ("delivery_steps", OdooType),
        ("active", OdooBoolean),
        ("_odoo_company_id", OdooId),
    ]
)

STOCK_PICKING_SCHEMA = pa.schema(
    [
        ("_odoo_picking_id", OdooId),
        ("name", OdooName),
        ("state", OdooState),
        ("picking_type_code", OdooType),
        ("_odoo_location_id", OdooId),
        ("_odoo_location_dest_id", OdooId),
        ("scheduled_date", OdooDatetime),
        ("date_deadline", OdooDatetime),
        ("date_done", OdooDatetime),
        ("origin", OdooText),
        ("_odoo_partner_id", OdooId),
        ("_odoo_backorder_id", OdooId),
        ("_odoo_sale_id", OdooId),
        ("priority", OdooType),
        ("move_type", OdooType),
        ("_odoo_company_id", OdooId),
    ]
)

STOCK_PICKING_TYPE_SCHEMA = pa.schema(
    [
        ("_odoo_picking_type_id", OdooId),
        ("name", OdooName),
        ("code", OdooType),
        ("sequence_code", OdooCode),
        ("_odoo_default_location_src_id", OdooId),
        ("_odoo_default_location_dest_id", OdooId),
        ("_odoo_warehouse_id", OdooId),
        ("active", OdooBoolean),
        ("_odoo_company_id", OdooId),
    ]
)

STOCK_ROUTE_SCHEMA = pa.schema(
    [
        ("_odoo_route_id", OdooId),
        ("route_name", OdooName),
        ("route_active", OdooBoolean),
        ("_odoo_rule_id", OdooId),
        ("rule_name", OdooName),
        ("action", OdooType),
        ("procure_method", OdooType),
        ("_odoo_picking_type_id", OdooId),
        ("picking_type_code", OdooType),
        ("_odoo_location_src_id", OdooId),
        ("_odoo_location_dest_id", OdooId),
        ("delay", OdooSequence),
        ("sequence", OdooSequence),
        ("_odoo_warehouse_id", OdooId),
        ("_odoo_company_id", OdooId),
        ("route_warehouse_ids", OdooIdList),
    ]
)

STOCK_STORAGE_CATEGORY_SCHEMA = pa.schema(
    [
        ("_odoo_storage_category_id", OdooId),
        ("name", OdooName),
        ("max_weight", OdooFloat),
        ("allow_new_product", OdooType),
        ("_odoo_company_id", OdooId),
    ]
)

STOCK_PACKAGE_TYPE_SCHEMA = pa.schema(
    [
        ("_odoo_package_type_id", OdooId),
        ("name", OdooName),
        ("barcode", OdooCode),
        ("height", OdooFloat),
        ("width", OdooFloat),
        ("packaging_length", OdooFloat),
        ("max_weight", OdooFloat),
        ("base_weight", OdooFloat),
        ("_odoo_company_id", OdooId),
    ]
)

STOCK_PACKAGE_SCHEMA = pa.schema(
    [
        ("_odoo_package_id", OdooId),
        ("name", OdooName),
        ("pack_date", OdooDate),
        ("_odoo_location_id", OdooId),
        ("_odoo_package_type_id", OdooId),
        ("shipping_weight", OdooFloat),
        ("_odoo_company_id", OdooId),
    ]
)

STOCK_PUTAWAY_RULE_SCHEMA = pa.schema(
    [
        ("_odoo_putaway_rule_id", OdooId),
        ("_odoo_product_id", OdooId),
        ("_odoo_category_id", OdooId),
        ("_odoo_location_in_id", OdooId),
        ("_odoo_location_out_id", OdooId),
        ("_odoo_storage_category_id", OdooId),
        ("sequence", OdooSequence),
        ("sublocation", OdooType),
        ("active", OdooBoolean),
    ]
)

PRODUCT_REMOVAL_SCHEMA = pa.schema(
    [
        ("_odoo_removal_id", OdooId),
        ("name", OdooName),
        ("method", OdooType),
    ]
)

STOCK_LOT_SCHEMA = pa.schema(
    [
        ("_odoo_lot_id", OdooId),
        ("name", OdooName),
        ("ref", OdooCode),
        ("_odoo_product_id", OdooId),
        ("_odoo_company_id", OdooId),
        ("expiration_date", OdooDatetime),
        ("use_date", OdooDatetime),
        ("removal_date", OdooDatetime),
        ("alert_date", OdooDatetime),
    ]
)

SALE_ORDER_SCHEMA = pa.schema(
    [
        ("_odoo_so_id", OdooId),
        ("name", OdooName),
        ("state", OdooState),
        ("_odoo_partner_id", OdooId),
        ("date_order", OdooDatetime),
        ("commitment_date", OdooDatetime),
        ("_odoo_warehouse_id", OdooId),
        ("warehouse_code", OdooCode),
        ("picking_policy", OdooType),
        ("amount_untaxed", OdooMonetary),
        ("amount_total", OdooMonetary),
        ("_odoo_currency_id", OdooId),
        ("invoice_status", OdooState),
        ("delivery_status", OdooState),
        ("_odoo_company_id", OdooId),
    ]
)

PURCHASE_ORDER_SCHEMA = pa.schema(
    [
        ("_odoo_po_id", OdooId),
        ("name", OdooName),
        ("state", OdooState),
        ("_odoo_partner_id", OdooId),
        ("date_order", OdooDatetime),
        ("date_approve", OdooDatetime),
        ("date_planned", OdooDatetime),
        ("receipt_status", OdooState),
        ("invoice_status", OdooState),
        ("amount_untaxed", OdooMonetary),
        ("amount_total", OdooMonetary),
        ("_odoo_currency_id", OdooId),
        ("_odoo_picking_type_id", OdooId),
        ("_odoo_warehouse_id", OdooId),
        ("origin", OdooText),
        ("priority", OdooType),
        ("_odoo_company_id", OdooId),
    ]
)

PURCHASE_REQUISITION_SCHEMA = pa.schema(
    [
        ("_odoo_requisition_id", OdooId),
        ("name", OdooName),
        ("state", OdooState),
        ("requisition_type", OdooType),
        ("_odoo_vendor_id", OdooId),
        ("vendor_name", OdooName),
        ("_odoo_currency_id", OdooId),
        ("date_start", OdooDate),
        ("date_end", OdooDate),
        ("_odoo_warehouse_id", OdooId),
        ("active", OdooBoolean),
        ("_odoo_company_id", OdooId),
    ]
)

POS_ORDER_SCHEMA = pa.schema(
    [
        ("_odoo_pos_order_id", OdooId),
        ("name", OdooName),
        ("state", OdooState),
        ("date_order", OdooDatetime),
        ("_odoo_partner_id", OdooId),
        ("_odoo_session_id", OdooId),
        ("_odoo_config_id", OdooId),
        ("amount_total", OdooMonetary),
        ("amount_tax", OdooMonetary),
        ("amount_paid", OdooMonetary),
        ("is_refund", OdooBoolean),
        ("_odoo_company_id", OdooId),
    ]
)

POS_ORDER_LINE_SCHEMA = pa.schema(
    [
        ("_odoo_pos_line_id", OdooId),
        ("_odoo_pos_order_id", OdooId),
        ("_odoo_product_id", OdooId),
        ("full_product_name", OdooName),
        ("qty", OdooQuantity),
        ("price_unit", OdooMonetary),
        ("price_subtotal", OdooMonetary),
        ("price_subtotal_incl", OdooMonetary),
        ("discount", OdooFloat),
        ("_odoo_company_id", OdooId),
    ]
)

POS_SESSION_SCHEMA = pa.schema(
    [
        ("_odoo_session_id", OdooId),
        ("name", OdooName),
        ("state", OdooState),
        ("_odoo_config_id", OdooId),
        ("_odoo_user_id", OdooId),
        ("start_at", OdooDatetime),
        ("stop_at", OdooDatetime),
        ("cash_register_balance_start", OdooMonetary),
        ("cash_register_balance_end_real", OdooMonetary),
        ("cash_real_transaction", OdooMonetary),
    ]
)

PRODUCT_CATEGORY_SCHEMA = pa.schema(
    [
        ("_odoo_categ_id", OdooId),
        ("name", OdooName),
        ("complete_name", OdooName),
        ("_odoo_parent_id", OdooId),
        ("parent_path", OdooPath),
        ("_odoo_removal_strategy_id", OdooId),
        ("removal_strategy_name", OdooName),
        ("valuation", OdooType),
        ("cost_method", OdooType),
    ]
)

STOCK_MOVE_LINE_SCHEMA = pa.schema(
    [
        ("_odoo_move_line_id", OdooId),
        ("_odoo_move_id", OdooId),
        ("_odoo_picking_id", OdooId),
        ("_odoo_product_id", OdooId),
        ("_odoo_product_uom_id", OdooId),
        ("quantity", OdooQuantity),
        ("_odoo_lot_id", OdooId),
        ("lot_name", OdooName),
        ("_odoo_package_id", OdooId),
        ("_odoo_result_package_id", OdooId),
        ("_odoo_owner_id", OdooId),
        ("_odoo_location_id", OdooId),
        ("_odoo_location_dest_id", OdooId),
        ("state", OdooState),
        ("date", OdooDatetime),
        ("expiration_date", OdooDatetime),
        ("_odoo_company_id", OdooId),
    ]
)

COUNTRY_SCHEMA = pa.schema(
    [
        ("_odoo_country_id", OdooId),
        ("name", OdooName),
        ("code", OdooCode),
    ]
)

PRICELIST_SCHEMA = pa.schema(
    [
        ("_odoo_pricelist_id", OdooId),
        ("name", OdooName),
        ("_odoo_currency_id", OdooId),
        ("_odoo_company_id", OdooId),
        ("active", OdooBoolean),
    ]
)

PRICELIST_ITEM_SCHEMA = pa.schema(
    [
        ("_odoo_pricelist_item_id", OdooId),
        ("_odoo_pricelist_id", OdooId),
        ("applied_on", OdooType),
        ("compute_price", OdooType),
        ("base", OdooType),
        ("fixed_price", OdooMonetary),
        ("percent_price", OdooFloat),
        ("price_discount", OdooFloat),
        ("price_surcharge", OdooMonetary),
        ("price_round", OdooFloat),
        ("price_min_margin", OdooMonetary),
        ("price_max_margin", OdooMonetary),
        ("min_quantity", OdooQuantity),
        ("date_start", OdooDatetime),
        ("date_end", OdooDatetime),
        ("_odoo_product_tmpl_id", OdooId),
        ("_odoo_product_id", OdooId),
        ("_odoo_categ_id", OdooId),
        ("_odoo_base_pricelist_id", OdooId),
        ("_odoo_company_id", OdooId),
    ]
)

# --- MPS (Master Production Schedule, Enterprise) ---

MPS_SCHEDULE_SCHEMA = pa.schema(
    [
        ("_odoo_schedule_id", OdooId),
        ("_odoo_product_id", OdooId),
        ("_odoo_warehouse_id", OdooId),
        ("_odoo_bom_id", OdooId),
        ("forecast_target_qty", OdooQuantity),
        ("min_to_replenish_qty", OdooQuantity),
        ("replenish_trigger", OdooType),
        ("_odoo_route_id", OdooId),
        ("_odoo_supplier_id", OdooId),
        ("is_indirect", OdooBoolean),
        ("mps_sequence", OdooSequence),
        ("_odoo_company_id", OdooId),
    ]
)

MPS_FORECAST_SCHEMA = pa.schema(
    [
        ("_odoo_forecast_id", OdooId),
        ("_odoo_schedule_id", OdooId),
        ("date", OdooDate),
        ("forecast_qty", OdooQuantity),
        ("replenish_qty", OdooQuantity),
        ("replenish_qty_updated", OdooBoolean),
        ("procurement_launched", OdooBoolean),
    ]
)

# --- Quality (Enterprise) ---

QUALITY_POINT_SCHEMA = pa.schema(
    [
        ("_odoo_point_id", OdooId),
        ("name", OdooCode),
        ("title", OdooName),
        ("sequence", OdooSequence),
        ("_odoo_test_type_id", OdooId),
        ("test_type", OdooCode),
        ("_odoo_team_id", OdooId),
        ("_odoo_company_id", OdooId),
        ("_odoo_user_id", OdooId),
        ("active", OdooBoolean),
        ("measure_on", OdooType),
        ("measure_frequency_type", OdooType),
        ("norm", OdooFloat),
        ("tolerance_min", OdooFloat),
        ("tolerance_max", OdooFloat),
        ("norm_unit", OdooCode),
        ("product_ids", OdooIdList),
        ("picking_type_ids", OdooIdList),
    ]
)

QUALITY_CHECK_SCHEMA = pa.schema(
    [
        ("_odoo_check_id", OdooId),
        ("_odoo_point_id", OdooId),
        ("quality_state", OdooState),
        ("_odoo_product_id", OdooId),
        ("_odoo_picking_id", OdooId),
        ("control_date", OdooDatetime),
        ("_odoo_user_id", OdooId),
        ("_odoo_team_id", OdooId),
        ("_odoo_company_id", OdooId),
        ("measure", OdooFloat),
        ("measure_success", OdooState),
        ("qty_tested", OdooQuantity),
        ("qty_passed", OdooQuantity),
        ("qty_failed", OdooQuantity),
    ]
)

ALL_OUTBOUND_SCHEMAS = {
    # Core
    "uom": UOM_SCHEMA,
    "partner": PARTNER_SCHEMA,
    "product": PRODUCT_SCHEMA,
    "product_category": PRODUCT_CATEGORY_SCHEMA,
    "calendar": CALENDAR_SCHEMA,
    "calendar_leaves": CALENDAR_LEAVES_SCHEMA,
    "company": COMPANY_SCHEMA,
    "country": COUNTRY_SCHEMA,
    "currency": CURRENCY_SCHEMA,
    # Stock
    "stock_location": STOCK_LOCATION_SCHEMA,
    "stock_warehouse": STOCK_WAREHOUSE_SCHEMA,
    "stock_storage_category": STOCK_STORAGE_CATEGORY_SCHEMA,
    "stock_package_type": STOCK_PACKAGE_TYPE_SCHEMA,
    "stock_package": STOCK_PACKAGE_SCHEMA,
    "stock_picking_type": STOCK_PICKING_TYPE_SCHEMA,
    "stock_quant": STOCK_QUANT_SCHEMA,
    "stock_move": STOCK_MOVE_SCHEMA,
    "stock_move_line": STOCK_MOVE_LINE_SCHEMA,
    "stock_picking": STOCK_PICKING_SCHEMA,
    "stock_route": STOCK_ROUTE_SCHEMA,
    "stock_lot": STOCK_LOT_SCHEMA,
    "stock_putaway_rule": STOCK_PUTAWAY_RULE_SCHEMA,
    "product_removal": PRODUCT_REMOVAL_SCHEMA,
    "orderpoint": ORDERPOINT_SCHEMA,
    # Sale
    "sale_order": SALE_ORDER_SCHEMA,
    "sale_order_line": SALE_ORDER_LINE_SCHEMA,
    "pricelist": PRICELIST_SCHEMA,
    "pricelist_item": PRICELIST_ITEM_SCHEMA,
    # Purchase
    "purchase_order": PURCHASE_ORDER_SCHEMA,
    "purchase_order_line": PURCHASE_ORDER_LINE_SCHEMA,
    "product_supplierinfo": PRODUCT_SUPPLIERINFO_SCHEMA,
    "purchase_requisition": PURCHASE_REQUISITION_SCHEMA,
    # POS
    "pos_session": POS_SESSION_SCHEMA,
    "pos_order": POS_ORDER_SCHEMA,
    "pos_order_line": POS_ORDER_LINE_SCHEMA,
    # MRP
    "mrp_production": MRP_PRODUCTION_SCHEMA,
    "mrp_workorder": MRP_WORKORDER_SCHEMA,
    "bom": BOM_SCHEMA,
    "bom_lines": BOM_LINES_SCHEMA,
    "bom_operations": BOM_OPERATIONS_SCHEMA,
    "bom_byproduct": BOM_BYPRODUCT_SCHEMA,
    "workcenter": WORKCENTER_SCHEMA,
    "workcenter_capacity": WORKCENTER_CAPACITY_SCHEMA,
    # MPS (Enterprise)
    "mps_schedule": MPS_SCHEDULE_SCHEMA,
    "mps_forecast": MPS_FORECAST_SCHEMA,
    # Quality (Enterprise)
    "quality_point": QUALITY_POINT_SCHEMA,
    "quality_check": QUALITY_CHECK_SCHEMA,
}
