// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Billet Cutting", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Billet Cutting', {
    refresh(frm) {
        // Run check on refresh 
        toggle_weight_field(frm);
    },
    miss_billet_pcs(frm) {
        // Run check whenever pcs changes
        toggle_weight_field(frm);
    }
});

function toggle_weight_field(frm) {
    let pcs = frm.doc.miss_billet_pcs;

    if (pcs && pcs > 0) {
        frm.set_df_property("miss_billet_weight", "reqd", 1);
        frm.set_df_property("miss_billet_weight", "hidden", 0);
    } else {
        frm.set_df_property("miss_billet_weight", "reqd", 0);
        frm.set_df_property("miss_billet_weight", "hidden", 1);
        frm.set_value("miss_billet_weight", null);
    }
}
