// Copyright (c) 2026, Beetashoke Chakraborty and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase receipt Solver", {
	pr_solver(_frm) {
		frappe.confirm(
			"This will fix <b>custom_total_party_billing_qty</b> on all submitted Purchase Receipts by summing their item-level <b>custom_party_billing_qty</b>. Continue?",
			() => {
				frappe.call({
					method: "prakash_steel.prakash_steel.doctype.purchase_receipt_solver.purchase_receipt_solver.fix_total_party_billing_qty",
					freeze: true,
					freeze_message: "Fixing Purchase Receipts...",
					callback(r) {
						if (r.message) {
							const { fixed, details } = r.message;
							if (fixed === 0) {
								frappe.msgprint("All Purchase Receipts already have correct values. Nothing to fix.");
							} else {
								let msg = `Fixed <b>${fixed}</b> Purchase Receipt(s):<br><br>`;
								msg += details
									.map(d => `• ${d.pr}: ${d.old} → ${d.new}`)
									.join("<br>");
								frappe.msgprint({ title: "PR Solver Done", message: msg, indicator: "green" });
							}
						}
					},
				});
			}
		);
	},
});
