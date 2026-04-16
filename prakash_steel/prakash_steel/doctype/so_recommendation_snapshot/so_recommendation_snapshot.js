// ── Cell colour formatters (applied globally for these field names) ──────────

frappe.form.formatters["order_status"] = function (value) {
	if (!value) return "";
	const map = {
		BLACK:  { bg: "#000000", fg: "#ffffff" },
		RED:    { bg: "#e03636", fg: "#ffffff" },
		YELLOW: { bg: "#f5d327", fg: "#000000" },
		GREEN:  { bg: "#36a83a", fg: "#ffffff" },
		WHITE:  { bg: "#f0f0f0", fg: "#000000" },
	};
	const c = map[value];
	if (!c) return value;
	return `<span style="background:${c.bg};color:${c.fg};padding:2px 10px;border-radius:4px;font-weight:bold;">${value}</span>`;
};

frappe.form.formatters["line_fullkit"] = function (value) {
	if (!value) return "";
	const map = {
		"Full-kit": { bg: "#36a83a", fg: "#ffffff" },
		"Partial":  { bg: "#f5d327", fg: "#000000" },
		"Pending":  { bg: "#e03636", fg: "#ffffff" },
	};
	const c = map[value];
	if (!c) return value;
	return `<span style="background:${c.bg};color:${c.fg};padding:2px 10px;border-radius:4px;font-weight:bold;">${value}</span>`;
};

frappe.form.formatters["order_fullkit"] = function (value) {
	if (!value) return "";
	const map = {
		"Full-kit": { bg: "#36a83a", fg: "#ffffff" },
		"Partial":  { bg: "#f5d327", fg: "#000000" },
		"Pending":  { bg: "#e03636", fg: "#ffffff" },
	};
	const c = map[value];
	if (!c) return value;
	return `<span style="background:${c.bg};color:${c.fg};padding:2px 10px;border-radius:4px;font-weight:bold;">${value}</span>`;
};

// ── Form ─────────────────────────────────────────────────────────────────────

frappe.ui.form.on("SO Recommendation Snapshot", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Run Manual Snapshot"), () => {
				frappe.call({
					method: "prakash_steel.prakash_steel.doctype.so_recommendation_snapshot.so_recommendation_snapshot.run_manual_snapshot",
					freeze: true,
					freeze_message: __("Capturing SO Recommendation data..."),
					callback(r) {
						if (r.message) {
							frappe.set_route("Form", "SO Recommendation Snapshot", r.message);
						}
					},
				});
			});
		}
	},
});
