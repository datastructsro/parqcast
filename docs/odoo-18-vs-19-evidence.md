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

## 4. `mrp.routing.workcenter.time_cycle` — **(C) Label change only, compute unchanged**

> **Corrected 2026-04-18.** The first draft of this section, following a
> surface read of the field declarations, claimed that `time_cycle` silently
> flipped from "Duration in minutes" to "Cycles count" between v18 and v19.
> That conclusion was wrong. A proper reading of the ``_compute_time_cycle``
> body in both versions shows the numeric value is unchanged: minutes per
> cycle, amortised over work orders. Only the display label was renamed.

### v18 compute (`community-18/addons/mrp/models/mrp_routing.py:45, 70-97`)

```python
time_cycle = fields.Float('Duration', compute="_compute_time_cycle")

def _compute_time_cycle(self):
    manual_ops = self.filtered(lambda op: op.time_mode == 'manual')
    for op in manual_ops:
        op.time_cycle = op.time_cycle_manual            # minutes
    for op in self - manual_ops:
        # ... gather total_duration and cycle_number from workorder history ...
        op.time_cycle = total_duration / cycle_number   # minutes per cycle
```

### v19 compute (`community-19/addons/mrp/models/mrp_routing.py:38, 72-102`)

```python
time_cycle = fields.Float('Cycles', compute="_compute_time_cycle")

def _compute_time_cycle(self):
    manual_ops = self.filtered(lambda op: op.time_mode == 'manual')
    for op in manual_ops:
        op.time_cycle = op.time_cycle_manual            # minutes
    for op in self - manual_ops:
        # ... gather total_duration and cycle_number the same way ...
        op.time_cycle = total_duration / cycle_number   # minutes per cycle
```

The compute body is identical apart from whitespace. Only the string label
on the field definition changed from `'Duration'` to `'Cycles'`, which is
purely a UX rename — the Odoo form shows "Cycles" as the column header but
the value is still minutes-per-cycle.

### v19 also adds two neighbouring fields (`community-19/addons/mrp/models/mrp_routing.py:57-59, 121`)

```python
cycle_number = fields.Integer("Repetitions", compute="_compute_time_cycle")
time_total   = fields.Float('Total Duration', compute="_compute_time_cycle")
# time_total = setup + cleanup + cycle_number * time_cycle * 100 / efficiency
```

These are new and additive — not a rename. Downstream code that wants the
total operation duration (setup + cleanup + per-cycle minutes × cycle count)
can read `time_total` on v19; on v18, the equivalent has to be computed in
the caller.

### Parqcast collector docstring

The docstring in the old ``mrp_bom.py`` claimed ``time_cycle was renamed to
time_cycle_manual in Odoo 19``. That was wrong on two counts — both fields
existed in both versions, and the field is on ``mrp.routing.workcenter``,
not ``mrp.bom``. The docstring was corrected when the mrp suite migrated
to ``v19/`` in this branch.

### Net

- `time_cycle`: no action needed. Same field, same semantics, label change
  is cosmetic.
- `time_total` on v19: additive; optional to export as a new column if
  downstream finds it useful. Not required for correctness.

This section is preserved here as an erratum rather than deleted so the
investigative trail (and the lesson — *always read the compute body, not
just the field declaration*) stays visible.

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
| `mrp.routing.workcenter.time_cycle`: label renamed 'Duration' → 'Cycles' | Cosmetic only | **C** | the old docstring's "rename to time_cycle_manual" claim was wrong |
| `product.product.standard_price` JSONB | Unchanged (pre-v18) | — | misleadingly attributed to v19 |
| `product.product.price_extra` | Present in both | — | **"removed in v19" is false** |
| `stock.warehouse.orderpoint.qty_on_hand/qty_forecast` computed | Unchanged | — | true but not v19-specific |
| `stock.warehouse.orderpoint.product_uom` | Unchanged | — | rename claim wrong for this model |
| `resource.calendar.leaves.resource_id` | Unchanged | — | **"removed in v19" unsupported** |
| `uom.uom.name` JSONB-backed (translatable) | Unchanged (pre-v18) | — | attributed to v19 in docstrings |
| `mrp.bom` label change | Cosmetic | **C** | n/a |

---

## Implications for the versioning plan

1. **Real v18→v19 breaks are few and specific** — §§1–3. The `v19/` subpackage
   needs version-branching for three things: the uom-hierarchy rewrite, the
   `purchase.order.line.product_uom` → `product_uom_id` field rename, and the
   removal of the `stock.location.scrap_location` boolean. Everything else
   examined in this document is either unchanged between v18 and v19 or is an
   additive enhancement (e.g. v19's new `time_total` field).

2. **Several parqcast docstrings were wrong or misleading.** The migration
   to `parqcast/collectors/v19/` in this branch treated each docstring as a
   hypothesis to re-verify and corrected the ones that didn't hold up. The
   most instructive example — `time_cycle` — is documented in §4 above as
   an erratum, with the correct investigation next to the original wrong
   conclusion.

3. **A lot of the alleged v19 surface is actually Odoo-wide** — JSONB
   storage for `company_dependent` fields, JSONB for translatable Chars.
   Don't branch on these per major version; they're constant from v18
   onward and the SQL that handles them is the same in any `vN/` collector.
   Shared helpers belong in `parqcast.core`, not duplicated per major.

4. **Scope for an Odoo 18 collector set (`v18/`), if it becomes needed,**
   is bounded: invert §§1–3 and keep §§4–9 shared. A `v18/` subpackage
   would be roughly the same size as `v19/` minus those three real deltas.
   This validates the "one directory per major, bounded cost" assumption
   in `versioning-plan.md`.

5. **Lesson on investigation discipline** — §4's original wrong conclusion
   came from reading the field declaration (``fields.Float('Cycles', …)``)
   without reading the ``_compute_time_cycle`` body. When a field's
   semantics are in question, read the compute; the label on the
   declaration is only a UI hint. The one-line difference would have been
   invisible without opening both files side by side.

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
