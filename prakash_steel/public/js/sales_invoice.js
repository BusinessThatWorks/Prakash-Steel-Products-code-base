frappe.ui.form.on("Sales Invoice", {
    onload(frm) {
        setup_sales_order_row_guard(frm);
    },
    refresh(frm) {
        setup_sales_order_row_guard(frm);
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
