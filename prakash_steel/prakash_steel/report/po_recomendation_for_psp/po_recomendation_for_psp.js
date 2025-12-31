// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.query_reports["PO Recomendation for PSP"] = {
	filters: [
		{
			fieldname: "sku_type",
			label: __("SKU Type"),
			fieldtype: "MultiSelectList",
			width: "80",
			reqd: 0,
			get_data: function (txt) {
				let sku_types = [
					"BBMTA",
					"RBMTA",
					"BOTA",
					"PTA",
					"TRMTA",
				];
				let options = [];
				for (let sku of sku_types) {
					if (!txt || sku.toLowerCase().includes(txt.toLowerCase())) {
						options.push({
							value: sku,
							label: __(sku),
							description: "",
						});
					}
				}
				return options;
			},
		},
		{
			fieldname: "item_code",
			label: __("Item Code"),
			fieldtype: "Link",
			options: "Item",
			width: "120",
			reqd: 0,
		},
	],
	
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		// Background colors for On Hand Colour (BLACK / RED / YELLOW / GREEN / WHITE)
		if (column.fieldname === "on_hand_colour" && data && data.on_hand_colour) {
			let colourRaw = data.on_hand_colour || "";
			let colour = colourRaw.toLowerCase();

			// If empty or unknown, just return default
			if (!colour) {
				return value;
			}

			let bg = "";
			let textColor = "#000000";
			let colourText = colourRaw.toUpperCase();

			if (colour === "black") {
				bg = "#000000";
				textColor = "#ffffff";
			} else if (colour === "white") {
				bg = "#ffffff";
				textColor = "#000000";
			} else if (colour === "green") {
				bg = "#4dff88"; // Green
				textColor = "#000000";
			} else if (colour === "yellow") {
				bg = "#ffff99"; // Yellow
				textColor = "#000000";
			} else if (colour === "red") {
				bg = "#ff9999"; // Red
				textColor = "#000000";
			}

			if (bg) {
				return `<div style="
					background-color:${bg};
					border-radius:0px;
					padding:4px;
					text-align:center;
					font-weight:bold;
					color:${textColor};
				">
					${colourText}
				</div>`;
			}
		}

		return value;
	},
	
	onload: function(report) {
		// HIDDEN: Add button to debug PO calculation for a specific item
		/*
		report.page.add_inner_button(__("Debug PO Calculation"), function() {
			frappe.prompt([
				{
					fieldname: "item_code",
					label: __("Item Code"),
					fieldtype: "Link",
					options: "Item",
					reqd: 1
				}
			], function(values) {
				var filters = report.get_filter_values();
				frappe.call({
					method: "prakash_steel.prakash_steel.report.po_recomendation_for_psp.po_recomendation_for_psp.debug_po_calculation",
					args: {
						item_code: values.item_code,
						filters: filters
					},
					callback: function(r) {
						if (r.message) {
							display_po_debug_info(r.message);
						}
					}
				});
			}, __("Enter Item Code"), __("Show Calculation"));
		});
		*/
		
		// HIDDEN: Add button to create Material Request for selected item
		/*
		report.page.add_inner_button(__("Create Material Request"), function() {
			frappe.prompt([
				{
					fieldname: "item_code",
					label: __("Item Code"),
					fieldtype: "Link",
					options: "Item",
					reqd: 1
				},
				{
					fieldname: "qty",
					label: __("Quantity (Net PO Recommendation)"),
					fieldtype: "Float",
					reqd: 1
				}
			], function(values) {
				if (!values.item_code || !values.qty || values.qty <= 0) {
					frappe.msgprint(__("Item Code and Quantity are required. Quantity must be greater than 0."));
					return;
				}
				
				frappe.confirm(
					__("Create Material Request for {0} with quantity {1}?", [values.item_code, values.qty]),
					function() {
						// Yes
						frappe.call({
							method: "prakash_steel.prakash_steel.report.po_recomendation_for_psp.po_recomendation_for_psp.create_material_request",
							args: {
								item_code: values.item_code,
								qty: values.qty
							},
							callback: function(r) {
								if (r.message && r.message.error) {
									frappe.msgprint(__("Error: {0}", [r.message.error]));
								} else if (r.message && r.message.material_request) {
									frappe.msgprint({
										title: __("Success"),
										message: __("Material Request {0} created and submitted successfully", [r.message.material_request]),
										indicator: "green"
									});
									report.refresh();
								}
							},
							error: function(r) {
								frappe.msgprint(__("Error creating Material Request"));
							}
						});
					},
					function() {
						// No
					}
				);
			}, __("Create Material Request"), __("Create"));
		});
		*/
		
		// HIDDEN: Add button to create Material Request automatically for all items with net_po_recommendation > 0
		/*
		report.page.add_inner_button(__("Create Material Request Automatically"), function() {
			frappe.confirm(
				__("This will create Material Requests for all items with Net PO Recommendation > 0. Continue?"),
				function() {
					// Yes
					frappe.call({
						method: "prakash_steel.prakash_steel.report.po_recomendation_for_psp.po_recomendation_for_psp.create_material_requests_automatically",
						args: {
							filters: report.get_filter_values()
						},
						callback: function(r) {
							if (r.message && r.message.error) {
								frappe.msgprint(__("Error: {0}", [r.message.error]));
							} else if (r.message) {
								let success_count = r.message.success_count || 0;
								let error_count = r.message.error_count || 0;
								let material_requests = r.message.material_requests || [];
								let errors = r.message.errors || [];
								
								let message = __("Created {0} Material Request(s) successfully.", [success_count]);
								if (error_count > 0) {
									message += " " + __("{0} item(s) failed.", [error_count]);
									if (errors.length > 0) {
										message += "<br><br>" + __("Errors:") + "<br>";
										errors.forEach(function(err) {
											message += "- " + err + "<br>";
										});
										if (errors.length >= 10) {
											message += __("... and more errors (check logs for details)");
										}
									}
								}
								
								if (material_requests.length > 0) {
									message += "<br><br>" + __("Material Requests created:") + "<br>";
									material_requests.forEach(function(mr) {
										message += "- " + mr + "<br>";
									});
								}
								
								frappe.msgprint({
									title: success_count > 0 ? __("Success") : __("Completed"),
									message: message,
									indicator: success_count > 0 ? "green" : "orange"
								});
								report.refresh();
							}
						},
						error: function(r) {
							frappe.msgprint(__("Error creating Material Requests"));
						}
					});
				},
				function() {
					// No
				}
			);
		});
		*/
	}
};

function display_po_debug_info(debug) {
	console.log("========================================");
	console.log("PO Recommendation Calculation Debug");
	console.log("========================================");
	
	if (debug.error) {
		console.error("Error:", debug.error);
		return;
	}
	
	console.log("Item Code:", debug.item_code);
	console.log("Item Name:", debug.item_name);
	console.log("Item Group:", debug.item_group);
	console.log("Is Raw Material:", debug.is_raw_material);
	console.log("Date Range:", debug.date_range);
	console.log("");
	console.log("SALES ORDER ANALYSIS:");
	console.log("  Sales Order Qty:", debug.sales_order_qty);
	console.log("  Initial Stock:", debug.initial_stock);
	if (debug.stock_consumers && debug.stock_consumers.length > 0) {
		console.log("  Stock Consumed by Other Items:", debug.stock_consumed_by_others);
		console.log("  Items that consumed stock:");
		debug.stock_consumers.forEach(function(consumer) {
			console.log("    - " + consumer.item_code + ": consumed " + consumer.consumed_qty + " (BOM qty: " + consumer.bom_qty + ")");
		});
		console.log("  Available Stock (after other items' consumption):", debug.available_stock);
	} else {
		console.log("  Available Stock:", debug.available_stock);
	}
	if (debug.allocated_stock !== undefined) {
		console.log("  Allocated Stock:", debug.allocated_stock);
		console.log("  Remaining Stock After Allocation:", debug.remaining_stock_after_allocation);
	}
	console.log("  Calculation: max(0, " + debug.sales_order_qty + " - " + debug.available_stock + ") = " + debug.po_recommendation);
	console.log("  PO Recommendation:", debug.po_recommendation);
	console.log("");
	
	if (debug.po_recommendation > 0 && debug.bom_traversal && debug.bom_traversal.length > 0) {
		console.log("BOM TRAVERSAL (Items needed to make " + debug.item_code + "):");
		console.log("========================================");
		display_bom_debug(debug.bom_traversal, 0);
		console.log("");
	} else if (debug.po_recommendation > 0) {
		console.log("No BOM found for " + debug.item_code);
		console.log("");
	} else {
		console.log("Stock is sufficient. No production needed.");
		console.log("");
	}
	
	if (debug.all_po_recommendations) {
		console.log("ALL PO RECOMMENDATIONS (including child items):");
		console.log("========================================");
		for (var item in debug.all_po_recommendations) {
			if (debug.all_po_recommendations[item] > 0) {
				console.log("  " + item + ": " + debug.all_po_recommendations[item]);
			}
		}
		console.log("");
	}
	
	console.log("========================================");
}

function display_bom_debug(children, indent_level) {
	var indent = "";
	for (var i = 0; i < indent_level; i++) {
		indent += "  ";
	}
	
	children.forEach(function(child, idx) {
		console.log(indent + "[" + (idx + 1) + "] " + child.item_code + " (" + (child.item_name || "") + ")");
		console.log(indent + "  Item Group: " + (child.item_group || "N/A"));
		console.log(indent + "  Is Raw Material: " + child.is_raw_material);
		console.log(indent + "  BOM Qty: " + child.bom_qty + " (need " + child.bom_qty + " to make 1 parent)");
		console.log(indent + "  Parent Required Qty: " + child.parent_required_qty);
		console.log(indent + "  Calculation: " + child.calculation);
		console.log(indent + "  Child Required Qty: " + child.child_required_qty);
		console.log(indent + "  Available Stock: " + child.available_stock);
		if (child.allocated_stock !== undefined) {
			console.log(indent + "  Allocated Stock: " + child.allocated_stock);
			console.log(indent + "  Remaining Stock After Allocation: " + child.remaining_stock_after_allocation);
		}
		console.log(indent + "  PO Calculation: " + child.po_calculation);
		console.log(indent + "  PO Recommendation: " + child.po_recommendation);
		
		if (child.po_recommendation > 0 && child.children && child.children.length > 0) {
			console.log(indent + "  → Has BOM, traversing...");
			display_bom_debug(child.children, indent_level + 1);
		} else if (child.po_recommendation > 0 && !child.is_raw_material) {
			console.log(indent + "  → No BOM found");
		} else if (child.is_raw_material) {
			console.log(indent + "  → Raw Material (end of branch)");
		} else {
			console.log(indent + "  ✓ Stock sufficient");
		}
		console.log("");
	});
}
