frappe.ui.form.on("Sales Order", {
    refresh(frm) {
        // Patch cancel behavior once per form instance
        if (frm.__pspl_cancel_patched) return;
        frm.__pspl_cancel_patched = true;

        const original_savecancel = frm.savecancel.bind(frm);

        frm.savecancel = function (btn, callback, on_error) {
            // For non-submitted docs, fall back to standard behaviour
            if (frm.doc.docstatus !== 1) {
                return original_savecancel(btn, callback, on_error);
            }

            // If reason is already set (e.g. via some other UI), just run our server cancel once
            const run_cancel_with_reason = (reason) => {
                frappe.call({
                    method: "prakash_steel.utils.sales_order_cancel.cancel_sales_order_with_reason",
                    args: {
                        name: frm.doc.name,
                        reason,
                    },
                    freeze: true,
                    freeze_message: __("Cancelling Sales Order..."),
                    callback() {
                        frm.reload_doc();
                    },
                    error: on_error,
                });
            };

            const existing_reason = (frm.doc.custom_cancel_reason || "").trim();
            if (existing_reason) {
                run_cancel_with_reason(existing_reason);
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
                primary_action_label: __("Cancel Sales Order"),
                primary_action(values) {
                    if (!values || !values.cancel_reason) {
                        return;
                    }

                    dialog.hide();
                    run_cancel_with_reason(values.cancel_reason);
                },
            });

            dialog.show();
        };
    },
});

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