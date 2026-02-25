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
    },

    before_cancel(frm) {
        // If a cancel reason is already set, allow normal cancellation
        if (frm.doc.custom_cancel_reason && frm.doc.custom_cancel_reason.trim()) {
            return;
        }

        const dialog = new frappe.ui.Dialog({
            title: __("Cancel Reason Required"),
            fields: [
                {
                    fieldname: "cancel_reason",
                    label: __("Cancel Reason"),
                    fieldtype: "Small Text",
                    reqd: 1,
                },
            ],
            primary_action_label: __("Cancel Purchase Receipt"),
            primary_action(values) {
                if (!values || !values.cancel_reason) {
                    return;
                }

                frappe.call({
                    method: "prakash_steel.utils.purchase_receipt_cancel.cancel_purchase_receipt_with_reason",
                    args: {
                        name: frm.doc.name,
                        reason: values.cancel_reason,
                    },
                    freeze: true,
                    freeze_message: __("Cancelling Purchase Receipt..."),
                    callback() {
                        dialog.hide();
                        frm.reload_doc();
                    },
                });
            },
        });

        dialog.show();

        // Prevent the standard cancel; our server method will perform the cancel
        frappe.validated = false;
    },
});

// Note: Client-side validation for PO quantity is handled server-side
// to avoid permission issues with child doctypes (Purchase Order Item)
// The server-side validation in purchase_receipt.py will check quantities
// and send email notifications when threshold is exceeded

