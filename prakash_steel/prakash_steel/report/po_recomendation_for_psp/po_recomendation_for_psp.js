// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.query_reports["PO Recomendation for PSP"] = {
	filters: [
		{
			fieldname: "sku_type",
			label: __("SKU Type"),
			fieldtype: "MultiSelectList",
			width: "80",
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
			width: "80",
		},
	],

	onload: function (report) {
		// Hide buttons: Debug PO Calculation, Create Material Request, Create Material Request Automatically
		// These buttons are commented out but can be uncommented later if needed
		/*
		// Debug PO Calculation button
		report.page.add_inner_button(__("Debug PO Calculation"), function () {
			frappe.prompt(
				[
					{
						fieldname: "item_code",
						label: __("Item Code"),
						fieldtype: "Link",
						options: "Item",
						reqd: 1,
					},
				],
				function (values) {
					frappe.call({
						method: "prakash_steel.prakash_steel.report.po_recomendation_for_psp.po_recomendation_for_psp.debug_po_calculation",
						args: {
							item_code: values.item_code,
							filters: report.get_filter_values(),
						},
						callback: function (r) {
							if (r.message && r.message.error) {
								frappe.msgprint(__("Error: {0}", [r.message.error]));
							} else {
								console.log("Debug PO Calculation:", r.message);
								frappe.msgprint(__("Check browser console for details"));
							}
						},
					});
				},
				__("Debug PO Calculation"),
				__("Calculate")
			);
		});

		// Create Material Request button
		report.page.add_inner_button(__("Create Material Request"), function () {
			frappe.prompt(
				[
					{
						fieldname: "item_code",
						label: __("Item Code"),
						fieldtype: "Link",
						options: "Item",
						reqd: 1,
					},
					{
						fieldname: "qty",
						label: __("Quantity"),
						fieldtype: "Float",
						reqd: 1,
					},
				],
				function (values) {
					frappe.call({
						method: "prakash_steel.prakash_steel.report.po_recomendation_for_psp.po_recomendation_for_psp.create_material_request",
						args: {
							item_code: values.item_code,
							qty: values.qty,
						},
						callback: function (r) {
							if (r.message && r.message.error) {
								frappe.msgprint(__("Error: {0}", [r.message.error]));
							} else {
								frappe.msgprint(__("Material Request {0} created successfully", [r.message.material_request]));
								report.refresh();
							}
						},
					});
				},
				__("Create Material Request"),
				__("Create")
			);
		});

		// Create Material Request Automatically button
		report.page.add_inner_button(__("Create Material Request Automatically"), function () {
			frappe.confirm(
				__("This will create Material Requests for all items with Net Order Recommendation > 0. Continue?"),
				function () {
					// Show progress
					frappe.show_progress(__("Creating Material Requests"), 0, __("Processing..."));

					frappe.call({
						method: "prakash_steel.prakash_steel.report.po_recomendation_for_psp.po_recomendation_for_psp.create_material_requests_automatically",
						args: {
							filters: report.get_filter_values(),
						},
						callback: function (r) {
							frappe.hide_progress();
							if (r.message) {
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
								report.refresh();
							}
						},
					});
				}
			);
		});
		*/
	},

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		// Background colors for On Hand Colour status
		if (column.fieldname === "on_hand_colour" && data && data.on_hand_colour) {
			let colour = data.on_hand_colour;
			let bg = "";
			let textColor = "#000000";

			if (colour === "BLACK") {
				bg = "#000000";
				textColor = "#FFFFFF";
			} else if (colour === "RED") {
				bg = "#FF0000";
				textColor = "#FFFFFF";
			} else if (colour === "YELLOW") {
				bg = "#FFFF00";
				textColor = "#000000";
			} else if (colour === "GREEN") {
				bg = "#00FF00";
				textColor = "#000000";
			} else if (colour === "WHITE") {
				bg = "#FFFFFF";
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
					${colour}
				</div>`;
			}
		}

		// Background colors for Child full-kit status
		if (column.fieldname === "child_full_kit_status" && data && data.child_full_kit_status) {
			let fullkitRaw = data.child_full_kit_status || "";
			let fullkit = fullkitRaw.toLowerCase();

			if (!fullkit) {
				return value;
			}

			let bg = "";
			let textColor = "#000000";
			let fullkitText = fullkitRaw;

			if (fullkit === "full-kit") {
				bg = "#4dff88"; // Green
				textColor = "#000000";
			} else if (fullkit === "partial") {
				bg = "#ffff99"; // Yellow
				textColor = "#000000";
			} else if (fullkit === "pending") {
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
					${fullkitText}
				</div>`;
			}
		}

		// Background colors for Child WIP/Open PO full-kit status
		if (column.fieldname === "child_wip_open_po_full_kit_status" && data && data.child_wip_open_po_full_kit_status) {
			let fullkitRaw = data.child_wip_open_po_full_kit_status || "";
			let fullkit = fullkitRaw.toLowerCase();

			if (!fullkit) {
				return value;
			}

			let bg = "";
			let textColor = "#000000";
			let fullkitText = fullkitRaw;

			if (fullkit === "full-kit") {
				bg = "#4dff88"; // Green
				textColor = "#000000";
			} else if (fullkit === "partial") {
				bg = "#ffff99"; // Yellow
				textColor = "#000000";
			} else if (fullkit === "pending") {
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
					${fullkitText}
				</div>`;
			}
		}

		return value;
	},
};