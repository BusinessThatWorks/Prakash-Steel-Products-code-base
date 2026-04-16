frappe.ui.form.on("Stock Balance Snapshot", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Run Manual Snapshot"), () => {
				frappe.call({
					method: "prakash_steel.prakash_steel.doctype.stock_balance_snapshot.stock_balance_snapshot.run_manual_snapshot",
					freeze: true,
					freeze_message: __("Capturing Item Wise Stock Balance..."),
					callback(r) {
						if (r.message) {
							frappe.set_route("Form", "Stock Balance Snapshot", r.message);
						}
					},
				});
			});
		}
	},
});
