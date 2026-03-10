// // Copyright (c) 2025, Prakash Steel and contributors
// // For license information, please see license.txt

// // NOTE:
// // This script adds simple, reliable totals for the Payment Reconciliation
// // doctype, including a button-based way to calculate totals of ONLY the
// // selected rows in each child table.

// frappe.ui.form.on("Payment Reconciliation", {
// 	refresh(frm) {
// 		// Always recompute base totals for all rows
// 		update_invoice_totals(frm, null);
// 		update_payment_totals(frm, null);

// 		// Add buttons so user can explicitly calculate selected-row totals
// 		add_totals_buttons(frm);
// 	},
// });

// // ---------------------------------------------------------------------------
// // Buttons
// // ---------------------------------------------------------------------------

// function add_totals_buttons(frm) {
// 	// Avoid adding duplicate buttons on multiple refreshes
// 	if (!frm.custom_totals_buttons_added) {
// 		frm.custom_totals_buttons_added = true;

// 		// Group under "Totals" for cleanliness
// 		frm.add_custom_button(
// 			__("Selected Invoice Total"),
// 			() => {
// 				update_invoice_totals(frm, get_selected_total(frm, "invoices", "outstanding_amount"));
// 			},
// 			__("Totals")
// 		);

// 		frm.add_custom_button(
// 			__("Selected Payment Total"),
// 			() => {
// 				update_payment_totals(frm, get_selected_total(frm, "payments", "amount"));
// 			},
// 			__("Totals")
// 		);
// 	}
// }

// // ---------------------------------------------------------------------------
// // Core helpers
// // ---------------------------------------------------------------------------

// /**
//  * Get total of a given numeric field for ONLY the selected rows of a child table.
//  */
// function get_selected_total(frm, table_fieldname, amount_fieldname) {
// 	let total = 0;
// 	let currency = "";

// 	const grid = frm.fields_dict[table_fieldname]?.grid;
// 	if (!grid) {
// 		return { total, currency };
// 	}

// 	// Use standard Frappe API – the checkboxes in the first column
// 	// drive the “selected children” list.
// 	let selected_rows = [];
// 	if (typeof grid.get_selected_children === "function") {
// 		selected_rows = grid.get_selected_children() || [];
// 	}

// 	selected_rows.forEach((row) => {
// 		total += flt(row[amount_fieldname]) || 0;
// 		if (!currency && row.currency) {
// 			currency = row.currency;
// 		}
// 	});

// 	return { total, currency };
// }

// /**
//  * Compute and render totals for the Invoices table.
//  * If selected_info is provided, its .total is used for the "Selected" side;
//  * otherwise the selected total is treated as 0.
//  */
// function update_invoice_totals(frm, selected_info) {
// 	let total_all = 0;
// 	let currency = "";

// 	(frm.doc.invoices || []).forEach((row) => {
// 		const amount = flt(row.outstanding_amount) || 0;
// 		total_all += amount;
// 		if (!currency && row.currency) {
// 			currency = row.currency;
// 		}
// 	});

// 	const selected_total = selected_info ? selected_info.total : 0;
// 	const selected_currency = selected_info && selected_info.currency ? selected_info.currency : currency;

// 	render_table_totals(
// 		frm,
// 		"invoices",
// 		selected_total,
// 		total_all,
// 		selected_currency || currency,
// 		__("Outstanding Amount")
// 	);
// }

// /**
//  * Compute and render totals for the Payments table.
//  */
// function update_payment_totals(frm, selected_info) {
// 	let total_all = 0;
// 	let currency = "";

// 	(frm.doc.payments || []).forEach((row) => {
// 		const amount = flt(row.amount) || 0;
// 		total_all += amount;
// 		if (!currency && row.currency) {
// 			currency = row.currency;
// 		}
// 	});

// 	const selected_total = selected_info ? selected_info.total : 0;
// 	const selected_currency = selected_info && selected_info.currency ? selected_info.currency : currency;

// 	render_table_totals(
// 		frm,
// 		"payments",
// 		selected_total,
// 		total_all,
// 		selected_currency || currency,
// 		__("Payment Amount")
// 	);
// }

// /**
//  * Render totals block below a child table –
//  * left = selected rows, right = all rows.
//  */
// function render_table_totals(frm, table_fieldname, selected_total, all_total, currency, base_label) {
// 	const field = frm.fields_dict[table_fieldname];
// 	if (!field || !field.wrapper) return;

// 	const $wrapper = $(field.wrapper);

// 	// Remove previous totals block if present
// 	const total_wrapper_id = `${table_fieldname}_totals_wrapper`;
// 	$wrapper.find(`#${total_wrapper_id}`).remove();

// 	// Format amounts
// 	const formatted_selected = format_currency_safe(selected_total, currency);
// 	const formatted_all = format_currency_safe(all_total, currency);

// 	const html = `
// 		<div id="${total_wrapper_id}"
// 		     style="margin-top: 10px; padding: 10px; background-color: #f8f9fa;
// 		            border-top: 2px solid #dee2e6; display: flex;
// 		            justify-content: space-between; align-items: center;">
// 			<div style="text-align: left;">
// 				<strong style="font-size: 13px; color: #0066cc;">
// 					${__("Selected")} ${base_label}:
// 				</strong>
// 				<span style="font-size: 14px; font-weight: bold; color: #ff6b35;">
// 					${formatted_selected}
// 				</span>
// 			</div>
// 			<div style="text-align: right;">
// 				<strong style="font-size: 13px; color: #0066cc;">
// 					${__("All")} ${base_label}:
// 				</strong>
// 				<span style="font-size: 14px; font-weight: bold; color: #28a745;">
// 					${formatted_all}
// 				</span>
// 			</div>
// 		</div>
// 	`;

// 	$wrapper.append(html);
// }

// /**
//  * Safe currency formatter using Frappe's formatter.
//  */
// function format_currency_safe(amount, currency) {
// 	return frappe.format(amount || 0, {
// 		fieldtype: "Currency",
// 		options: currency || undefined,
// 	});
// }








