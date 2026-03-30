// // Copyright (c) 2026, Beetashoke Chakraborty and contributors
// // For license information, please see license.txt

// frappe.ui.form.on("desc solver in si", {
// 	desc_solver(_frm) {
// 		frappe.confirm(
// 			"This will populate <b>custom_desc_code</b> in all Sales Invoice items that are missing it. Continue?",
// 			() => {
// 				frappe.call({
// 					method: "prakash_steel.prakash_steel.doctype.desc_solver_in_si.desc_solver_in_si.solve_desc_codes",
// 					freeze: true,
// 					freeze_message: "Solving desc codes...",
// 					callback(r) {
// 						if (r.message) {
// 							frappe.msgprint({
// 								title: "Done",
// 								message: r.message,
// 								indicator: "green"
// 							});
// 						}
// 					}
// 				});
// 			}
// 		);
// 	}
// });
