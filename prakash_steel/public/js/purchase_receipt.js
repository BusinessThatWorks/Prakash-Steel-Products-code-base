// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Receipt', {
    refresh: function (frm) {
        // Optional: Add any UI enhancements here
    },

    on_submit: function (frm) {
        // Client-side notification after submit
        // The server-side hook will handle the email notification
        frappe.show_alert({
            message: __('Purchase Receipt submitted. Quantity validation will be performed.'),
            indicator: 'green'
        }, 3);
    }
});

// Note: Client-side validation for PO quantity is handled server-side
// to avoid permission issues with child doctypes (Purchase Order Item)
// The server-side validation in purchase_receipt.py will check quantities
// and send email notifications when threshold is exceeded

