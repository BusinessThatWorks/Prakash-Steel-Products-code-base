// frappe.ui.form.on("Purchase Invoice", {
//     before_cancel(frm) {
//         // If a cancel reason is already set, allow normal cancellation
//         if (frm.doc.custom_cancel_reason && frm.doc.custom_cancel_reason.trim()) {
//             return;
//         }

//         // First dialog: Show 4 options
//         const reasonOptionsDialog = new frappe.ui.Dialog({
//             title: __("Select Cancel Reason"),
//             fields: [
//                 {
//                     fieldname: "cancel_reason_option",
//                     label: __("Cancel Reason"),
//                     fieldtype: "Select",
//                     options: [
//                         "Rate Mistake",
//                         "Size Mistake",
//                         "Data Entry Mistake",
//                         "Others",
//                     ],
//                     reqd: 1,
//                 },
//             ],
//             primary_action_label: __("Continue"),
//             primary_action(values) {
//                 if (!values || !values.cancel_reason_option) {
//                     return;
//                 }

//                 const selectedOption = values.cancel_reason_option;

//                 // If "Others" is selected, show the text input dialog
//                 if (selectedOption === "Others") {
//                     reasonOptionsDialog.hide();
//                     showCustomReasonDialog(frm);
//                 } else {
//                     // For options A, B, C: Save the reason directly and cancel
//                     reasonOptionsDialog.hide();
//                     frappe.call({
//                         method: "prakash_steel.utils.purchase_invoice_cancel.cancel_purchase_invoice_with_reason",
//                         args: {
//                             name: frm.doc.name,
//                             reason: selectedOption,
//                         },
//                         freeze: true,
//                         freeze_message: __("Cancelling Purchase Invoice..."),
//                         callback() {
//                             frm.reload_doc();
//                         },
//                     });
//                 }
//             },
//         });

//         // Function to show the custom reason dialog (for "Others" option)
//         function showCustomReasonDialog(frm) {
//             const customReasonDialog = new frappe.ui.Dialog({
//                 title: __("Cancel Reason Required"),
//                 fields: [
//                     {
//                         fieldname: "cancel_reason",
//                         label: __("Cancel Reason"),
//                         fieldtype: "Small Text",
//                         reqd: 1,
//                     },
//                 ],
//                 primary_action_label: __("Cancel Purchase Invoice"),
//                 primary_action(values) {
//                     if (!values || !values.cancel_reason) {
//                         return;
//                     }

//                     frappe.call({
//                         method: "prakash_steel.utils.purchase_invoice_cancel.cancel_purchase_invoice_with_reason",
//                         args: {
//                             name: frm.doc.name,
//                             reason: values.cancel_reason,
//                         },
//                         freeze: true,
//                         freeze_message: __("Cancelling Purchase Invoice..."),
//                         callback() {
//                             customReasonDialog.hide();
//                             frm.reload_doc();
//                         },
//                     });
//                 },
//             });

//             customReasonDialog.show();
//         }

//         reasonOptionsDialog.show();

//         // Prevent the standard cancel; our server method will perform the cancel
//         frappe.validated = false;
//     },
// });





frappe.ui.form.on("Purchase Invoice", {
    refresh(frm) {
        // Clear cancel reason on amended drafts — the field is copied from the
        // cancelled doc but should not carry over to the new invoice.
        if (frm.doc.amended_from && frm.doc.docstatus === 0 && frm.doc.custom_cancel_reason) {
            frm.set_value("custom_cancel_reason", "");
        }
    },

    before_workflow_action(frm) {
        // Only intercept the Reject action
        if (frm.selected_workflow_action !== "Reject") {
            return;
        }

        // If reason already present, allow workflow to proceed
        if (frm.doc.custom_cancel_reason && frm.doc.custom_cancel_reason.trim()) {
            return;
        }

        return new Promise((resolve, reject) => {
            frappe.dom.unfreeze();

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
                    if (!values || !values.cancel_reason_option) return;

                    const selectedOption = values.cancel_reason_option;

                    if (selectedOption === "Others") {
                        reasonOptionsDialog.hide();
                        showCustomReasonDialog(frm, resolve, reject);
                    } else {
                        reasonOptionsDialog.hide();
                        frappe.call({
                            method: "prakash_steel.utils.purchase_invoice_cancel.set_purchase_invoice_cancel_reason",
                            args: { name: frm.doc.name, reason: selectedOption },
                            freeze: true,
                            freeze_message: __("Saving Cancel Reason..."),
                            callback() { resolve(); },
                            error(err) { frappe.dom.unfreeze(); reject(err); },
                        });
                    }
                },
            });

            function showCustomReasonDialog(frm, resolveCallback, rejectCallback) {
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
                    primary_action_label: __("Continue"),
                    primary_action(values) {
                        if (!values || !values.cancel_reason) return;

                        frappe.call({
                            method: "prakash_steel.utils.purchase_invoice_cancel.set_purchase_invoice_cancel_reason",
                            args: { name: frm.doc.name, reason: values.cancel_reason },
                            freeze: true,
                            freeze_message: __("Saving Cancel Reason..."),
                            callback() { customReasonDialog.hide(); resolveCallback(); },
                            error(err) { customReasonDialog.hide(); frappe.dom.unfreeze(); rejectCallback(err); },
                        });
                    },
                });

                customReasonDialog.set_secondary_action(() => {
                    customReasonDialog.hide();
                    frappe.dom.unfreeze();
                    rejectCallback();
                });

                customReasonDialog.show();
            }

            reasonOptionsDialog.set_secondary_action(() => {
                reasonOptionsDialog.hide();
                frappe.dom.unfreeze();
                reject();
            });

            reasonOptionsDialog.show();
        });
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
                        method: "prakash_steel.utils.purchase_invoice_cancel.cancel_purchase_invoice_with_reason",
                        args: {
                            name: frm.doc.name,
                            reason: selectedOption,
                        },
                        freeze: true,
                        freeze_message: __("Cancelling Purchase Invoice..."),
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
                primary_action_label: __("Cancel Purchase Invoice"),
                primary_action(values) {
                    if (!values || !values.cancel_reason) {
                        return;
                    }

                    frappe.call({
                        method: "prakash_steel.utils.purchase_invoice_cancel.cancel_purchase_invoice_with_reason",
                        args: {
                            name: frm.doc.name,
                            reason: values.cancel_reason,
                        },
                        freeze: true,
                        freeze_message: __("Cancelling Purchase Invoice..."),
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
