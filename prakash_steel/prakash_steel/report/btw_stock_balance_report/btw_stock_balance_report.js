// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.query_reports["BTW Stock Balance Report"] = {
    "filters": [
        {
            "fieldname": "btw_item_code",
            "label": __("BTW Item Name"),
            "fieldtype": "Link",
            "options": "BTW Item Properties",
            "default": "",
            "reqd": 0
        },
        {
            "fieldname": "item_code",
            "label": __("Item Code"),
            "fieldtype": "Link",
            "options": "Item",
            "default": "",
            "reqd": 0
        },
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
            "default": "",
            "reqd": 0
        },
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "default": "",
            "reqd": 0
        },
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 0
        },
        {
            "fieldname": "include_zero_stock",
            "label": __("Include Zero Stock Items"),
            "fieldtype": "Check",
            "default": 0
        },
        {
            "fieldname": "color_filter",
            "label": __("Color"),
            "fieldtype": "Select",
            "options": ["", "Black", "White", "Green", "Yellow", "Red"],
            "width": "120"
        }
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "colour" && data) {
            // If colour is normal, show no color
            if (data.colour === "normal" || !data.colour) {
                return value;
            }

            let bg = "";
            let textColor = "black";
            let colourText = data.colour.charAt(0).toUpperCase() + data.colour.slice(1).toLowerCase();

            if (data.colour.toLowerCase() === "black") {
                bg = "#000000";
                textColor = "#FFFFFF";
            } else if (data.colour.toLowerCase() === "white") {
                bg = "#FFFFFF";
                textColor = "#000000";
            } else if (data.colour.toLowerCase() === "green") {
                bg = "#4dff88"; // Green
                textColor = "#000000";
            } else if (data.colour.toLowerCase() === "yellow") {
                bg = "#ffff99"; // Yellow
                textColor = "#000000";
            } else if (data.colour.toLowerCase() === "red") {
                bg = "#ff9999"; // Red
                textColor = "#000000";
            }

            if (bg) {
                return `<div style="background-color:${bg}; 
                                    border-radius:0px; 
                                    padding:4px; 
                                    text-align:center;
                                    font-weight:bold;
                                    color:${textColor};">
                        ${colourText}
                    </div>`;
            }
        }
        return value;
    }
};

