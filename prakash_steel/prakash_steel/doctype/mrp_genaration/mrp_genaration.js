// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.ui.form.on("MRP Genaration", {
	refresh(frm) {
		// Add click handler for the MR Generation button field
		if (frm.fields_dict.mr_genaration) {
			frm.fields_dict.mr_genaration.$input.on("click", function () {
				generate_mrp_order_recommendations(frm);
			});
		}
	},
});

function generate_mrp_order_recommendations(frm) {
	// Show confirmation dialog
	frappe.confirm(
		__("This will generate Material Request order recommendations for all items (buffer and non-buffer) by traversing all BOMs. This may take some time. Continue?"),
		function () {
			// Show progress
			frappe.show_progress(__("Generating MRP Order Recommendations"), 0, __("Processing..."));

			// Call the API to calculate order recommendations
			frappe.call({
				method: "prakash_steel.prakash_steel.doctype.mrp_genaration.mrp_genaration.generate_mrp_order_recommendations",
				callback: function (r) {
					frappe.hide_progress();

					if (r.message) {
						if (r.message.error) {
							frappe.msgprint({
								title: __("Error"),
								message: __("Error: {0}", [r.message.error]),
								indicator: "red",
							});
						} else {
							// Show success message for calculation
							// Use net_order_recommendations instead of order_recommendations
							const net_order_recs = r.message.net_order_recommendations || {};
							const items_with_rec = Object.keys(net_order_recs).filter(
								item => net_order_recs[item] > 0
							).length;

							frappe.msgprint({
								title: __("Order Recommendations Calculated"),
								message: __(
									"Order recommendations calculated successfully!<br><br>" +
									"Items with net order recommendations > 0: {0}<br><br>" +
									"Check server logs and console for detailed breakdown.",
									[items_with_rec]
								),
								indicator: "green",
							});

							// Log to browser console as well - show net order recommendations
							console.log("MRP Net Order Recommendations:", r.message.net_order_recommendations);
							console.log("MRP Base Order Recommendations:", r.message.order_recommendations);

							// Log detailed breakdown for each item
							if (r.message.detailed_info) {
								console.log("\n" + "=".repeat(100));
								console.log("MRP DETAILED BREAKDOWN FOR ALL ITEMS");
								console.log("=".repeat(100));

								// Sort items by net_order_rec (descending)
								const detailedInfo = r.message.detailed_info;
								const sortedItems = Object.keys(detailedInfo).sort((a, b) => {
									const netRecA = detailedInfo[a].net_order_rec || 0;
									const netRecB = detailedInfo[b].net_order_rec || 0;
									if (netRecB !== netRecA) {
										return netRecB - netRecA;
									}
									return a.localeCompare(b);
								});

								// Show summary first
								console.log("\n" + "-".repeat(100));
								console.log("SUMMARY (Items with Net Order Recommendation > 0)");
								console.log("-".repeat(100));
								const itemsWithRec = sortedItems.filter(item => {
									const netRec = detailedInfo[item].net_order_rec || 0;
									return netRec > 0;
								});

								itemsWithRec.forEach(itemCode => {
									const info = detailedInfo[itemCode];
									const netRec = info.net_order_rec || 0;
									const finalRec = info.final_order_rec || 0;
									const bufferFlag = info.buffer_flag || "Unknown";
									console.log(`  ${itemCode} (${bufferFlag}): Net Order Rec = ${netRec} (Base: ${finalRec})`);
								});

								// Show detailed breakdown for all items
								console.log("\n" + "=".repeat(100));
								console.log("DETAILED BREAKDOWN FOR ALL ITEMS");
								console.log("=".repeat(100));

								sortedItems.forEach(itemCode => {
									const info = detailedInfo[itemCode];
									const breakdown = info.calculation_breakdown || "";

									if (breakdown && breakdown.trim()) {
										console.log(breakdown);
									} else {
										// Create a basic breakdown if not available
										const netRec = info.net_order_rec || 0;
										const finalRec = info.final_order_rec || 0;
										const bufferFlag = info.buffer_flag || "Unknown";
										const moq = info.moq || 0;
										const batchSize = info.batch_size || 0;

										console.log(`\n  Item: ${itemCode}`);
										console.log(`  Type: ${bufferFlag}`);
										console.log(`  Base Order Recommendation: ${finalRec}`);
										console.log(`  Net Order Recommendation: ${netRec}`);
										if (moq > 0) {
											console.log(`  MOQ: ${moq}`);
										}
										if (batchSize > 0) {
											console.log(`  Batch Size: ${batchSize}`);
										}
										console.log(`  Note: Detailed breakdown not available`);
									}
									console.log("-".repeat(100));
								});

								console.log("\n" + "=".repeat(100));
								console.log(`Total Items: ${sortedItems.length}`);
								console.log(`Items with Net Order Rec > 0: ${itemsWithRec.length}`);
								console.log("=".repeat(100));
							}

							// Now automatically create Material Requests
							create_material_requests_automatically(frm);
						}
					}
				},
				error: function (r) {
					frappe.hide_progress();
					frappe.msgprint({
						title: __("Error"),
						message: __("An error occurred while generating order recommendations."),
						indicator: "red",
					});
				},
			});
		}
	);
}

function create_material_requests_automatically(frm) {
	// Show progress
	frappe.show_progress(__("Creating Material Requests"), 0, __("Processing..."));

	// Call the API
	frappe.call({
		method: "prakash_steel.prakash_steel.doctype.mrp_genaration.mrp_genaration.create_material_requests_automatically",
		callback: function (r) {
			frappe.hide_progress();

			if (r.message) {
				if (r.message.error) {
					frappe.msgprint({
						title: __("Error"),
						message: __("Error: {0}", [r.message.error]),
						indicator: "red",
					});
				} else {
					// Show result message
					if (r.message.error_count > 0) {
						frappe.msgprint({
							title: __("Material Requests Created"),
							message: __(
								"Success: {0}<br>Failed: {1}<br><br>Errors:<br>{2}",
								[
									r.message.success_count,
									r.message.error_count,
									r.message.errors.join("<br>"),
								]
							),
							indicator: r.message.error_count > r.message.success_count ? "red" : "green",
						});
					} else {
						frappe.msgprint({
							title: __("Success"),
							message: __("Created {0} Material Request(s)", [r.message.success_count]),
							indicator: "green",
						});
					}

					// Log to browser console
					console.log("Material Requests Created:", r.message.material_requests);
				}
			}
		},
		error: function (r) {
			frappe.hide_progress();
			frappe.msgprint({
				title: __("Error"),
				message: __("An error occurred while creating Material Requests."),
				indicator: "red",
			});
		},
	});
}
