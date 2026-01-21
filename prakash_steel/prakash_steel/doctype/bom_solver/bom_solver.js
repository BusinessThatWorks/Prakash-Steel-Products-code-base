// Copyright (c) 2026, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.ui.form.on("BOM Solver", {
	refresh(frm) {
		// Add button handler for solve_bom
		frm.add_custom_button(__("Solve BOM"), function() {
			solve_bom(frm);
		});
	},
});

function solve_bom(frm) {
	// Show confirmation dialog
	frappe.confirm(
		__("This will process ALL BOMs in the system. For each BOM:<br><br>" +
			"1. Remove bom_no from all BOM Item rows<br>" +
			"2. Set do_not_explode = 1 for all BOM Item rows<br>" +
			"3. Cancel linked Sales Orders/Invoices (if possible)<br>" +
			"4. Update and submit BOM<br>" +
			"5. Re-submit cancelled documents<br><br>" +
			"This process may take several minutes. Continue?"),
		function() {
			// User confirmed, proceed
			frappe.call({
				method: "prakash_steel.prakash_steel.doctype.bom_solver.bom_solver.solve_bom",
				freeze: true,
				freeze_message: __("Processing BOMs..."),
				callback: function(r) {
					if (r.message) {
						const results = r.message;
						
						// Build detailed message
						let message = __("BOM Processing Complete!<br><br>");
						message += __("<b>Summary:</b><br>");
						message += __("Total BOMs: {0}<br>", [results.total_boms]);
						message += __("Processed: {0}<br>", [results.processed]);
						message += __("Skipped: {0}<br>", [results.skipped]);
						message += __("Failed: {0}<br><br>", [results.failed]);
						
						// Show processed BOMs
						if (results.processed_list && results.processed_list.length > 0) {
							message += __("<b>Processed BOMs ({0}):</b><br>", [results.processed_list.length]);
							message += "<div style='max-height: 200px; overflow-y: auto; border: 1px solid #d1d8dd; padding: 10px; margin: 10px 0;'>";
							results.processed_list.forEach(function(item) {
								message += `<div style='padding: 5px 0; border-bottom: 1px solid #e7eef5;'>`;
								message += `<strong>${item.bom}</strong> (Item: ${item.item || 'N/A'})<br>`;
								message += `<small style='color: #6c7b7f;'>${item.message}</small>`;
								
								// Show cancelled documents
								if (item.cancelled_sos && item.cancelled_sos.length > 0) {
									message += `<br><small style='color: #8b4513;'>Cancelled SOs: ${item.cancelled_sos.join(', ')}</small>`;
								}
								if (item.cancelled_sis && item.cancelled_sis.length > 0) {
									message += `<br><small style='color: #8b4513;'>Cancelled SIs: ${item.cancelled_sis.join(', ')}</small>`;
								}
								
								// Show re-submitted documents
								if (item.re_submitted_sos && item.re_submitted_sos.length > 0) {
									message += `<br><small style='color: #28a745;'>✓ Re-submitted SOs: ${item.re_submitted_sos.join(', ')}</small>`;
								}
								if (item.re_submitted_sis && item.re_submitted_sis.length > 0) {
									message += `<br><small style='color: #28a745;'>✓ Re-submitted SIs: ${item.re_submitted_sis.join(', ')}</small>`;
								}
								
								// Show failed re-submissions
								if (item.failed_re_submit_sos && item.failed_re_submit_sos.length > 0) {
									message += `<br><small style='color: #dc3545;'>✗ Failed to re-submit SOs: ${item.failed_re_submit_sos.join(', ')}</small>`;
								}
								if (item.failed_re_submit_sis && item.failed_re_submit_sis.length > 0) {
									message += `<br><small style='color: #dc3545;'>✗ Failed to re-submit SIs: ${item.failed_re_submit_sis.join(', ')}</small>`;
								}
								
								message += "</div>";
							});
							message += "</div>";
						}
						
						// Show skipped BOMs
						if (results.skipped_list && results.skipped_list.length > 0) {
							message += __("<b>Skipped BOMs ({0}):</b><br>", [results.skipped_list.length]);
							message += "<div style='max-height: 200px; overflow-y: auto; border: 1px solid #d1d8dd; padding: 10px; margin: 10px 0;'>";
							results.skipped_list.forEach(function(item) {
								message += `<div style='padding: 5px 0; border-bottom: 1px solid #e7eef5;'>`;
								message += `<strong>${item.bom}</strong> (Item: ${item.item || 'N/A'})<br>`;
								message += `<small style='color: #6c7b7f;'>Reason: ${item.reason}</small>`;
								message += "</div>";
							});
							message += "</div>";
						}
						
						// Show errors
						if (results.errors && results.errors.length > 0) {
							message += __("<b>Failed BOMs ({0}):</b><br>", [results.errors.length]);
							message += "<div style='max-height: 150px; overflow-y: auto; border: 1px solid #d1d8dd; padding: 10px; margin: 10px 0;'>";
							results.errors.slice(0, 20).forEach(function(error) {
								message += `<div style='padding: 5px 0; color: #d9534f;'>• ${error}</div>`;
							});
							if (results.errors.length > 20) {
								message += __("<div style='color: #6c7b7f;'>... and {0} more errors. Check Error Log for details.</div>", [results.errors.length - 20]);
							}
							message += "</div>";
						}
						
						// Add note about console
						message += __("<br><small style='color: #6c7b7f;'>💡 Check browser console (F12) for complete detailed results</small>");
						
						frappe.msgprint({
							title: __("BOM Solver Results"),
							message: message,
							indicator: results.failed > 0 ? "orange" : (results.skipped > 0 ? "blue" : "green"),
							width: 800
						});
						
						// Show detailed results in console
						console.log("=== BOM Solver Detailed Results ===");
						console.log("Summary:", {
							total: results.total_boms,
							processed: results.processed,
							skipped: results.skipped,
							failed: results.failed
						});
						console.log("Processed BOMs:", results.processed_list);
						console.log("Skipped BOMs:", results.skipped_list);
						if (results.errors && results.errors.length > 0) {
							console.log("Failed BOMs:", results.errors);
						}
						console.log("Full Results:", results);
					}
				},
				error: function(r) {
					frappe.msgprint({
						title: __("Error"),
						message: __("An error occurred while processing BOMs. Check Error Log for details."),
						indicator: "red"
					});
				}
			});
		},
		function() {
			// User cancelled
		}
	);
}
