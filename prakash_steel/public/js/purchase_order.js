// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Order", {
    refresh(frm) {
        // Optional: existing UI behaviour
        if (frm.doc.status === "Closed") {
            frappe.show_alert(
                {
                    message: __(
                        "Purchase Order status changed to Closed. Quantity validation will be performed."
                    ),
                    indicator: "blue",
                },
                3
            );
        }

        // Patch cancel behaviour once per form instance
        if (frm.__pspl_po_cancel_patched) return;
        frm.__pspl_po_cancel_patched = true;

        const original_savecancel = frm.savecancel
            ? frm.savecancel.bind(frm)
            : null;

        if (!original_savecancel) return;

        frm.savecancel = function (btn, callback, on_error) {
            // For non-submitted docs, fall back to standard behaviour
            if (frm.doc.docstatus !== 1) {
                return original_savecancel(btn, callback, on_error);
            }

            const proceed_with_standard_cancel = () => {
                original_savecancel(btn, callback, on_error);
            };

            const existing_reason = (frm.doc.custom_cancel_reason || "").trim();
            if (existing_reason) {
                return proceed_with_standard_cancel();
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
                            "Wrong Qty",
                            "Wrong Item",
                            "Wrong Supplier",
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
                        showCustomReasonDialog(frm, proceed_with_standard_cancel, on_error);
                    } else {
                        // For options A, B, C: Save the reason directly and proceed
                        reasonOptionsDialog.hide();
                        frappe.call({
                            method: "prakash_steel.utils.purchase_order_cancel.set_purchase_order_cancel_reason",
                            args: {
                                name: frm.doc.name,
                                reason: selectedOption,
                            },
                            freeze: true,
                            freeze_message: __("Saving Cancel Reason..."),
                            callback() {
                                proceed_with_standard_cancel();
                            },
                            error: on_error,
                        });
                    }
                },
            });

            // Function to show the custom reason dialog (for "Others" option)
            function showCustomReasonDialog(frm, proceedCallback, onError) {
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
                        if (!values || !values.cancel_reason) {
                            return;
                        }

                        frappe.call({
                            method: "prakash_steel.utils.purchase_order_cancel.set_purchase_order_cancel_reason",
                            args: {
                                name: frm.doc.name,
                                reason: values.cancel_reason,
                            },
                            freeze: true,
                            freeze_message: __("Saving Cancel Reason..."),
                            callback() {
                                customReasonDialog.hide();
                                proceedCallback();
                            },
                            error: onError,
                        });
                    },
                });

                customReasonDialog.show();
            }

            reasonOptionsDialog.show();
        };
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
            // Unfreeze UI so user can type in our dialog
            frappe.dom.unfreeze();

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
                        showCustomReasonDialog(frm, resolve, reject);
                    } else {
                        // For options A, B, C: Save the reason directly and resolve
                        reasonOptionsDialog.hide();
                        frappe.call({
                            method: "prakash_steel.utils.purchase_order_cancel.set_purchase_order_cancel_reason",
                            args: {
                                name: frm.doc.name,
                                reason: selectedOption,
                            },
                            freeze: true,
                            freeze_message: __("Saving Cancel Reason..."),
                            callback() {
                                resolve();
                            },
                            error(err) {
                                frappe.dom.unfreeze();
                                reject(err);
                            },
                        });
                    }
                },
            });

            // Function to show the custom reason dialog (for "Others" option)
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
                        if (!values || !values.cancel_reason) {
                            return;
                        }

                        frappe.call({
                            method: "prakash_steel.utils.purchase_order_cancel.set_purchase_order_cancel_reason",
                            args: {
                                name: frm.doc.name,
                                reason: values.cancel_reason,
                            },
                            freeze: true,
                            freeze_message: __("Saving Cancel Reason..."),
                            callback() {
                                customReasonDialog.hide();
                                resolveCallback();
                            },
                            error(err) {
                                customReasonDialog.hide();
                                frappe.dom.unfreeze();
                                rejectCallback(err);
                            },
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

    on_update_after_submit(frm) {
        // Client-side notification after update
        if (frm.doc.status === "Closed") {
            frappe.show_alert(
                {
                    message: __(
                        "Purchase Order updated. Quantity validation will be performed."
                    ),
                    indicator: "blue",
                },
                3
            );
        }
    },
});

// Note: Client-side validation for PO quantity is handled server-side
// to avoid permission issues with child doctypes (Purchase Order Item)
// The server-side validation in purchase_order.py will check quantities
// and send email notifications when status is changed to Closed and items have shortfall





