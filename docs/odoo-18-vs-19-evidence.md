# Odoo 18 → 19 Schema Evidence

**Purpose.** This document is the factual backing for [`versioning-plan.md`](./versioning-plan.md). Every claim cites a file:line in the Odoo community sources at `/Users/thatoleg/datastructsro/replenishment-investigation/community-{18,19}`. Where parqcast's current collector docstrings disagree with what the source actually says, that's called out — those are bugs waiting to bite.

Scope: models currently pulled by parqcast collectors/ingesters.

---

## Severity legend

- **(A) Schema break** — column/table renamed or removed. SQL that worked on v18 will error on v19 (or vice versa).
- **(B) Semantic change** — same column name, different meaning. **Worst kind** because SQL "works" and returns wrong data.
- **(C) Additive / no-op** — field added with no removal, or field unchanged. No code action needed.

---

## 1. `uom.uom` / `uom.category` — **(A) Schema break**

### v18

- `uom.category` is its own model with `name = fields.Char(..., translate=True)` — `community-18/addons/uom/models/uom_uom.py:12, 15`.
- `uom.uom.category_id` is a `Many2one('uom.category', ...)` — `community-18/addons/uom/models/uom_uom.py:56`.
- Category is how UOMs are grouped for convertibility.

### v19

- `uom.category` **does not exist**. The model class is gone from `community-19/addons/uom/models/uom_uom.py` (only `uom.uom` class present).
- `uom.uom` now has `_parent_name = 'relative_uom_id'` — `community-19/addons/uom/models/uom_uom.py:20`.
- New field `relative_uom_id = Many2one('uom.uom', 'Reference Unit')` replaces category membership — `community-19/addons/uom/models/uom_uom.py:41`.
- New field `parent_path = Char(index=True)` for tree traversal — `community-19/addons/uom/models/uom_uom.py:44`.

### Parqcast collector docstring claim

> "Odoo 19: uom_category removed. Hierarchy via relative_uom_id + parent_path."

**Verdict: correct.** The uom collector must genuinely branch between v18 and v19.

---

## 2. `purchase.order.line.product_uom` — **(A) Schema break**

### v18

`product_uom = fields.Many2one('uom.uom', string='Unit of Measure', ...)` — `community-18/addons/purchase/models/purchase_order_line.py:34`.

### v19

Field is renamed to `product_uom_id` — `community-19/addons/purchase/models/purchase_order_line.py:36`:

```python
product_uom_id = fields.Many2one('uom.uom', string='Unit', ...)
```

All references in v19 use `product_uom_id` (e.g. lines 162, 197, 199, 274, 385, 398, 400, 438).

### Parqcast collector docstring claim

> "Odoo 19: product_uom → product_uom_id"

**Verdict: correct.**

---

## 3. `stock.location.scrap_location` — **(A) Schema break**

### v18

`scrap_location = fields.Boolean(...)` — `community-18/addons/stock/models/stock_location.py:71`.

### v19

Field is absent. The scrap check is now expressed by `usage = 'inventory'` — see the constraint `_check_scrap_location` at `community-19/addons/stock/models/stock_location.py:198`, which references `usage='inventory'` instead of a dedicated boolean.

### Parqcast collector docstring claim

> "Odoo 19: scrap_location and return_location columns removed"

**Verdict: partially correct.** `scrap_location` confirmed gone. **`return_location`: no evidence in any examined file in either version** — this part of the docstring may be folklore. Worth grepping `enterprise-{18,19}` before acting on it.

---

## 4. `mrp.routing.workcenter.time_cycle` — **(B) Semantic change — dangerous**

This is the nastiest kind of change: **same field name, different meaning.**

### v18

`community-18/addons/mrp/models/mrp_routing.py:45`:

```python
time_cycle = fields.Float('Duration', compute="_compute_time_cycle")
```

Unit: **minutes** (it's a duration).

### v19

`community-19/addons/mrp/models/mrp_routing.py:38`:

```python
time_cycle = fields.Float('Cycles', compute="_compute_time_cycle")
```

Unit: **count** (number of cycles / repetitions). The "duration" concept moved to new fields at `community-19/addons/mrp/models/mrp_routing.py:57-59`:

```python
cycle_number = fields.Integer("Repetitions", compute="_compute_time_cycle")
time_total  = fields.Float('Total Duration', compute="_compute_time_cycle")
show_time_total = fields.Boolean('Show Total Duration?', compute="_compute_time_cycle")
```

So in v19, **`time_cycle` × `cycle_number` ≈ `time_total`** (the old v18 `time_cycle`).

`time_cycle_manual` exists in both versions (`community-18:40`, `community-19:33`) and is the operator-entered override.

### Parqcast collector docstring claim

> "mrp.bom: time_cycle renamed to time_cycle_manual"

**Verdict: wrong on both counts.**
- The field lives on `mrp.routing.workcenter`, not `mrp.bom`.
- Nothing was renamed. Both `time_cycle` and `time_cycle_manual` exist in both v18 and v19. The actual change is that **`time_cycle` silently changed its unit of measurement from minutes to cycle count**. A v18-era collector running against v19 will push numerically plausible but semantically garbage data to Snowflake.

**Action:** v19 collector should export `time_total` (new) when operation duration is wanted. This is a concrete example of why per-version code isolation isn't optional.

---

## 5. `product.product.standard_price` — **(C) No v18→v19 change**

### v18 and v19 (identical)

Both define `standard_price = fields.Float('Cost', company_dependent=True, …)`:
- `community-18/addons/product/models/product_product.py:54-60`
- `community-19/addons/product/models/product_product.py:62-68`

### Parqcast collector docstring claim

> "Odoo 19: standard_price on product_product as JSONB, needs cast; no price_extra"

**Verdict: misleading on both points.**

**On JSONB storage:** `standard_price` is `company_dependent=True`. Since Odoo's general company-dependent fields refactor (shipped **before** 18), these are stored as JSONB keyed by company on the shared table. That's an Odoo-wide representation, not a v19 change. If the SQL needs a JSONB cast, it needs that cast against v18 too.

**On `price_extra`:** still defined in v19 at `community-19/addons/product/models/product_product.py:25-26`:

```python
price_extra = fields.Float(
    'Variant Price Extra', compute='_compute_product_price_extra', ...)
```

With computations still referring to it at lines 314, 317, 320, 322, 334. **The "no price_extra" claim is plain wrong.**

---

## 6. `stock.warehouse.orderpoint` — **(C) No v18→v19 change**

- `qty_on_hand` / `qty_forecast`: computed, `store=False` in both versions.
  - `community-18/addons/stock/models/stock_orderpoint.py:83-84`
  - `community-19/addons/stock/models/stock_orderpoint.py:85-86`
- `product_uom` (field name): **unchanged** between 18 and 19 on this model.
  - `community-18/addons/stock/models/stock_orderpoint.py:54-56`
  - `community-19/addons/stock/models/stock_orderpoint.py:53-55`

### Parqcast collector docstring claim

> "Odoo 19: qty_on_hand/qty_forecast are computed, not stored"

**Verdict: technically true for v19 but also true for v18.** Not a v19 discriminator. The collector either cannot rely on these columns existing (correct) or must compute them in SQL — same strategy in both versions.

### Unrelated parqcast claim in the same area

> "product_uom → product_uom_id" (on `stock.warehouse.orderpoint`)

**Wrong on this model.** The rename happened on `purchase.order.line` (§2), not here.

---

## 7. `resource.calendar.leaves` — **(C) No v18→v19 change**

`resource_id = fields.Many2one(...)` in both:
- `community-18/addons/resource/models/resource_calendar_leaves.py:47`
- `community-19/addons/resource/models/resource_calendar_leaves.py:47`

Depends-clause at line 53 is identical across versions.

### Parqcast collector docstring claim

> "Odoo 19: no resource_id; Has duration_days/hours"

**Verdict: unsupported by the source.** `resource_id` exists in v19. No `duration_days` / `duration_hours` field found on any calendar model in either version. If the calendar collector is branching on this claim, it's branching on a phantom.

---

## 8. `uom.uom.name` — **(C) No v18→v19 change (but general note)**

Both versions:

```python
name = fields.Char(..., translate=True)
```

- `community-18/addons/uom/models/uom_uom.py:55` (on `uom.uom` — the category line at :15 is `uom.category.name`).
- `community-19/addons/uom/models/uom_uom.py:34`.

Since Odoo 16/17's translation-storage refactor, Postgres columns for `translate=True` fields are JSONB. That's Odoo-wide and predates 18. The "uom.name is JSONB" observation is accurate about Postgres but is **not** a v18→v19 break.

---

## 9. `mrp.bom` header — minor label shift only

`digits='Product Unit of Measure'` in v18 (`community-18/addons/mrp/models/mrp_bom.py:45`) becomes `digits='Product Unit'` in v19 (`community-19/addons/mrp/models/mrp_bom.py:44`). Cosmetic. No SQL impact.

---

## Summary matrix

| Model / field | v18 → v19 change | Severity | Parqcast docstring status |
|---|---|---|---|
| `uom.category` removed; `relative_uom_id` + `parent_path` on `uom.uom` | Schema | **A** | **correct** |
| `purchase.order.line.product_uom` → `product_uom_id` | Rename | **A** | **correct** |
| `stock.location.scrap_location` removed | Removal | **A** | partially correct (`return_location` claim unsupported) |
| `mrp.routing.workcenter.time_cycle`: Duration → Cycles count | Meaning flip | **B** | **wrong model + wrong description** |
| `product.product.standard_price` JSONB | Unchanged (pre-v18) | — | misleadingly attributed to v19 |
| `product.product.price_extra` | Present in both | — | **"removed in v19" is false** |
| `stock.warehouse.orderpoint.qty_on_hand/qty_forecast` computed | Unchanged | — | true but not v19-specific |
| `stock.warehouse.orderpoint.product_uom` | Unchanged | — | rename claim wrong for this model |
| `resource.calendar.leaves.resource_id` | Unchanged | — | **"removed in v19" unsupported** |
| `uom.uom.name` JSONB-backed (translatable) | Unchanged (pre-v18) | — | attributed to v19 in docstrings |
| `mrp.bom` label change | Cosmetic | **C** | n/a |

---

## Implications for the versioning plan

1. **Real v18→v19 breaks are few and specific** — §§1–4. The planned `v19/` subpackage needs version-branching for: uom hierarchy, purchase line uom field rename, scrap_location boolean, mrp operation duration semantics. That's it on the currently-examined surface.

2. **Several parqcast docstrings are wrong.** When migrating collectors into `parqcast/collectors/v19/`, treat each docstring as a hypothesis to re-verify against the source, not a specification. The current code may already be doing the wrong thing (e.g. `time_cycle` unit mismatch, `price_extra` assumed absent).

3. **The most dangerous class of change is §4** — same column name, different meaning, no type signature to catch it. A generic/base type system cannot detect this. The only defense is:
   - Explicit v19-suffixed collector classes with explicit comments citing the meaning change.
   - Downstream schema contracts (PyArrow `OdooDuration` dtype vs a new `OdooCycleCount`) that force the collector author to pick the right target column.
   - An integration test against a seeded v19 DB that compares `time_cycle × cycle_number ≈ time_total` and fails loud if the mapping is wrong.

4. **A lot of the alleged v19 surface is actually Odoo-wide** — JSONB storage for `company_dependent` fields, JSONB for translatable Chars. Don't branch on these per major version; they're constant from v18 onward and the SQL that handles them is the same in both `v18/` and `v19/` collectors. Shared helpers belong in `parqcast.core`, not duplicated per major.

5. **Scope for an Odoo 18 collector set (`v18/`), if it becomes needed,** is bounded: invert §§1–4 and keep §§5–9 shared. A `v18/` subpackage would be roughly the same size as `v19/` minus the four real deltas. This validates the "one directory per major, bounded cost" assumption in `versioning-plan.md`.

---

## Files consulted (for re-verification)

```
community-18/addons/uom/models/uom_uom.py
community-19/addons/uom/models/uom_uom.py
community-18/addons/product/models/product_product.py
community-19/addons/product/models/product_product.py
community-18/addons/stock/models/stock_location.py
community-19/addons/stock/models/stock_location.py
community-18/addons/stock/models/stock_orderpoint.py
community-19/addons/stock/models/stock_orderpoint.py
community-18/addons/purchase/models/purchase_order_line.py
community-19/addons/purchase/models/purchase_order_line.py
community-18/addons/mrp/models/mrp_bom.py
community-19/addons/mrp/models/mrp_bom.py
community-18/addons/mrp/models/mrp_routing.py
community-19/addons/mrp/models/mrp_routing.py
community-18/addons/resource/models/resource_calendar_leaves.py
community-19/addons/resource/models/resource_calendar_leaves.py
```

Enterprise addon sources under `enterprise-{18,19}` were **not** consulted for this pass. If any collector pulls enterprise-only tables (e.g. MPS, quality, advanced mrp), re-run the comparison there before finalizing the v19 collector set.
