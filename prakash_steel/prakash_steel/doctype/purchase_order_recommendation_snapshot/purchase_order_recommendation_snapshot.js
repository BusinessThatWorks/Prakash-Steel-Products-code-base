frappe.ui.form.on("Purchase Order Recommendation Snapshot", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Run Manual Snapshot"), () => {
				frappe.call({
					method: "prakash_steel.prakash_steel.doctype.purchase_order_recommendation_snapshot.purchase_order_recommendation_snapshot.run_manual_snapshot",
					freeze: true,
					freeze_message: __("Capturing PO Recommendation data..."),
					callback(r) {
						if (r.message) {
							frappe.set_route("Form", "Purchase Order Recommendation Snapshot", r.message);
						}
					},
				});
			});
		}
	},
});
