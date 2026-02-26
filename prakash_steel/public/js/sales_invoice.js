frappe.ui.form.on("Sales Invoice", {
    onload(frm) {
        setup_sales_order_row_guard(frm);
    },
    refresh(frm) {
        setup_sales_order_row_guard(frm);
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
            primary_action_label: __("Cancel Invoice"),
            primary_action(values) {
                if (!values || !values.cancel_reason) {
                    return;
                }

                frappe.call({
                    method: "prakash_steel.utils.sales_invoice_cancel.cancel_sales_invoice_with_reason",
                    args: {
                        name: frm.doc.name,
                        reason: values.cancel_reason,
                    },
                    freeze: true,
                    freeze_message: __("Cancelling Sales Invoice..."),
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

function setup_sales_order_row_guard(frm) {
    const grid = frm.get_field("items")?.grid;
    if (!grid || grid.__pspl_row_guard_attached) {
        return;
    }

    grid.__pspl_row_guard_attached = true;

    grid.on("grid-row-added", (row) => {
        const hasSalesOrderRows = (frm.doc.items || []).some(
            (d) => d.sales_order
        );

        // Only enforce when the invoice is Sales Order–based
        if (!hasSalesOrderRows) return;

        const child = row?.doc || {};
        if (!child.sales_order) {
            frappe.msgprint({
                title: __("Not Allowed"),
                message: __(
                    "Only items linked to Sales Order are allowed in this Sales Invoice."
                ),
                indicator: "red",
            });

            // Remove the just-added row to prevent save with invalid data
            grid.remove(child);
        }
    });
}
