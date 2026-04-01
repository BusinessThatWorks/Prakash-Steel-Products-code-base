frappe.ui.form.on("Sales Invoice", {
    onload(frm) {
        setup_sales_order_row_guard(frm);
        if (frm.is_new() && frm.doc.company) {
            fetch_dispatch_address(frm);
        }
    },
    refresh(frm) {
        setup_sales_order_row_guard(frm);

        if (frm.is_new() && !frm.doc.dispatch_address_name) {
            fetch_dispatch_address(frm);
        }

        // When a new amendment is opened, clear fields that must not carry over
        if (frm.is_new() && frm.doc.amended_from) {
            if (frm.doc.custom_stock_entry_id) {
                frm.set_value("custom_stock_entry_id", "");
            }
            if (frm.doc.custom_cancel_reason) {
                frm.set_value("custom_cancel_reason", "");
            }
        }
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
                        "Party Name Mistake",
                        "Rate Mistake",
                        "Size Mistake",
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

                // If "Others" or "Party Name Mistake" is selected, show the text input dialog
                if (selectedOption === "Others" || selectedOption === "Party Name Mistake") {
                    reasonOptionsDialog.hide();
                    showCustomReasonDialog(frm, selectedOption);
                } else {
                    // For other options: save the reason label directly and cancel
                    reasonOptionsDialog.hide();
                    frappe.call({
                        method: "prakash_steel.utils.sales_invoice_cancel.cancel_sales_invoice_with_reason",
                        args: {
                            name: frm.doc.name,
                            reason: selectedOption,
                        },
                        freeze: true,
                        freeze_message: __("Cancelling Sales Invoice..."),
                        callback() {
                            frm.reload_doc();
                        },
                    });
                }
            },
        });

        // Function to show the custom reason dialog (for "Others" / Party Name Mistake)
        function showCustomReasonDialog(frm, selectedOption) {
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
                primary_action_label: __("Cancel Invoice"),
                primary_action(values) {
                    if (!values || !values.cancel_reason) {
                        return;
                    }

                    frappe.call({
                        method: "prakash_steel.utils.sales_invoice_cancel.cancel_sales_invoice_with_reason",
                        args: {
                            name: frm.doc.name,
                            reason: `${selectedOption}, ${values.cancel_reason}`,
                        },
                        freeze: true,
                        freeze_message: __("Cancelling Sales Invoice..."),
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

function fetch_dispatch_address(frm) {
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Address",
            filters: [
                ["address_title", "=", "Prakash Steel Products Pvt Ltd"],
                ["is_shipping_address", "=", 1]
            ],
            fields: ["name"],
            limit: 1
        },
        callback: function (r) {
            if (r.message && r.message.length > 0) {
                frm.set_value("dispatch_address_name", r.message[0].name);
            }
        }
    });
}

function setup_sales_order_row_guard(frm) {
    const grid = frm.get_field("items")?.grid;
    if (!grid || grid.__pspl_row_guard_attached) {
        return;
    }

    grid.__pspl_row_guard_attached = true;

    const original_add_new_row = grid.add_new_row.bind(grid);
    grid.add_new_row = function (idx, callback, show) {
        const hasSalesOrderRows = (frm.doc.items || []).some(
            (d) => d.sales_order
        );

        // Only enforce when the invoice is Sales Order–based
        if (!hasSalesOrderRows) {
            return original_add_new_row(idx, callback, show);
        }

        frappe.msgprint({
            title: __("Not Allowed"),
            message: __(
                "Only items linked to Sales Order are allowed in this Sales Invoice."
            ),
            indicator: "red",
        });
    };
}
