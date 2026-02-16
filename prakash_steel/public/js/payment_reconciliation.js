// Copyright (c) 2025, Prakash Steel and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Reconciliation', {
	refresh: function(frm) {
		// Update visibility of custom_supplier_invoice_no on refresh
		update_supplier_invoice_no_visibility(frm);
	}
});

frappe.ui.form.on('Payment Reconciliation Invoice', {
	invoice_type: function(frm, cdt, cdn) {
		// Update visibility when invoice_type changes
		update_row_supplier_invoice_no_visibility(frm, cdt, cdn);
	},
	
	invoices_add: function(frm, cdt, cdn) {
		// Update visibility when a new row is added
		update_row_supplier_invoice_no_visibility(frm, cdt, cdn);
	},
	
	invoices_refresh: function(frm) {
		// Update visibility for all rows when table is refreshed
		update_supplier_invoice_no_visibility(frm);
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

