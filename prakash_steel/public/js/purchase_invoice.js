frappe.ui.form.on("Purchase Invoice", {
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





