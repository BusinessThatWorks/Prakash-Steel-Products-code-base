# Copyright (c) 2025, Prakash Steel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def get_rolled_production_data(from_date=None, to_date=None, item_code=None, production_plan=None):
	"""
	Fetch Rolled Production data for the Production Dashboard.

	Primary source: Billet Cutting (submitted)
	Cross-referenced with:
	  - Production Plan Item (po_items) → FG Planned Qty
	  - Finish Weight → Actual Qty & Burning Loss %

	Returns dict with 'rows' (table data) and 'totals' (KPI aggregates).
	"""
	# ── 1.  Fetch Billet Cutting records ────────────────────────────
	conditions = "bc.docstatus = 1"
	params = {}

	if from_date:
		conditions += " AND bc.posting_date >= %(from_date)s"
		params["from_date"] = from_date
	if to_date:
		conditions += " AND bc.posting_date <= %(to_date)s"
		params["to_date"] = to_date
	if item_code:
		conditions += " AND bc.finish_size = %(item_code)s"
		params["item_code"] = item_code
	if production_plan:
		conditions += " AND bc.production_plan = %(production_plan)s"
		params["production_plan"] = production_plan

	billet_cutting_data = frappe.db.sql(
		f"""
		SELECT
			bc.name              AS billet_cutting_name,
			bc.production_plan,
			bc.posting_date      AS production_date,
			bc.finish_size       AS finished_item,
			bc.billet_length_full AS fg_length,
			bc.billet_size       AS rm,
			bc.billet_weight     AS rm_consumption
		FROM `tabBillet Cutting` bc
		WHERE {conditions}
		ORDER BY bc.posting_date DESC, bc.name DESC
		""",
		params,
		as_dict=True,
	)

	if not billet_cutting_data:
		return {"rows": [], "totals": {"total_production": 0, "rm_consumption": 0}}

	# Collect unique (production_plan, finished_item) pairs for batch lookups
	pp_item_pairs = set()
	pp_names = set()
	for row in billet_cutting_data:
		if row.production_plan and row.finished_item:
			pp_item_pairs.add((row.production_plan, row.finished_item))
			pp_names.add(row.production_plan)

	# ── 2.  Batch-fetch FG Planned Qty from Production Plan Item ───
	planned_qty_map = {}  # key: (production_plan, item_code)
	if pp_names:
		pp_list = list(pp_names)
		planned_rows = frappe.db.sql(
			"""
			SELECT
				ppi.parent   AS production_plan,
				ppi.item_code,
				ppi.planned_qty
			FROM `tabProduction Plan Item` ppi
			WHERE ppi.parent IN %(pp_list)s
			""",
			{"pp_list": pp_list},
			as_dict=True,
		)
		for pr in planned_rows:
			planned_qty_map[(pr.production_plan, pr.item_code)] = flt(pr.planned_qty)

	# ── 3.  Batch-fetch Actual Qty & Burning Loss from Finish Weight
	#         Aggregate per (production_plan, item_code).
	fw_map = {}  # key: (production_plan, item_code) → {actual_qty, burning_loss}
	if pp_names:
		pp_list = list(pp_names)
		fw_rows = frappe.db.sql(
			"""
			SELECT
				fw.production_plan,
				fw.item_code,
				SUM(fw.finish_weight)               AS total_finish_weight,
				AVG(NULLIF(fw.burning_loss_per, 0))  AS avg_burning_loss
			FROM `tabFinish Weight` fw
			WHERE fw.docstatus = 1
			  AND fw.production_plan IN %(pp_list)s
			GROUP BY fw.production_plan, fw.item_code
			""",
			{"pp_list": pp_list},
			as_dict=True,
		)
		for fr in fw_rows:
			fw_map[(fr.production_plan, fr.item_code)] = {
				"actual_qty": flt(fr.total_finish_weight),
				"burning_loss": flt(fr.avg_burning_loss, 2),
			}

	# ── 4.  Assemble final rows ────────────────────────────────────
	rows = []
	total_production = 0
	total_rm_consumption = 0
	# Track unique (production_plan, finished_item) pairs to avoid double-counting planned qty
	planned_qty_tracked = set()

	for row in billet_cutting_data:
		pp = row.production_plan or ""
		fi = row.finished_item or ""

		fg_planned_qty = planned_qty_map.get((pp, fi), 0)
		fw_data = fw_map.get((pp, fi), {})
		actual_qty = fw_data.get("actual_qty", 0)
		burning_loss = fw_data.get("burning_loss", 0)

		# Sum FG Planned Qty only once per (production_plan, finished_item) combination
		if pp and fi and (pp, fi) not in planned_qty_tracked:
			total_production += flt(fg_planned_qty)
			planned_qty_tracked.add((pp, fi))

		total_rm_consumption += flt(row.rm_consumption)

		rows.append({
			"production_plan": pp,
			"production_date": str(row.production_date) if row.production_date else "",
			"finished_item": fi,
			"fg_planned_qty": flt(fg_planned_qty),
			"actual_qty": flt(actual_qty),
			"fg_length": flt(row.fg_length),
			"rm": row.rm or "",
			"rm_consumption": flt(row.rm_consumption),
			"burning_loss": flt(burning_loss, 2),
		})

	return {
		"rows": rows,
		"totals": {
			"total_production": flt(total_production),
			"rm_consumption": flt(total_rm_consumption),
		},
	}


@frappe.whitelist()
def get_bright_production_data(from_date=None, to_date=None, item_code=None, production_plan=None):
	"""
	Fetch Bright Production data for the Production Dashboard.

	Primary source: Bright Bar Production (submitted)
	Cross-referenced with:
	  - Production Plan Item (po_items) → FG Planned Qty

	Returns dict with 'rows' (table data) and 'totals' (KPI aggregates).
	"""
	# ── 1.  Fetch Bright Bar Production records ────────────────────
	conditions = "bbp.docstatus = 1"
	params = {}

	if from_date:
		conditions += " AND bbp.production_date >= %(from_date)s"
		params["from_date"] = from_date
	if to_date:
		conditions += " AND bbp.production_date <= %(to_date)s"
		params["to_date"] = to_date
	if item_code:
		conditions += " AND bbp.finished_good = %(item_code)s"
		params["item_code"] = item_code
	if production_plan:
		conditions += " AND bbp.production_plan = %(production_plan)s"
		params["production_plan"] = production_plan

	bright_data = frappe.db.sql(
		f"""
		SELECT
			bbp.name                AS bright_bar_name,
			bbp.production_plan,
			bbp.production_date,
			bbp.finished_good       AS finished_item,
			bbp.fg_weight           AS actual_qty,
			bbp.finish_length       AS fg_length,
			bbp.raw_material        AS rm,
			bbp.actual_rm_consumption AS rm_consumption,
			bbp.wastage_per         AS wastage
		FROM `tabBright Bar Production` bbp
		WHERE {conditions}
		ORDER BY bbp.production_date DESC, bbp.name DESC
		""",
		params,
		as_dict=True,
	)

	if not bright_data:
		return {"rows": [], "totals": {"total_production": 0, "rm_consumption": 0}}

	# Collect unique production plan names for batch lookup
	pp_names = set()
	pp_item_pairs = set()
	for row in bright_data:
		if row.production_plan:
			pp_names.add(row.production_plan)
			if row.finished_item:
				pp_item_pairs.add((row.production_plan, row.finished_item))

	# ── 2.  Batch-fetch FG Planned Qty from Production Plan Item ───
	planned_qty_map = {}  # key: (production_plan, item_code)
	if pp_names:
		pp_list = list(pp_names)
		planned_rows = frappe.db.sql(
			"""
			SELECT
				ppi.parent   AS production_plan,
				ppi.item_code,
				ppi.planned_qty
			FROM `tabProduction Plan Item` ppi
			WHERE ppi.parent IN %(pp_list)s
			""",
			{"pp_list": pp_list},
			as_dict=True,
		)
		for pr in planned_rows:
			planned_qty_map[(pr.production_plan, pr.item_code)] = flt(pr.planned_qty)

	# ── 3.  Assemble final rows ────────────────────────────────────
	rows = []
	total_production = 0
	total_rm_consumption = 0
	# Track unique (production_plan, finished_item) pairs to avoid double-counting planned qty
	planned_qty_tracked = set()

	for row in bright_data:
		pp = row.production_plan or ""
		fi = row.finished_item or ""

		fg_planned_qty = planned_qty_map.get((pp, fi), 0)

		# Sum FG Planned Qty only once per (production_plan, finished_item) combination
		if pp and fi and (pp, fi) not in planned_qty_tracked:
			total_production += flt(fg_planned_qty)
			planned_qty_tracked.add((pp, fi))

		total_rm_consumption += flt(row.rm_consumption)

		rows.append({
			"production_plan": pp,
			"production_date": str(row.production_date) if row.production_date else "",
			"finished_item": fi,
			"fg_planned_qty": flt(fg_planned_qty),
			"actual_qty": flt(row.actual_qty),
			"fg_length": row.fg_length or "",
			"rm": row.rm or "",
			"rm_consumption": flt(row.rm_consumption),
			"wastage": flt(row.wastage, 2),
		})

	return {
		"rows": rows,
		"totals": {
			"total_production": flt(total_production),
			"rm_consumption": flt(total_rm_consumption),
		},
	}
