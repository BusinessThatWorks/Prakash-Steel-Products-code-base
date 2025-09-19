frappe.ui.form.on("Sales Order Item", {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.item_code) {
            frappe.call({
                method: "prakash_steel.api.get_last_sales_invoice_rate.get_last_sales_invoice_rate",
                args: {
                    item_code: row.item_code,
                },
                callback: function(r) {
                    frappe.model.set_value(cdt, cdn, "custom_last_rate", r.message || 0);
                }
            });
            frappe.call({
                method: "prakash_steel.api.get_last_sales_invoice_sold_qty.get_last_sales_invoice_sold_qty",
                args: {
                    item_code: row.item_code,
                },
                callback: function(r) {
                    frappe.model.set_value(cdt, cdn, "custom_last_sold_qty", r.message || 0);
                }
            });
        }
    }
});