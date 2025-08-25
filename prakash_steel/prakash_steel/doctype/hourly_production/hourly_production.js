// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Hourly Production", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Hourly Production', {
    refresh(frm) {
        toggle_miss_roll_fields(frm);
        toggle_miss_ingot_fields(frm);
        calculate_total_pcs(frm);
    },
    miss_roll_pcs(frm) {
        toggle_miss_roll_fields(frm);
        calculate_total_pcs(frm);
    },
    miss_ingot_pcs(frm) {
        toggle_miss_ingot_fields(frm);
        calculate_total_pcs(frm);
    },
    finish_item_pcs(frm) {
        calculate_total_pcs(frm);
    }
});

function toggle_miss_roll_fields(frm) {
    if (frm.doc.miss_roll_pcs && frm.doc.miss_roll_pcs > 0) {
        frm.set_df_property("miss_roll_weight", "hidden", 0);
        frm.set_df_property("miss_roll_weight", "reqd", 1);

        frm.set_df_property("remarks_for_miss_roll", "hidden", 0);
        frm.set_df_property("remarks_for_miss_roll", "reqd", 1);
    } else {
        frm.set_df_property("miss_roll_weight", "hidden", 1);
        frm.set_df_property("miss_roll_weight", "reqd", 0);
        frm.set_value("miss_roll_weight", null);

        frm.set_df_property("remarks_for_miss_roll", "hidden", 1);
        frm.set_df_property("remarks_for_miss_roll", "reqd", 0);
        frm.set_value("remarks_for_miss_roll", null);
    }
}

function toggle_miss_ingot_fields(frm) {
    if (frm.doc.miss_ingot_pcs && frm.doc.miss_ingot_pcs > 0) {
        frm.set_df_property("miss_ingot__billet_weight", "hidden", 0);
        frm.set_df_property("miss_ingot__billet_weight", "reqd", 1);

        frm.set_df_property("reason_for_miss_ingot__billet", "hidden", 0);
        frm.set_df_property("reason_for_miss_ingot__billet", "reqd", 1);
    } else {
        frm.set_df_property("miss_ingot__billet_weight", "hidden", 1);
        frm.set_df_property("miss_ingot__billet_weight", "reqd", 0);
        frm.set_value("miss_ingot__billet_weight", null);

        frm.set_df_property("reason_for_miss_ingot__billet", "hidden", 1);
        frm.set_df_property("reason_for_miss_ingot__billet", "reqd", 0);
        frm.set_value("reason_for_miss_ingot__billet", null);
    }
}

function calculate_total_pcs(frm) {
    let finish = parseFloat(frm.doc.finish_item_pcs) || 0;
    let miss_roll = parseFloat(frm.doc.miss_roll_pcs) || 0;
    let miss_ingot = parseFloat(frm.doc.miss_ingot_pcs) || 0;

    let total = finish + miss_roll + miss_ingot;
    frm.set_value("total_pcs", total);
}
