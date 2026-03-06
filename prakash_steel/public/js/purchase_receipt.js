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

        // First dialog: Show 4 options
        const reasonOptionsDialog = new frappe.ui.Dialog({
            title: __("Select Cancel Reason"),
            fields: [
                {
                    fieldname: "cancel_reason_option",
                    label: __("Cancel Reason"),
                    fieldtype: "Select",
                    options: [
                        "Rate Mistake",
                        "Size Mistake",
                        "Data Entry Mistake",
                        "Others",
                    ],
                    reqd: 1,
                },
            ],
            primary_action_label: __("Continue"),
            primary_action(values) {
                if (!values || !values.cancel_reason_option) {
                    return;
                }

                const selectedOption = values.cancel_reason_option;

                // If "Others" is selected, show the text input dialog
                if (selectedOption === "Others") {
                    reasonOptionsDialog.hide();
                    showCustomReasonDialog(frm);
                } else {
                    // For options A, B, C: Save the reason directly and cancel
                    reasonOptionsDialog.hide();
                    frappe.call({
                        method: "prakash_steel.utils.purchase_receipt_cancel.cancel_purchase_receipt_with_reason",
                        args: {
                            name: frm.doc.name,
                            reason: selectedOption,
                        },
                        freeze: true,
                        freeze_message: __("Cancelling Purchase Receipt..."),
                        callback() {
                            frm.reload_doc();
                        },
                    });
                }
            },
        });

        // Function to show the custom reason dialog (for "Others" option)
        function showCustomReasonDialog(frm) {
            const customReasonDialog = new frappe.ui.Dialog({
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
                            customReasonDialog.hide();
                            frm.reload_doc();
                        },
                    });
                },
            });

            customReasonDialog.show();
        }

        reasonOptionsDialog.show();

        // Prevent the standard cancel; our server method will perform the cancel
        frappe.validated = false;
    },
});

// Note: Client-side validation for PO quantity is handled server-side
// to avoid permission issues with child doctypes (Purchase Order Item)
// The server-side validation in purchase_receipt.py will check quantities
// and send email notifications when threshold is exceeded

