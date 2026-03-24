// Copyright (c) 2026, Beetashoke Chakraborty and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bom Item type solver", {
	bit_solver(_frm) {
		console.log("BIT Solver: Button clicked. Calling solve_bom_item_types...");

		frappe.show_progress("BIT Solver", 0, 100, "Scanning BOMs...");

		frappe.call({
			method: "prakash_steel.prakash_steel.doctype.bom_item_type_solver.bom_item_type_solver.solve_bom_item_types",
			freeze: true,
			freeze_message: "Solving BOM Item Types... Please wait.",
			callback(r) {
				frappe.hide_progress();

				if (r.exc) {
					console.error("BIT Solver: Server returned an error:", r.exc);
					frappe.msgprint({
						title: "BIT Solver Error",
						indicator: "red",
						message: "An error occurred. Check the server logs for details.",
					});
					return;
				}

				const res = r.message;
				console.log("BIT Solver: Server response:", res);
				console.log(`BIT Solver: BOM parent  -> Updated: ${res.parent_updated}, Skipped: ${res.parent_skipped}`);
				console.log(`BIT Solver: BOM Item rows -> Updated: ${res.child_updated}, Skipped: ${res.child_skipped}`);

				frappe.msgprint({
					title: "BIT Solver Completed",
					indicator: "green",
					message: `
						<b>BOM (parent):</b><br>
						&nbsp;&nbsp;Updated: <b>${res.parent_updated}</b> &nbsp;|&nbsp; Skipped (already correct / no item type): <b>${res.parent_skipped}</b>
						<br><br>
						<b>BOM Items (child rows):</b><br>
						&nbsp;&nbsp;Updated: <b>${res.child_updated}</b> &nbsp;|&nbsp; Skipped: <b>${res.child_skipped}</b>
					`,
				});
			},
		});
	},
});
