// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.ui.form.on("Billet Cutting", {
    refresh(frm) {
        toggle_miss_billet_fields(frm);
        
        // Only calculate if form is dirty (user is editing) or if it's a new form
        // Don't recalculate on refresh after save to avoid making form dirty
        if (frm.is_dirty() || frm.is_new()) {
            calculate_fields(frm);
        } else {
            // Just refresh the display without recalculating (to avoid dirty state)
            frm.refresh_field("cutting_weight_per_pcs");
            frm.refresh_field("total_raw_material_pcs");
        }
    },

    billet_weight(frm) {
        calculate_fields(frm);
    },

    total_billet_cutting_pcs(frm) {
        calculate_fields(frm);
    },

    miss_billet_pcs(frm) {
        toggle_miss_billet_fields(frm);
        calculate_fields(frm);
    },

    production_plan: function (frm) {
        console.log("🔥 production_plan event triggered");

        if (!frm.doc.production_plan) {
            console.log("❌ No Production Plan selected");
            return;
        }

        console.log("✅ Selected Production Plan ID:", frm.doc.production_plan);

        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Production Plan",
                name: frm.doc.production_plan
            },
            callback: function (r) {
                console.log("📦 Full frappe.call response:", r);

                if (!r.message) {
                    console.log("❌ No document returned");
                    return;
                }

                let pp = r.message;
                console.log("📄 Production Plan Doc:", pp);

                if (!pp.mr_items) {
                    console.log("❌ mr_items not found in Production Plan");
                    return;
                }

                console.log("📋 mr_items rows count:", pp.mr_items.length);

                let item_codes = [];

                pp.mr_items.forEach((row, index) => {
                    console.log(`➡️ Row ${index}:`, row);

                    if (row.item_code) {
                        item_codes.push(row.item_code);
                        console.log("➕ item_code added:", row.item_code);
                    } else {
                        console.log("⚠️ item_code missing in row", index);
                    }
                });

                console.log("🧾 Final item_codes array:", item_codes);

                if (item_codes.length === 0) {
                    console.log("❌ No item codes collected");
                    return;
                }

                // Remove duplicates
                item_codes = [...new Set(item_codes)];
                console.log("🧹 Unique item_codes:", item_codes);

                frm.set_df_property(
                    "billet_size",
                    "options",
                    item_codes.join("\n")
                );

                console.log("✅ billet_size options set");

                frm.refresh_field("billet_size");
            }
        });
    },

    before_save: function (frm) {
        // Ensure calculations are correct before save
        // Update directly in doc to avoid marking as dirty (since we're about to save anyway)
        let billet_weight = flt(frm.doc.billet_weight) || 0;
        let total_billet_cutting_pcs = flt(frm.doc.total_billet_cutting_pcs) || 0;
        let miss_billet_pcs = flt(frm.doc.miss_billet_pcs) || 0;

        // cutting_weight_per_pcs
        if (billet_weight && total_billet_cutting_pcs) {
            frm.doc.cutting_weight_per_pcs = billet_weight / total_billet_cutting_pcs;
        } else {
            frm.doc.cutting_weight_per_pcs = 0;
        }

        // total_raw_material_pcs
        frm.doc.total_raw_material_pcs = total_billet_cutting_pcs + miss_billet_pcs;
    }
});

function calculate_fields(frm) {
    let billet_weight = flt(frm.doc.billet_weight) || 0;
    let total_billet_cutting_pcs = flt(frm.doc.total_billet_cutting_pcs) || 0;
    let miss_billet_pcs = flt(frm.doc.miss_billet_pcs) || 0;

    // cutting_weight_per_pcs
    if (billet_weight && total_billet_cutting_pcs) {
        const new_value = billet_weight / total_billet_cutting_pcs;
        const current_value = flt(frm.doc.cutting_weight_per_pcs) || 0;
        
        // Only update if value actually changed (to avoid unnecessary dirty state)
        if (Math.abs(new_value - current_value) > 0.01) {
            frm.set_value("cutting_weight_per_pcs", new_value);
        }
    } else {
        const current_value = flt(frm.doc.cutting_weight_per_pcs) || 0;
        if (current_value !== 0) {
            frm.set_value("cutting_weight_per_pcs", 0);
        }
    }

    // total_raw_material_pcs
    const new_total = total_billet_cutting_pcs + miss_billet_pcs;
    const current_total = flt(frm.doc.total_raw_material_pcs) || 0;
    
    // Only update if value actually changed (to avoid unnecessary dirty state)
    if (Math.abs(new_total - current_total) > 0.01) {
        frm.set_value("total_raw_material_pcs", new_total);
    }
}

function toggle_miss_billet_fields(frm) {
    if (flt(frm.doc.miss_billet_pcs) > 0) {
        frm.set_df_property("miss_billet_weight", "hidden", 0);
        frm.set_df_property("miss_billet_weight", "reqd", 1);
    } else {
        frm.set_df_property("miss_billet_weight", "hidden", 1);
        frm.set_df_property("miss_billet_weight", "reqd", 0);
        frm.set_value("miss_billet_weight", ""); // clear if hidden
    }
}