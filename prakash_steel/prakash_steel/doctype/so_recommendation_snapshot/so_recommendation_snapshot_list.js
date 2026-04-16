frappe.listview_settings["SO Recommendation Snapshot"] = {
	onload(listview) {
		listview.page.add_action_item(__("Capture Snapshot Now"), function () {
			frappe.confirm(
				__("Capture a fresh Open SO Analysis snapshot now?"),
				function () {
					frappe.show_alert({ message: __("Capturing snapshot..."), indicator: "blue" });
					frappe.call({
						method: "prakash_steel.prakash_steel.doctype.so_recommendation_snapshot.so_recommendation_snapshot.run_manual_snapshot",
						callback(r) {
							if (r.message) {
								frappe.set_route("Form", "SO Recommendation Snapshot", r.message);
							}
						},
					});
				}
			);
		});
	},

	get_indicator(doc) {
		if (doc.status === "Success") return [__("Success"), "green", "status,=,Success"];
		if (doc.status === "Failed") return [__("Failed"), "red", "status,=,Failed"];
	},
};
