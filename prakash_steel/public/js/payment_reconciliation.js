// Copyright (c) 2025, Prakash Steel and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Reconciliation', {
	refresh: function(frm) {
		// Update visibility of custom_supplier_invoice_no on refresh
		update_supplier_invoice_no_visibility(frm);
		
		// Update totals on refresh (with delay to ensure tables are rendered)
		setTimeout(() => {
			update_invoice_total(frm);
			update_payment_total(frm);
		}, 300);
	}
});

frappe.ui.form.on('Payment Reconciliation Invoice', {
	invoice_type: function(frm, cdt, cdn) {
		// Update visibility when invoice_type changes
		update_row_supplier_invoice_no_visibility(frm, cdt, cdn);
		setTimeout(() => update_invoice_total(frm), 100);
	},
	
	outstanding_amount: function(frm, cdt, cdn) {
		// Update total when outstanding_amount changes
		setTimeout(() => update_invoice_total(frm), 100);
	},
	
	invoices_add: function(frm, cdt, cdn) {
		// Update visibility when a new row is added
		update_row_supplier_invoice_no_visibility(frm, cdt, cdn);
		setTimeout(() => update_invoice_total(frm), 100);
	},
	
	invoices_remove: function(frm, cdt, cdn) {
		// Update total when a row is removed
		setTimeout(() => update_invoice_total(frm), 100);
	},
	
	invoices_refresh: function(frm) {
		// Update visibility for all rows when table is refreshed
		update_supplier_invoice_no_visibility(frm);
		setTimeout(() => {
			update_invoice_total(frm);
		}, 200);
	}
});

frappe.ui.form.on('Payment Reconciliation Payment', {
	amount: function(frm, cdt, cdn) {
		// Update total when amount changes
		setTimeout(() => update_payment_total(frm), 100);
	},
	
	payments_add: function(frm, cdt, cdn) {
		// Update total when a new row is added
		setTimeout(() => update_payment_total(frm), 100);
	},
	
	payments_remove: function(frm, cdt, cdn) {
		// Update total when a row is removed
		setTimeout(() => update_payment_total(frm), 100);
	},
	
	payments_refresh: function(frm) {
		// Update total when table is refreshed
		setTimeout(() => {
			update_payment_total(frm);
		}, 200);
	}
});

function update_supplier_invoice_no_visibility(frm) {
	// Update visibility for all rows in the invoices table
	if (frm.doc.invoices) {
		frm.doc.invoices.forEach(function(row) {
			update_row_supplier_invoice_no_visibility(frm, 'Payment Reconciliation Invoice', row.name);
		});
	}
}

function update_row_supplier_invoice_no_visibility(frm, cdt, cdn) {
	// Get the child row
	let row = locals[cdt][cdn];
	
	if (!row || !frm.fields_dict.invoices || !frm.fields_dict.invoices.grid) return;
	
	// Show/hide custom_supplier_invoice_no based on invoice_type
	if (row.invoice_type === 'Purchase Invoice') {
		frm.fields_dict.invoices.grid.toggle_display('custom_supplier_invoice_no', true, cdn);
	} else {
		frm.fields_dict.invoices.grid.toggle_display('custom_supplier_invoice_no', false, cdn);
		// Clear the value if not Purchase Invoice
		if (row.custom_supplier_invoice_no) {
			frappe.model.set_value(cdt, cdn, 'custom_supplier_invoice_no', '');
		}
	}
}

function calculate_selected_invoice_total(frm) {
	// Calculate total outstanding amount from selected invoices
	let total_selected = 0;
	let total_all = 0;
	let currency = '';
	
	if (frm.doc.invoices && frm.doc.invoices.length > 0) {
		// Get selected row names by checking checkboxes in DOM
		let selected_row_names = [];
		if (frm.fields_dict.invoices && frm.fields_dict.invoices.grid) {
			let grid = frm.fields_dict.invoices.grid;
			let $wrapper = $(grid.wrapper);
			
			// Find all checked checkboxes in the invoices grid
			$wrapper.find('input[type="checkbox"]:checked').each(function() {
				let $checkbox = $(this);
				let $row = $checkbox.closest('[data-name]');
				if ($row.length) {
					let row_name = $row.attr('data-name');
					if (row_name && selected_row_names.indexOf(row_name) === -1) {
						selected_row_names.push(row_name);
					}
				}
			});
		}
		
		frm.doc.invoices.forEach(function(row) {
			let amount = flt(row.outstanding_amount) || 0;
			total_all += amount;
			
			// Check if this row is selected
			if (selected_row_names.indexOf(row.name) !== -1) {
				total_selected += amount;
			}
			
			// Get currency from first row that has currency
			if (!currency && row.currency) {
				currency = row.currency;
			}
		});
	}
	
	// Display totals below invoices table
	display_table_totals(frm, 'invoices', total_selected, total_all, currency, __('Total Outstanding Amount'));
	
	// Show message
	if (total_selected > 0) {
		frappe.show_alert({
			message: __('Selected Invoice Total: {0}', [format_currency(total_selected, currency)]),
			indicator: 'green'
		}, 3);
	} else {
		frappe.show_alert({
			message: __('Please select at least one invoice row'),
			indicator: 'orange'
		}, 3);
	}
}

function update_invoice_total(frm) {
	// Calculate total outstanding amount from all invoices (for display on load)
	let total_all = 0;
	let total_selected = 0;
	let currency = '';
	
	if (frm.doc.invoices && frm.doc.invoices.length > 0) {
		frm.doc.invoices.forEach(function(row) {
			let amount = flt(row.outstanding_amount) || 0;
			total_all += amount;
			
			// Get currency from first row that has currency
			if (!currency && row.currency) {
				currency = row.currency;
			}
		});
	}
	
	// Display totals below invoices table (selected will be 0 on initial load)
	display_table_totals(frm, 'invoices', total_selected, total_all, currency, __('Total Outstanding Amount'));
}

function calculate_selected_payment_total(frm) {
	// Calculate total amount from selected payments
	let total_selected = 0;
	let total_all = 0;
	let currency = '';
	
	if (frm.doc.payments && frm.doc.payments.length > 0) {
		// Get selected row names by checking checkboxes in DOM
		let selected_row_names = [];
		if (frm.fields_dict.payments && frm.fields_dict.payments.grid) {
			let grid = frm.fields_dict.payments.grid;
			let $wrapper = $(grid.wrapper);
			
			// Find all checked checkboxes in the payments grid
			$wrapper.find('input[type="checkbox"]:checked').each(function() {
				let $checkbox = $(this);
				let $row = $checkbox.closest('[data-name]');
				if ($row.length) {
					let row_name = $row.attr('data-name');
					if (row_name && selected_row_names.indexOf(row_name) === -1) {
						selected_row_names.push(row_name);
					}
				}
			});
		}
		
		frm.doc.payments.forEach(function(row) {
			let amount = flt(row.amount) || 0;
			total_all += amount;
			
			// Check if this row is selected
			if (selected_row_names.indexOf(row.name) !== -1) {
				total_selected += amount;
			}
			
			// Get currency from first row that has currency
			if (!currency && row.currency) {
				currency = row.currency;
			}
		});
	}
	
	// Display totals below payments table
	display_table_totals(frm, 'payments', total_selected, total_all, currency, __('Total Payment Amount'));
	
	// Show message
	if (total_selected > 0) {
		frappe.show_alert({
			message: __('Selected Payment Total: {0}', [format_currency(total_selected, currency)]),
			indicator: 'green'
		}, 3);
	} else {
		frappe.show_alert({
			message: __('Please select at least one payment row'),
			indicator: 'orange'
		}, 3);
	}
}

function update_payment_total(frm) {
	// Calculate total amount from all payments (for display on load)
	let total_all = 0;
	let total_selected = 0;
	let currency = '';
	
	if (frm.doc.payments && frm.doc.payments.length > 0) {
		frm.doc.payments.forEach(function(row) {
			let amount = flt(row.amount) || 0;
			total_all += amount;
			
			// Get currency from first row that has currency
			if (!currency && row.currency) {
				currency = row.currency;
			}
		});
	}
	
	// Display totals below payments table (selected will be 0 on initial load)
	display_table_totals(frm, 'payments', total_selected, total_all, currency, __('Total Payment Amount'));
}

function display_table_totals(frm, table_fieldname, total_selected, total_all, currency, label) {
	if (!frm.fields_dict[table_fieldname] || !frm.fields_dict[table_fieldname].wrapper) {
		return;
	}
	
	// Remove existing total if any
	let total_wrapper_id = table_fieldname + '_total_wrapper';
	let existing_wrapper = $(frm.fields_dict[table_fieldname].wrapper).find('#' + total_wrapper_id);
	if (existing_wrapper.length) {
		existing_wrapper.remove();
	}
	
	// Format the total amounts
	let formatted_selected = format_currency(total_selected, currency);
	let formatted_all = format_currency(total_all, currency);
	
	// Determine button text and function based on table
	let button_text = '';
	let button_function = null;
	if (table_fieldname === 'invoices') {
		button_text = __('Calculate Selected Invoice Total');
		button_function = function() { calculate_selected_invoice_total(frm); };
	} else if (table_fieldname === 'payments') {
		button_text = __('Calculate Selected Payment Total');
		button_function = function() { calculate_selected_payment_total(frm); };
	}
	
	// Create total display element with two totals side by side and button
	let total_html = `
		<div id="${total_wrapper_id}" style="margin-top: 10px; padding: 10px; background-color: #f8f9fa; border-top: 2px solid #dee2e6;">
			<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
				<div style="text-align: left;">
					<strong style="font-size: 13px; color: #0066cc;">${__('Selected')} ${label}: </strong>
					<span style="font-size: 14px; font-weight: bold; color: #ff6b35;">${formatted_selected}</span>
				</div>
				<div style="text-align: right;">
					<strong style="font-size: 13px; color: #0066cc;">${__('All')} ${label}: </strong>
					<span style="font-size: 14px; font-weight: bold; color: #28a745;">${formatted_all}</span>
				</div>
			</div>
			<div style="text-align: center; margin-top: 8px;">
				<button id="${table_fieldname}_calculate_btn" class="btn btn-primary btn-sm" style="padding: 6px 20px; font-size: 12px;">
					${button_text}
				</button>
			</div>
		</div>
	`;
	
	// Append total below the table
	$(frm.fields_dict[table_fieldname].wrapper).append(total_html);
	
	// Attach click handler to the button
	if (button_function) {
		$(`#${table_fieldname}_calculate_btn`).off('click').on('click', function() {
			button_function();
		});
	}
}


function format_currency(amount, currency) {
	// Format currency using Frappe's currency formatter
	if (currency) {
		return frappe.format(amount, {
			fieldtype: 'Currency',
			options: currency
		});
	}
	return frappe.format(amount, {
		fieldtype: 'Currency'
	});
}

