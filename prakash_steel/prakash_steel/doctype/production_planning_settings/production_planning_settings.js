// Copyright (c) 2026, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.ui.form.on("Production planning settings", {
	refresh(frm) {
		// Ensure only one checkbox is selected on refresh
		ensure_single_checkbox_selection(frm);
	},

	from_work_order(frm) {
		// If from_work_order is checked, uncheck from_production_plan
		if (frm.doc.from_work_order) {
			frm.set_value("from_production_plan", 0);
		}
	},

	from_production_plan(frm) {
		// If from_production_plan is checked, uncheck from_work_order
		if (frm.doc.from_production_plan) {
			frm.set_value("from_work_order", 0);
		}
	}
});

function ensure_single_checkbox_selection(frm) {
	// If both are checked, keep the last modified one
	// This handles edge cases where both might be checked
	if (frm.doc.from_work_order && frm.doc.from_production_plan) {
		// Default to unchecking from_production_plan if both are checked
		frm.set_value("from_production_plan", 0);
	}
}
