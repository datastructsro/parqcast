# Parqcast Data Dictionary

## Overview
This document serves as the single source of truth for the data architecture within the `parqcast` repository. Parqcast extracts operational data from Odoo, serializes it into Apache Parquet format via PyArrow, and transmits it for external forecasting, predictive replenishment, and supply chain planning.

**Critical Note for AI Agents & Developers:**
Data is **NOT** extracted via the standard Odoo ORM (`env['...'].search_read()`). Instead, it is extracted using extremely fast, raw PostgreSQL queries defined in `packages/parqcast-collectors/`. The extracted data strictly conforms to the PyArrow schemas defined in `packages/parqcast-core/src/parqcast/schemas/outbound.py`.

When answering questions about available data or modifying the pipeline, you MUST refer to `outbound.py` as the ultimate authority on what data columns are currently supported.

---

## Available Data Entities

Below is a categorized list of the primary data entities currently extracted by Parqcast.

### 1. Manufacturing & Production
- **`MRP_PRODUCTION`** (`mrp_production`): Core manufacturing orders. Extracts state, priorities, and crucial scheduling dates to feed production planning algorithms.
  - **Schema Fields:** `_odoo_mo_id`, `name`, `_odoo_product_id`, `product_name`, `_odoo_bom_id`, `product_qty`, `qty_producing`, `_odoo_uom_id`, `state`, `priority`, `reservation_state`, `date_start`, `date_finished`, `date_deadline`, `_odoo_location_src_id`, `_odoo_location_dest_id`, `_odoo_picking_type_id`, `origin`, `_odoo_company_id`.
- **`MRP_WORKORDER`** (`mrp_workorder`): Specific routing operations tied to an MO. Extracts durations and costs to model workcenter capacity.
  - **Schema Fields:** `_odoo_wo_id`, `_odoo_mo_id`, `display_name`, `_odoo_workcenter_id`, `workcenter_name`, `_odoo_operation_id`, `state`, `date_start`, `date_finished`, `duration_expected`, `duration_unit`, `is_user_working`, `employee_costs_hour`.
- **`BOM`** (`mrp_bom`): Bills of Materials. Essential for recursive material planning.
  - **Schema Fields:** `_odoo_bom_id`, `_odoo_product_tmpl_id`, `_odoo_product_id`, `product_name`, `bom_type`, `product_qty`, `_odoo_uom_id`, `uom_name`, `product_qty_multiple`, `produce_delay`, `days_to_prepare_mo`, `sequence`, `code`, `_odoo_company_id`.
- **`BOM_LINES`** (`mrp_bom_line`): Component-level BOM requirements.
  - **Schema Fields:** `_odoo_bom_line_id`, `_odoo_bom_id`, `_odoo_product_id`, `product_name`, `product_qty`, `_odoo_uom_id`, `uom_name`, `_odoo_operation_id`, `operation_name`, `bom_product_template_attribute_value_ids`.
- **`BOM_OPERATIONS`** (`mrp_routing_workcenter`): Standard cycle times.
  - **Schema Fields:** `_odoo_operation_id`, `_odoo_bom_id`, `name`, `sequence`, `_odoo_workcenter_id`, `workcenter_name`, `time_cycle`, `workcenter_quantity`, `search_mode`, `_odoo_skill_id`, `skill_name`, `post_operation_time`.
- **`WORKCENTER`** (`mrp_workcenter`): Captures default capacity and costs to constrain production schedules.
  - **Schema Fields:** `_odoo_workcenter_id`, `name`, `_odoo_resource_id`, `default_capacity`, `time_efficiency`, `is_tool`, `is_constrained`, `_odoo_owner_id`, `owner_name`, `_odoo_calendar_id`, `calendar_name`, `post_operation_time`, `employee_costs_hour`, `_odoo_company_id`.

### 2. Inventory & Stock
- **`STOCK_QUANT`** (`stock_quant`): Live, real-time snapshot of inventory. Distinguishes between physical and reserved quantity.
  - **Schema Fields:** `_odoo_quant_id`, `_odoo_product_id`, `product_name`, `product_code`, `_odoo_location_id`, `location_name`, `location_usage`, `_odoo_warehouse_id`, `warehouse_code`, `quantity`, `reserved_quantity`, `_odoo_lot_id`, `lot_name`, `expiry_date`, `_odoo_package_id`, `package_name`, `_odoo_owner_id`, `owner_name`, `in_date`, `_odoo_company_id`.
- **`STOCK_MOVE`** (`stock_move`): Planned or pending inventory movements.
  - **Schema Fields:** `_odoo_move_id`, `_odoo_product_id`, `product_name`, `product_uom_qty`, `quantity`, `_odoo_uom_id`, `state`, `priority`, `_odoo_picking_id`, `picking_name`, `_odoo_location_id`, `_odoo_location_dest_id`, `_odoo_warehouse_id`, `_odoo_production_id`, `_odoo_sale_line_id`, `_odoo_purchase_line_id`, `origin`, `date`, `date_deadline`, `delay_alert_date`, `procure_method`, `move_orig_ids`, `move_dest_ids`, `is_subcontract`.
- **`STOCK_MOVE_LINE`** (`stock_move_line`): Granular execution of moves. Tracks the exact lot and expiration.
  - **Schema Fields:** `_odoo_move_line_id`, `_odoo_move_id`, `_odoo_picking_id`, `_odoo_product_id`, `_odoo_product_uom_id`, `quantity`, `_odoo_lot_id`, `lot_name`, `_odoo_package_id`, `_odoo_result_package_id`, `_odoo_owner_id`, `_odoo_location_id`, `_odoo_location_dest_id`, `state`, `date`, `expiration_date`, `_odoo_company_id`.
- **`STOCK_LOCATION`** (`stock_location`): The spatial hierarchy, noting location usage and removal strategy.
  - **Schema Fields:** `_odoo_location_id`, `name`, `complete_name`, `usage`, `_odoo_parent_id`, `_odoo_warehouse_id`, `warehouse_code`, `removal_strategy`, `_odoo_storage_category_id`, `storage_category_name`, `active`, `_odoo_company_id`.
- **`STOCK_PICKING`** (`stock_picking`): The overarching transfer document (receipts/deliveries).
  - **Schema Fields:** `_odoo_picking_id`, `name`, `state`, `picking_type_code`, `_odoo_location_id`, `_odoo_location_dest_id`, `scheduled_date`, `date_deadline`, `date_done`, `origin`, `_odoo_partner_id`, `_odoo_backorder_id`, `_odoo_sale_id`, `priority`, `move_type`, `_odoo_company_id`.
- **`ORDERPOINT`** (`stock_warehouse_orderpoint`): Configured reordering rules.
  - **Schema Fields:** `_odoo_orderpoint_id`, `_odoo_product_id`, `product_name`, `_odoo_warehouse_id`, `warehouse_code`, `_odoo_location_id`, `location_name`, `product_min_qty`, `product_max_qty`, `trigger`, `active`, `snoozed_until`, `_odoo_route_id`, `route_name`, `deadline_date`, `_odoo_replenishment_uom_id`, `qty_to_order_computed`, `qty_to_order_manual`, `_odoo_supplier_id`, `_odoo_company_id`.

### 3. Sales & Purchasing
- **`SALE_ORDER`** (`sale_order`): Customer orders.
  - **Schema Fields:** `_odoo_so_id`, `name`, `state`, `_odoo_partner_id`, `date_order`, `commitment_date`, `_odoo_warehouse_id`, `warehouse_code`, `picking_policy`, `amount_untaxed`, `amount_total`, `_odoo_currency_id`, `invoice_status`, `delivery_status`, `_odoo_company_id`.
- **`SALE_ORDER_LINE`** (`sale_order_line`): Specific order lines tracking requested vs delivered quantities.
  - **Schema Fields:** `_odoo_sol_id`, `_odoo_so_id`, `so_name`, `_odoo_product_id`, `product_name`, `product_uom_qty`, `qty_delivered`, `qty_invoiced`, `_odoo_uom_id`, `uom_name`, `price_unit`, `discount`, `price_subtotal`, `customer_lead`, `_odoo_partner_id`, `partner_name`, `is_company`, `commitment_date`, `date_order`, `so_state`, `sol_state`, `_odoo_warehouse_id`, `warehouse_code`, `picking_policy`.
- **`PURCHASE_ORDER`** (`purchase_order`): Vendor orders showing status and planned dates.
  - **Schema Fields:** `_odoo_po_id`, `name`, `state`, `_odoo_partner_id`, `date_order`, `date_approve`, `date_planned`, `receipt_status`, `invoice_status`, `amount_untaxed`, `amount_total`, `_odoo_currency_id`, `_odoo_picking_type_id`, `_odoo_warehouse_id`, `origin`, `priority`, `_odoo_company_id`.
- **`PURCHASE_ORDER_LINE`** (`purchase_order_line`): Purchased quantities and unit prices.
  - **Schema Fields:** `_odoo_pol_id`, `_odoo_po_id`, `po_name`, `po_state`, `receipt_status`, `_odoo_product_id`, `product_name`, `product_qty`, `qty_received`, `_odoo_uom_id`, `uom_name`, `price_unit`, `_odoo_currency_id`, `date_order`, `date_planned`, `_odoo_partner_id`, `partner_name`, `_odoo_warehouse_id`, `origin`, `_odoo_sale_line_id`, `_odoo_orderpoint_id`, `_odoo_company_id`.
- **`POS_ORDER` & `POS_ORDER_LINE`** (`pos_order`): Point of Sale transactions for retail forecasting.
  - **POS_ORDER Schema Fields:** `_odoo_pos_order_id`, `name`, `state`, `date_order`, `_odoo_partner_id`, `_odoo_session_id`, `_odoo_config_id`, `amount_total`, `amount_tax`, `amount_paid`, `is_refund`, `_odoo_company_id`.
  - **POS_ORDER_LINE Schema Fields:** `_odoo_pos_line_id`, `_odoo_pos_order_id`, `_odoo_product_id`, `full_product_name`, `qty`, `price_unit`, `price_subtotal`, `price_subtotal_incl`, `discount`, `_odoo_company_id`.

### 4. Master Data
- **`PRODUCT`** (`product_product` / `product_template`): Core item master. Extracts critical rules to determine how items are procured.
  - **Schema Fields:** `_odoo_product_id`, `_odoo_template_id`, `name`, `name_lang2`, `name_lang3`, `default_code`, `barcode`, `display_name`, `_odoo_uom_id`, `uom_name`, `uom_factor`, `list_price`, `standard_price`, `weight`, `volume`, `_odoo_categ_id`, `category_name`, `purchase_ok`, `sale_ok`, `is_storable`, `active`, `product_type`, `description_sale`, `invoice_policy`, `purchase_method`, `use_expiration_date`, `service_tracking`, `sale_delay`, `route_ids`, `route_names`, `expiration_time`, `tracking`, `_odoo_company_id`.
- **`PRODUCT_SUPPLIERINFO`** (`product_supplierinfo`): Vendor pricing and constraints. Critical for replenishment planners.
  - **Schema Fields:** `_odoo_supplierinfo_id`, `_odoo_template_id`, `_odoo_product_id`, `_odoo_partner_id`, `partner_name`, `delay`, `min_qty`, `price`, `_odoo_currency_id`, `currency_name`, `sequence`, `date_start`, `date_end`, `batching_window`, `is_subcontractor`.
- **`PARTNER`** (`res_partner`): Suppliers and customers.
  - **Schema Fields:** `_odoo_partner_id`, `name`, `ref`, `is_company`, `_odoo_parent_id`, `parent_name`, `_odoo_country_id`, `customer_rank`, `supplier_rank`, `active`, `_odoo_company_id`.
- **`COMPANY` & `CURRENCY`** (`res_company`, `res_currency`): Context variables like `security_lead` and exchange rates.
  - **COMPANY Schema Fields:** `_odoo_company_id`, `name`, `_odoo_currency_id`, `_odoo_parent_id`, `security_lead`, `active`, `_odoo_country_id`.
  - **CURRENCY Schema Fields:** `_odoo_currency_id`, `name`, `symbol`, `decimal_places`, `rounding`, `active`, `_odoo_rate_id`, `rate`, `rate_date`, `_odoo_rate_company_id`.

### 5. Inbound Actions & Decisions (The Ingesters)
While the entities above describe the data being extracted *out* of Odoo via `parqcast-collectors` (using raw SQL), the external planner also pushes actionable decisions *back into* Odoo. This data is handled by `parqcast-ingesters`, which is the ONLY package explicitly permitted to use the standard Odoo ORM (e.g., `env['purchase.order'].create(...)`) to safely trigger Odoo's internal workflows.

- **`DECISIONS`** (`inbound.py`): The prescriptive actions prescribed by the external AI/planner (e.g., creating a Purchase Order, updating an Orderpoint, scheduling Manufacturing).
  - **Schema Fields:** `decision_id`, `decision_type`, `status`, `item_name`, `_odoo_product_id`, `_odoo_uom_id`, `location_name`, `_odoo_location_id`, `quantity`, `start_date`, `end_date`, `supplier_name`, `_odoo_supplier_id`, `_odoo_bom_id`, `origin_location`, `destination_location`, `parent_reference`, `workcenter_name`, `_odoo_workcenter_id`, `batch`, `remark`, `min_quantity`, `max_quantity`.

---

## Technical Nuances

1. **Internationalization (i18n):** Queries are dynamically parameterized to extract translatable JSONB fields in the company's language. The `parqcast-collectors` system injects the primary language via `self.caps.lang(1)` into the raw SQL (e.g., `name->>'{lang1}'`). `en_US` is only used as a final fallback if the environment lacks language capabilities entirely. This guarantees that LLMs and external systems receive the correctly localized entity names natively.
2. **Timestamps:** All dates and datetimes are exported as UTC to ensure cross-system consistency.
3. **Odoo IDs:** Primary and foreign keys are explicitly typed and prefixed with `_odoo_` in the Parquet schema (e.g., `_odoo_product_id`) to differentiate them from downstream system IDs.
4. **Boolean & Numeric Types:** We strictly map Odoo's internal types to optimized PyArrow equivalents (e.g., `OdooMonetary`, `OdooQuantity`, `OdooId`) to compress file sizes and maximize memory efficiency.

---
*For the exact, up-to-date column definitions, always inspect `outbound.py`.*
