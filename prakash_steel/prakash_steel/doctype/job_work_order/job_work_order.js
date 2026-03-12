// Copyright (c) 2026, Beetashoke Chakraborty and contributors
// For license information, please see license.txt

frappe.ui.form.on("JOB Work Item table", {
	fg_item: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (!row.fg_item) return;

		// Clear dependent fields first
		frappe.model.set_value(cdt, cdn, "default_bom", null);
		frappe.model.set_value(cdt, cdn, "raw_material", null);
		frappe.model.set_value(cdt, cdn, "rm_qty_required", 0);

		frappe.call({
			method: "prakash_steel.utils.lead_time.get_default_bom",
			args: { item_code: row.fg_item },
			callback: function (r) {
				if (!r.message) return;

				frappe.model.set_value(cdt, cdn, "default_bom", r.message);

				// Fetch BOM details (raw material + qty ratios)
				frappe.call({
					method: "prakash_steel.utils.lead_time.get_bom_details",
					args: { bom_name: r.message },
					callback: function (res) {
						if (!res.message) return;

						frappe.model.set_value(cdt, cdn, "raw_material", res.message.raw_material);

						// Recalculate if qty already entered
						let current_row = locals[cdt][cdn];
						if (current_row.fg_production_qty) {
							_calc_rm_qty(cdt, cdn, current_row.fg_production_qty, res.message);
						}
					},
				});
			},
		});
	},

	fg_production_qty: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (!row.default_bom || !row.fg_production_qty) return;

		frappe.call({
			method: "prakash_steel.utils.lead_time.get_bom_details",
			args: { bom_name: row.default_bom },
			callback: function (r) {
				if (!r.message) return;
				_calc_rm_qty(cdt, cdn, row.fg_production_qty, r.message);
			},
		});
	},
});

function _calc_rm_qty(cdt, cdn, fg_production_qty, bom_details) {
	let bom_fg_qty = bom_details.bom_fg_qty;
	let bom_rm_qty = bom_details.bom_rm_qty;

	if (!bom_fg_qty) return;

	let rm_qty = flt((fg_production_qty / bom_fg_qty) * bom_rm_qty, 3);
	frappe.model.set_value(cdt, cdn, "rm_qty_required", rm_qty);
}
