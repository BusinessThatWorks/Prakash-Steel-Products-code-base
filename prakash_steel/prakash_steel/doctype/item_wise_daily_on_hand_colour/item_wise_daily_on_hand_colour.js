// Copyright (c) 2026, beetashoke chakraborty and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Item wise Daily On Hand Colour", {
// 	refresh(frm) {

// 	},
// });

// Copyright (c) 2026, beetashoke chakraborty and contributors
// For license information, please see license.txt

function apply_on_hand_colour_styles(frm) {
    const grid_field = frm.fields_dict["item_wise_on_hand_colour"];
    if (!grid_field || !grid_field.grid || !grid_field.grid.grid_rows) {
        return;
    }

    (grid_field.grid.grid_rows || []).forEach((row) => {
        const colour = row.doc.on_hand_colour;
        if (!colour) return;

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

        if (!bg || !row.columns || !row.columns.on_hand_colour) return;

        const $cell = $(row.columns.on_hand_colour);
        $cell.css({
            "background-color": bg,
            "border-radius": "0px",
            padding: "4px",
            "text-align": "center",
            "font-weight": "bold",
            color: textColor,
        });
    });
}

frappe.ui.form.on("Item wise Daily On Hand Colour", {
	onload(frm) {
		// Periodically re-apply styles so pagination / grid redraws
		// always keep the colours, even when the grid DOM is rebuilt.
		if (!frm._on_hand_colour_interval) {
			frm._on_hand_colour_interval = setInterval(() => {
				if (frm && frm.doc) {
					apply_on_hand_colour_styles(frm);
				}
			}, 1000);
		}
	},
	refresh(frm) {
		apply_on_hand_colour_styles(frm);
	},
	onload_post_render(frm) {
		apply_on_hand_colour_styles(frm);
	},
});