# Copyright (c) 2025, Prakash Steel and contributors
# For license information, please see license.txt

import frappe
from datetime import date as _date
from io import BytesIO

import openpyxl
from frappe import _
from frappe.utils import flt
from frappe.utils.xlsxutils import make_xlsx


@frappe.whitelist()
def get_rolled_production_data(
    from_date=None,
    to_date=None,
    item_code=None,
    production_plan=None,
    machine_name=None,
    category_name=None,
):
    """
    Fetch Rolled Production data for the Production Dashboard.

    Primary source: Billet Cutting (submitted)
    Cross-referenced with:
      - Production Plan Item (po_items) → FG Planned Qty
      - Finish Weight → Actual Qty & related FG fields
      - Burning Loss % (KPI) = aggregate formula on dashboard totals (not Finish Weight field)

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
    if category_name:
        cat_items = frappe.db.sql(
            """SELECT name FROM `tabItem` WHERE custom_category_name = %(cat)s""",
            {"cat": category_name},
            as_dict=True,
        )
        cat_item_codes = [r.name for r in cat_items]
        if cat_item_codes:
            conditions += " AND (bc.billet_size IN %(cat_items)s OR bc.finish_size IN %(cat_items)s)"
            params["cat_items"] = cat_item_codes
        else:
            return {"rows": [], "totals": {"total_production": 0, "rm_consumption": 0}}

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
			bc.miss_billet_weight AS miss_billet_weight,
			bc.heat_no            AS heat_no
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

    # ── 3.  Batch-fetch Actual Qty, Length, Melting Weight, Finish Pcs, and Miss Roll/Ingot fields from Finish Weight
    fw_map = {}
    if pp_names:
        pp_list = list(pp_names)
        fw_rows = frappe.db.sql(
            """
			SELECT
				fw.production_plan,
				fw.item_code,
				SUM(fw.finish_weight)               AS total_finish_weight,
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
                "length": fr.length or "",
                "melting_weight": flt(fr.total_melting_weight),
                "finish_pcs": flt(fr.total_finish_pcs),
                "total_miss_roll_pcs": flt(fr.total_miss_roll_pcs),
                "total_miss_roll_weight": flt(fr.total_miss_roll_weight),
                "total_miss_ingot_pcs": flt(fr.total_miss_ingot_pcs),
                "total_miss_ingot_weight": flt(fr.total_miss_ingot_weight),
            }

    # ── 3.a  Compute Total Hr Consumed from Hourly Production (per Billet Cutting) ──
    hours_map = {}
    if billet_cutting_data:
        bc_names = [
            row.billet_cutting_name
            for row in billet_cutting_data
            if row.get("billet_cutting_name")
        ]
        if bc_names:
            hour_rows = frappe.db.sql(
                """
				SELECT
					hp.billet_cutting_id AS billet_cutting_name,
					SUM(TIME_TO_SEC(TIMEDIFF(hp.time_to, hp.time_from))) / 3600.0 AS total_hours
				FROM `tabHourly Production` hp
				WHERE hp.docstatus = 1
				  AND hp.billet_cutting_id IN %(bc_names)s
				GROUP BY hp.billet_cutting_id
				""",
                {"bc_names": tuple(bc_names)},
                as_dict=True,
            )
            for hr in hour_rows:
                hours_map[hr.billet_cutting_name] = flt(hr.total_hours, 2)

    # ── 3.b  Batch-fetch custom_category_name from Item ──────────────
    all_item_codes_rolled = set()
    for row in billet_cutting_data:
        if row.rm:
            all_item_codes_rolled.add(row.rm)
        if row.finished_item:
            all_item_codes_rolled.add(row.finished_item)

    category_map_rolled = {}
    if all_item_codes_rolled:
        item_cat_rows = frappe.db.sql(
            """SELECT name, custom_category_name FROM `tabItem` WHERE name IN %(items)s""",
            {"items": list(all_item_codes_rolled)},
            as_dict=True,
        )
        for ir in item_cat_rows:
            category_map_rolled[ir.name] = ir.custom_category_name or ""

    # ── 4.  Assemble final rows ────────────────────────────────────
    rows = []
    total_production = 0
    total_rm_consumption = 0
    total_hours_overall = 0
    total_melting_weight_overall = 0
    total_miss_billet_weight_overall = 0
    total_miss_roll_weight_overall = 0
    total_miss_ingot_weight_overall = 0

    for row in billet_cutting_data:
        pp = row.production_plan or ""
        fi = row.finished_item or ""

        fg_planned_qty = planned_qty_map.get((pp, fi), 0)
        fw_data = fw_map.get((pp, fi), {})
        actual_qty = fw_data.get("actual_qty", 0)
        melting_weight = fw_data.get("melting_weight", 0)
        finish_pcs = fw_data.get("finish_pcs", 0)
        total_miss_roll_pcs = fw_data.get("total_miss_roll_pcs", 0)
        total_miss_roll_weight = fw_data.get("total_miss_roll_weight", 0)
        total_miss_ingot_pcs = fw_data.get("total_miss_ingot_pcs", 0)
        total_miss_ingot_weight = fw_data.get("total_miss_ingot_weight", 0)
        fg_length = fw_data.get("length", "") or row.fg_length or ""

        rm_c = flt(row.rm_consumption)
        miss_bw = flt(row.miss_billet_weight)
        if rm_c > 0:
            burning_loss = flt(
                ((rm_c + miss_bw - flt(actual_qty) - flt(total_miss_ingot_weight)) / rm_c)
                * 100,
                2,
            )
        else:
            burning_loss = 0.0

        total_production += flt(actual_qty)
        total_rm_consumption += flt(row.rm_consumption)
        total_melting_weight_overall += flt(melting_weight)
        total_miss_billet_weight_overall += flt(row.miss_billet_weight)
        total_miss_roll_weight_overall += flt(total_miss_roll_weight)
        total_miss_ingot_weight_overall += flt(total_miss_ingot_weight)

        total_hr_consumed = hours_map.get(row.billet_cutting_name, 0)
        total_hours_overall += flt(total_hr_consumed)

        rows.append(
            {
                "production_plan": pp,
                "production_date": (
                    str(row.production_date) if row.production_date else ""
                ),
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
                "description_of_cutting_billet": row.description_of_cutting_billet
                or "",
                "total_raw_material_pcs": (
                    flt(row.total_raw_material_pcs) if row.total_raw_material_pcs else 0
                ),
                "miss_billet_pcs": (
                    flt(row.miss_billet_pcs) if row.miss_billet_pcs else 0
                ),
                "miss_billet_weight": (
                    flt(row.miss_billet_weight) if row.miss_billet_weight else 0
                ),
                "heat_no": row.heat_no or "",
                "total_hr_consumed": flt(total_hr_consumed, 2),
                "fg_length": fg_length,
                "rm": row.rm or "",
                "rm_consumption": flt(row.rm_consumption),
                "burning_loss": flt(burning_loss, 2),
                "rm_category_name": category_map_rolled.get(row.rm or "", ""),
                "finished_item_category_name": category_map_rolled.get(fi, ""),
            }
        )

    # Dashboard Burning Loss % = ((RM + Miss Billet - Production - Miss Ingot) / RM) × 100
    burning_loss_per_total = 0.0
    if total_rm_consumption > 0:
        burning_loss_per_total = flt(
            (
                (
                    total_rm_consumption
                    + total_miss_billet_weight_overall
                    - total_production
                    - total_miss_ingot_weight_overall
                )
                / total_rm_consumption
            )
            * 100,
            2,
        )

    return {
        "rows": rows,
        "totals": {
            "total_production": flt(total_production),
            "rm_consumption": flt(total_rm_consumption),
            "total_hr_consumed": flt(total_hours_overall, 2),
            "total_melting_weight": flt(total_melting_weight_overall),
            "total_miss_billet_weight": flt(total_miss_billet_weight_overall),
            "total_miss_roll_weight": flt(total_miss_roll_weight_overall),
            "total_miss_ingot_weight": flt(total_miss_ingot_weight_overall),
            "burning_loss_per": burning_loss_per_total,
        },
    }


@frappe.whitelist()
def get_bright_production_data(
    from_date=None,
    to_date=None,
    item_code=None,
    production_plan=None,
    machine_name=None,
    category_name=None,
):
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
    if machine_name:
        conditions += " AND bbp.machine_name = %(machine_name)s"
        params["machine_name"] = machine_name
    if category_name:
        cat_items = frappe.db.sql(
            """SELECT name FROM `tabItem` WHERE custom_category_name = %(cat)s""",
            {"cat": category_name},
            as_dict=True,
        )
        cat_item_codes = [r.name for r in cat_items]
        if cat_item_codes:
            conditions += " AND (bbp.raw_material IN %(cat_items)s OR bbp.finished_good IN %(cat_items)s)"
            params["cat_items"] = cat_item_codes
        else:
            return {"rows": [], "totals": {"total_production": 0, "rm_consumption": 0}}

    bright_data = frappe.db.sql(
        f"""
		SELECT
			bbp.name                  AS bright_bar_name,
			bbp.production_plan,
			bbp.production_date,
			bbp.finished_good         AS finished_item,
			bbp.fg_weight             AS fg_weight,
			bbp.fg_weight             AS actual_qty,
			bbp.finish_length         AS fg_length,
			bbp.raw_material          AS rm,
			bbp.actual_rm_consumption AS rm_consumption,
			bbp.wastage_per           AS wastage,
			bbp.machine_name          AS machine_name,
			bbp.finish_length         AS finish_length,
			bbp.tolerance             AS tolerance
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
    planned_qty_map = {}
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

    # ── 2.b  Batch-fetch custom_category_name from Item ──────────────
    all_item_codes_bright = set()
    for row in bright_data:
        if row.rm:
            all_item_codes_bright.add(row.rm)
        if row.finished_item:
            all_item_codes_bright.add(row.finished_item)

    category_map_bright = {}
    if all_item_codes_bright:
        item_cat_rows = frappe.db.sql(
            """SELECT name, custom_category_name FROM `tabItem` WHERE name IN %(items)s""",
            {"items": list(all_item_codes_bright)},
            as_dict=True,
        )
        for ir in item_cat_rows:
            category_map_bright[ir.name] = ir.custom_category_name or ""

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
        fg_weight = flt(row.fg_weight)

        total_production += actual_qty
        total_rm_consumption += rm_consumption
        total_fg_weight += fg_weight
        total_rm_for_wastage += rm_consumption

        rows.append(
            {
                "production_plan": pp,
                "production_date": (
                    str(row.production_date) if row.production_date else ""
                ),
                "finished_item": fi,
                "fg_planned_qty": flt(fg_planned_qty),
                "actual_qty": actual_qty,
                "fg_weight": fg_weight,
                "fg_length": row.fg_length or "",
                "rm": row.rm or "",
                "rm_consumption": rm_consumption,
                "wastage": flt(row.wastage, 2),
                "machine_name": row.machine_name or "",
                "finish_length": row.finish_length or "",
                "tolerance": row.tolerance or "",
                "rm_category_name": category_map_bright.get(row.rm or "", ""),
                "finished_item_category_name": category_map_bright.get(fi, ""),
            }
        )

    # Average Wastage % for KPI card
    avg_wastage_per = 0.0
    wastage_values = [
        flt(row.get("wastage", 0))
        for row in bright_data
        if row.get("wastage") is not None
    ]
    if wastage_values:
        avg_wastage_per = sum(wastage_values) / len(wastage_values)

    return {
        "rows": rows,
        "totals": {
            "total_production": flt(total_production),
            "rm_consumption": flt(total_rm_consumption),
            "total_fg_weight": flt(total_fg_weight),
            "wastage_per": flt(avg_wastage_per, 2),
        },
    }


@frappe.whitelist()
def get_bend_weight_details(
    from_date=None,
    to_date=None,
    item_code=None,
    production_plan=None,
    machine_name=None,
    category_name=None,
):
    """
    Fetch Bend Weight Details for the Production Dashboard.

    Source: Finish Weight (submitted)
    """
    conditions = "fw.docstatus = 1"
    params = {}

    if from_date:
        conditions += " AND fw.posting_date >= %(from_date)s"
        params["from_date"] = from_date
    if to_date:
        conditions += " AND fw.posting_date <= %(to_date)s"
        params["to_date"] = to_date
    if item_code:
        conditions += " AND fw.item_code = %(item_code)s"
        params["item_code"] = item_code
    if production_plan:
        conditions += " AND fw.production_plan = %(production_plan)s"
        params["production_plan"] = production_plan
    if category_name:
        cat_items = frappe.db.sql(
            """SELECT name FROM `tabItem` WHERE custom_category_name = %(cat)s""",
            {"cat": category_name},
            as_dict=True,
        )
        cat_item_codes = [r.name for r in cat_items]
        if cat_item_codes:
            conditions += " AND fw.item_code IN %(cat_items)s"
            params["cat_items"] = cat_item_codes
        else:
            return {"rows": [], "totals": {}}

    rows = frappe.db.sql(
        f"""
		SELECT
			fw.name AS finish_weight_id,
			fw.bend_material_weight,
			fw.item_code
		FROM `tabFinish Weight` fw
		WHERE {conditions}
		ORDER BY fw.posting_date DESC, fw.name DESC
		""",
        params,
        as_dict=True,
    )

    all_item_codes_bend = set(r.item_code for r in rows if r.item_code)
    category_map_bend = {}
    if all_item_codes_bend:
        item_cat_rows = frappe.db.sql(
            """SELECT name, custom_category_name FROM `tabItem` WHERE name IN %(items)s""",
            {"items": list(all_item_codes_bend)},
            as_dict=True,
        )
        for ir in item_cat_rows:
            category_map_bend[ir.name] = ir.custom_category_name or ""

    result_rows = []
    for r in rows:
        result_rows.append(
            {
                "bend_material_weight": flt(r.bend_material_weight),
                "item_code": r.item_code,
                "id": r.finish_weight_id,
                "category_name": category_map_bend.get(r.item_code or "", ""),
            }
        )

    return {
        "rows": result_rows,
        "totals": {},
    }


def _fmt_date(date_val):
    """Return a Python date object so Excel treats the cell as a real date."""
    if not date_val:
        return ""
    try:
        if isinstance(date_val, _date):
            return date_val
        parts = str(date_val).split("-")
        if len(parts) == 3:
            return _date(int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        pass
    return str(date_val)


@frappe.whitelist()
def export_production_dashboard(
    tab_id,
    from_date=None,
    to_date=None,
    item_code=None,
    production_plan=None,
    machine_name=None,
    category_name=None,
):
    """
    Build an Excel file (XLSX) for the Production Dashboard tables.
    """
    if tab_id == "rolled_production":
        data = get_rolled_production_data(
            from_date, to_date, item_code, production_plan, machine_name, category_name
        )
        rows = data.get("rows", [])
        header = [
            _("Production Plan"),
            _("Production Date"),
            _("RM"),
            _("RM Category Name"),
            _("Actual RM Consumption"),
            _("Total Billet Pcs"),
            _("Description of Cutting Billet"),
            _("Total Raw Material Pcs"),
            _("Total RM Weight"),
            _("Miss Billet Pcs"),
            _("Miss Billet Weight"),
            _("Heat No"),
            _("Finished Item"),
            _("Finished Item Category Name"),
            _("FG Planned Qty"),
            _("Actual Qty"),
            _("Finish Pcs"),
            _("FG Length"),
            _("Total Miss Roll (Pcs)"),
            _("Total Miss Roll Weight"),
            _("Total Miss Ingot"),
            _("Total Miss Ingot / Billet Weight"),
            _("Melting Weight"),
            _("Burning Loss %"),
            _("Total Hr Consumed"),
        ]

        def map_row(r):
            return [
                r.get("production_plan") or "",
                _fmt_date(r.get("production_date")),
                r.get("rm") or "",
                r.get("rm_category_name") or "",
                flt(r.get("rm_consumption")) or 0,
                flt(r.get("billet_pcs")) or 0,
                r.get("description_of_cutting_billet") or "",
                flt(r.get("total_raw_material_pcs")) or 0,
                (flt(r.get("rm_consumption")) or 0)
                + (flt(r.get("miss_billet_weight")) or 0),
                flt(r.get("miss_billet_pcs")) or 0,
                flt(r.get("miss_billet_weight")) or 0,
                r.get("heat_no") or "",
                r.get("finished_item") or "",
                r.get("finished_item_category_name") or "",
                flt(r.get("fg_planned_qty")) or 0,
                flt(r.get("actual_qty")) or 0,
                flt(r.get("finish_pcs")) or 0,
                r.get("fg_length") or "",
                flt(r.get("total_miss_roll_pcs")) or 0,
                flt(r.get("total_miss_roll_weight")) or 0,
                flt(r.get("total_miss_ingot_pcs")) or 0,
                flt(r.get("total_miss_ingot_weight")) or 0,
                flt(r.get("melting_weight")) or 0,
                flt(r.get("burning_loss")) or 0,
                flt(r.get("total_hr_consumed")) or 0,
            ]

    elif tab_id == "bright_production":
        data = get_bright_production_data(
            from_date, to_date, item_code, production_plan, machine_name, category_name
        )
        rows = data.get("rows", [])
        header = [
            _("Production Plan"),
            _("Production Date"),
            _("RM"),
            _("RM Category Name"),
            _("Actual RM Consumption"),
            _("Machine Name"),
            _("Finished Item"),
            _("Finished Item Category Name"),
            _("FG Planned Qty"),
            _("Actual Qty"),
            _("Melting Weight"),
            _("Finish Length"),
            _("Tolerance"),
            _("Wastage %"),
        ]

        def map_row(r):
            return [
                r.get("production_plan") or "",
                _fmt_date(r.get("production_date")),
                r.get("rm") or "",
                r.get("rm_category_name") or "",
                flt(r.get("rm_consumption")) or 0,
                r.get("machine_name") or "",
                r.get("finished_item") or "",
                r.get("finished_item_category_name") or "",
                flt(r.get("fg_planned_qty")) or 0,
                flt(r.get("actual_qty")) or 0,
                flt(r.get("fg_weight")) or 0,
                r.get("finish_length") or "",
                r.get("tolerance") or "",
                flt(r.get("wastage")) or 0,
            ]

    elif tab_id == "bend_weight_details":
        data = get_bend_weight_details(from_date, to_date, item_code, production_plan, category_name=category_name)
        rows = data.get("rows", [])
        header = [
            _("ID"),
            _("Item Code"),
            _("Category Name"),
            _("Bend Material Weight"),
        ]

        def map_row(r):
            return [
                r.get("id") or r.get("name") or "",
                r.get("item_code") or "",
                r.get("category_name") or "",
                flt(r.get("bend_material_weight")) or 0,
            ]

    else:
        frappe.throw(_("Invalid tab selected for export."))

    data_rows = [map_row(r) for r in rows]
    table_data = [header] + data_rows

    file_name = f"{tab_id}_export.xlsx"
    xlsx_file = make_xlsx(table_data, _("Production Dashboard"))

    # Post-process: apply DD-MM-YYYY number format to the Production Date column
    # (column 2 in Excel, 1-indexed) for tabs that have a date field
    if tab_id in ("rolled_production", "bright_production"):
        wb = openpyxl.load_workbook(BytesIO(xlsx_file.getvalue()))
        ws = wb.active
        for row in ws.iter_rows(min_row=2, min_col=2, max_col=2):
            for cell in row:
                if cell.value:
                    cell.number_format = "DD-MM-YYYY"
        out = BytesIO()
        wb.save(out)
        out.seek(0)
        xlsx_file = out

    frappe.response["filename"] = file_name
    frappe.response["filecontent"] = xlsx_file.getvalue()
    frappe.response["type"] = "binary"
    frappe.response["content_type"] = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
