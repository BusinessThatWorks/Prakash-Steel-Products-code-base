frappe.ui.form.on("PO Recommendation Snapshot", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Run Manual Snapshot"), () => {
				frappe.call({
					method: "prakash_steel.po_recommendation_history.doctype.po_recommendation_snapshot.po_recommendation_snapshot.run_manual_snapshot",
					args: {
						purchase: frm.doc.purchase,
						sell: frm.doc.sell,
						buffer_flag: frm.doc.buffer_flag,
						sku_type_filter: frm.doc.sku_type_filter,
						item_code_filter: frm.doc.item_code_filter,
					},
					freeze: true,
					freeze_message: __("Capturing PO Recommendation data..."),
					callback(r) {
						if (r.message) {
							frappe.set_route("Form", "PO Recommendation Snapshot", r.message);
						}
					},
				});
			});
		}
	},
});
