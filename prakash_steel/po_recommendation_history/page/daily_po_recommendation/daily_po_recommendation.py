import frappe
from frappe import _

SKU_COMBO = {
	"PTA":   {"purchase": 1, "sell": 0, "buffer_flag": 1},
	"BOTA":  {"purchase": 1, "sell": 0, "buffer_flag": 1},
	"TRMTA": {"purchase": 1, "sell": 0, "buffer_flag": 1},
	"PTO":   {"purchase": 1, "sell": 0, "buffer_flag": 0},
	"BOTO":  {"purchase": 1, "sell": 0, "buffer_flag": 0},
	"TRMTO": {"purchase": 1, "sell": 0, "buffer_flag": 0},
	"BBMTA": {"purchase": 0, "sell": 1, "buffer_flag": 1},
	"RBMTA": {"purchase": 0, "sell": 1, "buffer_flag": 1},
	"BBMTO": {"purchase": 0, "sell": 1, "buffer_flag": 0},
	"RBMTO": {"purchase": 0, "sell": 1, "buffer_flag": 0},
}

BUFFER_SKUS = {"PTA", "BOTA", "TRMTA", "BBMTA", "RBMTA"}


def get_columns(sku_type):
	is_buffer = sku_type in BUFFER_SKUS
	cols = [
		{"label": _("Snapshot Time"),  "fieldname": "snapshot_time",  "fieldtype": "Data",  "width": 100},
		{"label": _("Item Code"),       "fieldname": "item_code",       "fieldtype": "Link",  "options": "Item", "width": 160},
	]

	if is_buffer:
		cols += [
			{"label": _("TOG"),              "fieldname": "tog",              "fieldtype": "Float", "width": 80},
			{"label": _("TOY"),              "fieldname": "toy",              "fieldtype": "Float", "width": 80},
			{"label": _("TOR"),              "fieldname": "tor",              "fieldtype": "Float", "width": 80},
			{"label": _("Qualified Demand"), "fieldname": "qualified_demand", "fieldtype": "Float", "width": 130},
			{"label": _("Additional Demand"),"fieldname": "additional_demand","fieldtype": "Float", "width": 140},
		]
	else:
		cols += [
			{"label": _("Requirement"),        "fieldname": "requirement",        "fieldtype": "Float", "width": 110},
			{"label": _("Total SO"),           "fieldname": "total_so",           "fieldtype": "Float", "width": 100},
			{"label": _("Open SO (Qualified)"),"fieldname": "open_so_qualified",  "fieldtype": "Float", "width": 140},
		]

	cols += [
		{"label": _("On Hand Stock"),           "fieldname": "on_hand_stock",           "fieldtype": "Float", "width": 120},
		{"label": _("WIP"),                     "fieldname": "wip",                     "fieldtype": "Float", "width": 80},
		{"label": _("Open PO"),                 "fieldname": "open_po",                 "fieldtype": "Float", "width": 100},
		{"label": _("Open Subcon PO"),          "fieldname": "open_subcon_po",          "fieldtype": "Float", "width": 130},
		{"label": _("Net Flow"),                "fieldname": "net_flow",                "fieldtype": "Float", "width": 100},
	]

	if is_buffer:
		cols += [
			{"label": _("On Hand Status"),  "fieldname": "on_hand_status", "fieldtype": "Data", "width": 120},
			{"label": _("On Hand Colour"),  "fieldname": "on_hand_colour", "fieldtype": "Data", "width": 120},
		]

	cols += [
		{"label": _("Order Recommendation"),    "fieldname": "order_recommendation",    "fieldtype": "Float", "width": 170},
		{"label": _("MRQ"),                     "fieldname": "mrq",                     "fieldtype": "Float", "width": 80},
		{"label": _("Balance Order Rec"),       "fieldname": "balance_order_recommendation", "fieldtype": "Float", "width": 150},
		{"label": _("Net Order Recommendation"),"fieldname": "net_order_recommendation","fieldtype": "Float", "width": 180},
		{"label": _("MOQ"),                     "fieldname": "moq",                     "fieldtype": "Float", "width": 80},
		{"label": _("Order Multiple Qty"),      "fieldname": "batch_size",              "fieldtype": "Float", "width": 130},
	]

	if is_buffer:
		cols += [
			{"label": _("Prod Qty (Child Stock)"),           "fieldname": "production_qty_based_on_child_stock",                 "fieldtype": "Float", "width": 170},
			{"label": _("Child Full Kit Status"),            "fieldname": "child_full_kit_status",                               "fieldtype": "Data",  "width": 150},
			{"label": _("Prod Qty (Child Stock+WIP+PO)"),   "fieldname": "production_qty_based_on_child_stock_wip_open_po",     "fieldtype": "Float", "width": 200},
			{"label": _("Child WIP+PO Full Kit Status"),    "fieldname": "child_wip_open_po_full_kit_status",                   "fieldtype": "Data",  "width": 180},
			{"label": _("Child Item Code"),                 "fieldname": "child_item_code",                                     "fieldtype": "Link",  "options": "Item", "width": 150},
			{"label": _("Child Item Type"),                 "fieldname": "child_item_type",                                     "fieldtype": "Data",  "width": 120},
			{"label": _("Child SKU Type"),                  "fieldname": "child_sku_type",                                      "fieldtype": "Data",  "width": 110},
			{"label": _("Child Requirement"),               "fieldname": "child_requirement",                                   "fieldtype": "Float", "width": 130},
			{"label": _("Child Stock"),                     "fieldname": "child_stock",                                         "fieldtype": "Float", "width": 100},
			{"label": _("Child Stock Soft Alloc"),          "fieldname": "child_stock_soft_allocation_qty",                     "fieldtype": "Float", "width": 150},
			{"label": _("Child Stock Shortage"),            "fieldname": "child_stock_shortage",                                "fieldtype": "Float", "width": 140},
			{"label": _("Child WIP+Open PO"),               "fieldname": "child_wip_open_po",                                   "fieldtype": "Float", "width": 130},
			{"label": _("Child WIP+PO Soft Alloc"),         "fieldname": "child_wip_open_po_soft_allocation_qty",               "fieldtype": "Float", "width": 160},
			{"label": _("Child WIP+PO Shortage"),           "fieldname": "child_wip_open_po_shortage",                          "fieldtype": "Float", "width": 150},
		]

	return cols


def _get_latest_snapshot(snapshot_date, purchase, sell, buffer_flag):
	results = frappe.get_all(
		"PO Recommendation Snapshot",
		filters={
			"snapshot_date": snapshot_date,
			"purchase": purchase,
			"sell": sell,
			"buffer_flag": buffer_flag,
			"status": "Success",
			"sku_type_filter": "",
			"item_code_filter": "",
		},
		fields=["name", "snapshot_time"],
		order_by="snapshot_time desc",
		limit=1,
	)
	return results[0] if results else None


@frappe.whitelist()
def get_sku_data(sku_type, snapshot_date, item_code=None):
	combo = SKU_COMBO.get(sku_type)
	if not combo:
		frappe.throw(_(f"Unknown SKU type: {sku_type}"))

	columns = get_columns(sku_type)
	snap = _get_latest_snapshot(snapshot_date, combo["purchase"], combo["sell"], combo["buffer_flag"])
	if not snap:
		return {"columns": columns, "data": []}

	is_buffer = sku_type in BUFFER_SKUS

	item_filters = {"parent": snap.name, "sku_type": sku_type}
	if item_code:
		item_filters["item_code"] = item_code

	base_fields = [
		"item_code", "requirement", "tog", "toy", "tor",
		"open_so", "total_so", "open_so_qualified",
		"on_hand_stock", "wip", "open_po", "open_subcon_po",
		"qualified_demand", "additional_demand", "net_flow",
		"on_hand_status", "on_hand_colour",
		"order_recommendation", "mrq",
		"balance_order_recommendation", "net_order_recommendation",
		"moq", "batch_size",
	]

	buffer_extra_fields = [
		"production_qty_based_on_child_stock",
		"child_full_kit_status",
		"production_qty_based_on_child_stock_wip_open_po",
		"child_wip_open_po_full_kit_status",
		"child_item_code", "child_item_type", "child_sku_type",
		"child_requirement", "child_stock",
		"child_stock_soft_allocation_qty", "child_stock_shortage",
		"child_wip_open_po", "child_wip_open_po_soft_allocation_qty",
		"child_wip_open_po_shortage",
	]

	fields = base_fields + (buffer_extra_fields if is_buffer else [])

	rows = frappe.get_all(
		"PO Recommendation Snapshot Item",
		filters=item_filters,
		fields=fields,
		order_by="item_code asc",
	)

	snap_time = str(snap.snapshot_time)[:8] if snap.snapshot_time else ""
	data = []
	for row in rows:
		row = dict(row)
		row["snapshot_time"] = snap_time
		data.append(row)

	return {"columns": columns, "data": data}


@frappe.whitelist()
def export_sku_xlsx(sku_type, snapshot_date, item_code=None):
	import base64
	from frappe.utils.xlsxutils import make_xlsx

	result = get_sku_data(sku_type, snapshot_date, item_code)
	columns = result["columns"]
	data = result["data"]

	# Header row + data rows
	rows = [[col["label"] for col in columns]]
	for row in data:
		rows.append([row.get(col["fieldname"], "") for col in columns])

	xlsx_file = make_xlsx(rows, sku_type)
	return {
		"filename": f"{sku_type}_Snapshot_{snapshot_date}.xlsx",
		"content": base64.b64encode(xlsx_file.getvalue()).decode("utf-8"),
	}
