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
			bc.billet_weight     AS rm_consumption,
			bc.billet_pcs_full   AS billet_pcs,
			bc.description_of_cutting_billet AS description_of_cutting_billet,
			bc.total_raw_material_pcs AS total_raw_material_pcs,
			bc.miss_billet_pcs   AS miss_billet_pcs,
			bc.miss_billet_weight AS miss_billet_weight
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

	# ── 3.  Batch-fetch Actual Qty, Burning Loss, Length, Melting Weight, Finish Pcs, and Miss Roll/Ingot fields from Finish Weight
	#         Aggregate per (production_plan, item_code) for row-level data.
	fw_map = {}  # key: (production_plan, item_code) → {actual_qty, burning_loss, length, melting_weight, finish_pcs, miss_roll_pcs, miss_roll_weight, miss_ingot_pcs, miss_ingot_weight}
	if pp_names:
		pp_list = list(pp_names)
		# Get aggregated data (actual_qty and burning_loss) along with length, melting_weight, finish_pcs, and miss roll/ingot fields
		fw_rows = frappe.db.sql(
			"""
			SELECT
				fw.production_plan,
				fw.item_code,
				SUM(fw.finish_weight)               AS total_finish_weight,
				AVG(NULLIF(fw.burning_loss_per, 0))  AS avg_burning_loss,
				SUM(fw.melting_weight)              AS total_melting_weight,
				SUM(fw.finish_pcs)                 AS total_finish_pcs,
				SUM(fw.total_miss_roll_pcs)        AS total_miss_roll_pcs,
				SUM(fw.total_miss_roll_weight)     AS total_miss_roll_weight,
				SUM(fw.total_miss_ingot_pcs)       AS total_miss_ingot_pcs,
				SUM(fw.total_miss_ingot_weight)    AS total_miss_ingot_weight,
				(SELECT fw2.length
				 FROM `tabFinish Weight` fw2
				 WHERE fw2.docstatus = 1
				   AND fw2.production_plan = fw.production_plan
				   AND fw2.item_code = fw.item_code
				   AND fw2.length IS NOT NULL
				   AND fw2.length != ''
				 ORDER BY fw2.creation DESC
				 LIMIT 1) AS length
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
				"length": fr.length or "",
				"melting_weight": flt(fr.total_melting_weight),
				"finish_pcs": flt(fr.total_finish_pcs),
				"total_miss_roll_pcs": flt(fr.total_miss_roll_pcs),
				"total_miss_roll_weight": flt(fr.total_miss_roll_weight),
				"total_miss_ingot_pcs": flt(fr.total_miss_ingot_pcs),
				"total_miss_ingot_weight": flt(fr.total_miss_ingot_weight),
			}

	# ── 3.a  Compute average Burning Loss % from Finish Weight records ──
	# Calculate the average of burning_loss_per values from all Finish Weight
	# records that match the current filters (date, item, production plan).
	avg_burning_loss_per = 0.0
	if pp_names:
		conditions_fw = ["fw.docstatus = 1", "fw.production_plan IN %(pp_list)s"]
		params_fw = {"pp_list": list(pp_names)}

		if from_date:
			# Use posting_date on Finish Weight to align with the date filters.
			conditions_fw.append("fw.posting_date >= %(from_date)s")
			params_fw["from_date"] = from_date
		if to_date:
			conditions_fw.append("fw.posting_date <= %(to_date)s")
			params_fw["to_date"] = to_date
		if item_code:
			conditions_fw.append("fw.item_code = %(item_code)s")
			params_fw["item_code"] = item_code
		if production_plan:
			conditions_fw.append("fw.production_plan = %(production_plan)s")
			params_fw["production_plan"] = production_plan

		fw_avg_rows = frappe.db.sql(
			f"""
			SELECT
				AVG(NULLIF(fw.burning_loss_per, 0)) AS avg_burning_loss
			FROM `tabFinish Weight` fw
			WHERE {" AND ".join(conditions_fw)}
			""",
			params_fw,
			as_dict=True,
		)

		if fw_avg_rows and fw_avg_rows[0].get("avg_burning_loss") is not None:
			avg_burning_loss_per = flt(fw_avg_rows[0].get("avg_burning_loss"), 2)

	# ── 4.  Assemble final rows ────────────────────────────────────
	rows = []
	total_production = 0
	total_rm_consumption = 0

	for row in billet_cutting_data:
		pp = row.production_plan or ""
		fi = row.finished_item or ""

		fg_planned_qty = planned_qty_map.get((pp, fi), 0)
		fw_data = fw_map.get((pp, fi), {})
		actual_qty = fw_data.get("actual_qty", 0)
		burning_loss = fw_data.get("burning_loss", 0)
		melting_weight = fw_data.get("melting_weight", 0)
		finish_pcs = fw_data.get("finish_pcs", 0)
		total_miss_roll_pcs = fw_data.get("total_miss_roll_pcs", 0)
		total_miss_roll_weight = fw_data.get("total_miss_roll_weight", 0)
		total_miss_ingot_pcs = fw_data.get("total_miss_ingot_pcs", 0)
		total_miss_ingot_weight = fw_data.get("total_miss_ingot_weight", 0)
		# Fetch length from Finish Weight, fallback to billet_length_full if not found
		fg_length = fw_data.get("length", "") or row.fg_length or ""

		# Sum Actual Qty (from Finish Weight) for Total Production
		total_production += flt(actual_qty)

		total_rm_consumption += flt(row.rm_consumption)

		rows.append({
			"production_plan": pp,
			"production_date": str(row.production_date) if row.production_date else "",
			"finished_item": fi,
			"fg_planned_qty": flt(fg_planned_qty),
			"actual_qty": flt(actual_qty),
			"melting_weight": flt(melting_weight),
			"finish_pcs": flt(finish_pcs),
			"total_miss_roll_pcs": flt(total_miss_roll_pcs),
			"total_miss_roll_weight": flt(total_miss_roll_weight),
			"total_miss_ingot_pcs": flt(total_miss_ingot_pcs),
			"total_miss_ingot_weight": flt(total_miss_ingot_weight),
			"billet_pcs": flt(row.billet_pcs) if row.billet_pcs else 0,
			"description_of_cutting_billet": row.description_of_cutting_billet or "",
			"total_raw_material_pcs": flt(row.total_raw_material_pcs) if row.total_raw_material_pcs else 0,
			"miss_billet_pcs": flt(row.miss_billet_pcs) if row.miss_billet_pcs else 0,
			"miss_billet_weight": flt(row.miss_billet_weight) if row.miss_billet_weight else 0,
			"fg_length": fg_length,
			"rm": row.rm or "",
			"rm_consumption": flt(row.rm_consumption),
			"burning_loss": flt(burning_loss, 2),
		})

	return {
		"rows": rows,
		"totals": {
			"total_production": flt(total_production),
			"rm_consumption": flt(total_rm_consumption),
			# Average Burning Loss % from all Finish Weight records that match
			# the current filters (date, item, production plan).
			"burning_loss_per": flt(avg_burning_loss_per, 2),
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
	total_fg_weight = 0.0
	total_rm_for_wastage = 0.0

	for row in bright_data:
		pp = row.production_plan or ""
		fi = row.finished_item or ""

		fg_planned_qty = planned_qty_map.get((pp, fi), 0)

		rm_consumption = flt(row.rm_consumption)
		actual_qty = flt(row.actual_qty)

		# Sum Actual Qty (fg_weight from Bright Bar Production) for Total Production
		total_production += actual_qty

		total_rm_consumption += rm_consumption
		# For correct overall wastage %, aggregate via quantities rather than
		# simply averaging the per-row percentage:
		#   wastage_per (per row) = |(fg_weight / actual_rm) * 100 - 100|
		# In the normal case fg_weight <= actual_rm, this is:
		#   (actual_rm - fg_weight) / actual_rm * 100
		# So overall wastage % is:
		#   (Σ(actual_rm - fg_weight) / Σ(actual_rm)) * 100
		total_fg_weight += actual_qty
		total_rm_for_wastage += rm_consumption

		rows.append({
			"production_plan": pp,
			"production_date": str(row.production_date) if row.production_date else "",
			"finished_item": fi,
			"fg_planned_qty": flt(fg_planned_qty),
			"actual_qty": actual_qty,
			"fg_length": row.fg_length or "",
			"rm": row.rm or "",
			"rm_consumption": rm_consumption,
			"wastage": flt(row.wastage, 2),
		})

	# Average Wastage % for KPI card - calculate average of wastage_per from rows
	avg_wastage_per = 0.0
	wastage_values = [flt(row.get("wastage", 0)) for row in bright_data if row.get("wastage") is not None]
	if wastage_values:
		avg_wastage_per = sum(wastage_values) / len(wastage_values)

	return {
		"rows": rows,
		"totals": {
			"total_production": flt(total_production),
			"rm_consumption": flt(total_rm_consumption),
			# Average Wastage % from all Bright Bar Production rows that
			# match the current filters (date, item, production plan).
			"wastage_per": flt(avg_wastage_per, 2),
		},
	}
