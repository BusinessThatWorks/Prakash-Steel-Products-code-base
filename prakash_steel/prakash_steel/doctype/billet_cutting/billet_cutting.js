
// Copyright (c) 2025, beetashoke chakraborty and contributors
// For license information, please see license.txt

frappe.ui.form.on("Billet Cutting", {
    refresh(frm) {
        console.log("🔄 Billet Cutting refresh event triggered");
        console.log("📄 Document name:", frm.doc.name);
        console.log("📋 Production Plan:", frm.doc.production_plan);
        console.log("🔧 Billet Size:", frm.doc.billet_size);
        console.log("📊 Is new:", frm.is_new());
        console.log("💾 Is dirty:", frm.is_dirty());

        // Store if form was dirty before we do anything
        const was_dirty = frm.is_dirty();

        toggle_miss_billet_fields(frm);

        // Restore billet_size options if production_plan exists (even in draft state)
        if (frm.doc.production_plan) {
            console.log("✅ Production Plan exists, restoring billet_size options...");
            // Store current billet_size value to preserve it
            const current_billet_size = frm.doc.billet_size;
            console.log("💾 Preserving current billet_size value:", current_billet_size);

            // Load options from production plan
            load_billet_size_options_from_production_plan(frm, function () {
                // Restore the billet_size value if it was set
                if (current_billet_size) {
                    console.log("🔄 Restoring billet_size value:", current_billet_size);
                    // Use set_value to ensure it's set properly
                    frm.set_value("billet_size", current_billet_size);
                }
            });
        } else {
            console.log("❌ No Production Plan, skipping billet_size options restoration");
        }

        // Only calculate if form is dirty (user is editing) or if it's a new form
        // Don't recalculate on refresh after save to avoid making form dirty
        if (was_dirty || frm.is_new()) {
            calculate_fields(frm);
        } else {
            // Just refresh the display without recalculating (to avoid dirty state)
            frm.refresh_field("cutting_weight_per_pcs");
            frm.refresh_field("total_raw_material_pcs");

            // Ensure form stays clean after refresh
            if (!was_dirty && frm.is_dirty && frm.is_dirty()) {
                // Check if only calculated fields were modified
                const modified_fields = frm._dirty_fields || [];
                const only_calculated = modified_fields.every(field =>
                    ['cutting_weight_per_pcs', 'total_raw_material_pcs', 'miss_billet_weight'].includes(field)
                );

                if (only_calculated) {
                    // Remove from dirty fields
                    modified_fields.forEach(field => {
                        const index = frm._dirty_fields.indexOf(field);
                        if (index > -1) {
                            frm._dirty_fields.splice(index, 1);
                        }
                    });

                    // Reset dirty state
                    setTimeout(function () {
                        if (frm.is_dirty && frm.is_dirty()) {
                            const has_other_changes = frm._dirty_fields && frm._dirty_fields.length > 0;
                            if (!has_other_changes) {
                                frm.dirty(false);
                            }
                        }
                    }, 100);
                }
            }
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
            // Clear billet_size options if production plan is cleared
            frm.set_df_property("billet_size", "options", "");
            frm.refresh_field("billet_size");
            return;
        }

        console.log("✅ Selected Production Plan ID:", frm.doc.production_plan);

        // Store current billet_size value to preserve it if it's still valid
        const current_billet_size = frm.doc.billet_size;
        console.log("💾 Current billet_size value:", current_billet_size);

        // Load options from production plan
        load_billet_size_options_from_production_plan(frm, function () {
            // Try to restore the billet_size value if it's still in the new options
            if (current_billet_size) {
                console.log("🔄 Attempting to restore billet_size value:", current_billet_size);
                // The value will be preserved automatically if it's in the options
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
    },

    after_save: function (frm) {
        // Ensure form is clean after save
        setTimeout(function () {
            if (frm.is_dirty && frm.is_dirty()) {
                console.log("⚠️ Form is dirty after save, cleaning up...");
                // Clear any dirty fields that might have been set
                if (frm._dirty_fields) {
                    frm._dirty_fields = [];
                }
                frm.dirty(false);
            }
        }, 200);
    }
});

function calculate_fields(frm) {
    const was_dirty = frm.is_dirty();
    let billet_weight = flt(frm.doc.billet_weight) || 0;
    let total_billet_cutting_pcs = flt(frm.doc.total_billet_cutting_pcs) || 0;
    let miss_billet_pcs = flt(frm.doc.miss_billet_pcs) || 0;

    // cutting_weight_per_pcs
    let new_cutting_weight = 0;
    if (billet_weight && total_billet_cutting_pcs) {
        new_cutting_weight = billet_weight / total_billet_cutting_pcs;
    }

    const current_cutting_weight = flt(frm.doc.cutting_weight_per_pcs) || 0;

    // Only update if value actually changed
    if (Math.abs(new_cutting_weight - current_cutting_weight) > 0.01) {
        if (!was_dirty) {
            // Update using locals to avoid dirty state
            const doc = locals[frm.doctype] && locals[frm.doctype][frm.docname];
            if (doc) {
                doc.cutting_weight_per_pcs = new_cutting_weight;
            }
            frm.doc.cutting_weight_per_pcs = new_cutting_weight;
            frm.refresh_field("cutting_weight_per_pcs");

            // Remove from dirty fields if it was added
            if (frm._dirty_fields) {
                const index = frm._dirty_fields.indexOf('cutting_weight_per_pcs');
                if (index > -1) {
                    frm._dirty_fields.splice(index, 1);
                }
            }
        } else {
            frm.set_value("cutting_weight_per_pcs", new_cutting_weight);
        }
    }

    // total_raw_material_pcs
    const new_total = total_billet_cutting_pcs + miss_billet_pcs;
    const current_total = flt(frm.doc.total_raw_material_pcs) || 0;

    // Only update if value actually changed
    if (Math.abs(new_total - current_total) > 0.01) {
        if (!was_dirty) {
            // Update using locals to avoid dirty state
            const doc = locals[frm.doctype] && locals[frm.doctype][frm.docname];
            if (doc) {
                doc.total_raw_material_pcs = new_total;
            }
            frm.doc.total_raw_material_pcs = new_total;
            frm.refresh_field("total_raw_material_pcs");

            // Remove from dirty fields if it was added
            if (frm._dirty_fields) {
                const index = frm._dirty_fields.indexOf('total_raw_material_pcs');
                if (index > -1) {
                    frm._dirty_fields.splice(index, 1);
                }
            }
        } else {
            frm.set_value("total_raw_material_pcs", new_total);
        }
    }

    // Reset dirty state if form wasn't dirty before and no other changes
    if (!was_dirty) {
        setTimeout(function () {
            if (frm.is_dirty && frm.is_dirty()) {
                const has_other_changes = frm._dirty_fields && frm._dirty_fields.length > 0;
                if (!has_other_changes) {
                    frm.dirty(false);
                }
            }
        }, 100);
    }
}

function load_billet_size_options_from_production_plan(frm, callback) {
    console.log("📥 load_billet_size_options_from_production_plan called");
    console.log("📋 Production Plan:", frm.doc.production_plan);

    if (!frm.doc.production_plan) {
        console.log("❌ No Production Plan provided");
        if (callback) callback();
        return;
    }

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
                if (callback) callback();
                return;
            }

            let pp = r.message;
            console.log("📄 Production Plan Doc:", pp);

            if (!pp.mr_items) {
                console.log("❌ mr_items not found in Production Plan");
                if (callback) callback();
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
                if (callback) callback();
                return;
            }

            // Remove duplicates
            item_codes = [...new Set(item_codes)];
            console.log("🧹 Unique item_codes:", item_codes);

            // Set the options
            frm.set_df_property(
                "billet_size",
                "options",
                item_codes.join("\n")
            );

            console.log("✅ billet_size options set");

            frm.refresh_field("billet_size");

            if (callback) {
                console.log("✅ Calling callback function");
                callback();
            }
        }
    });
}

function toggle_miss_billet_fields(frm) {
    const was_dirty = frm.is_dirty();
    const miss_billet_pcs = flt(frm.doc.miss_billet_pcs) || 0;

    if (miss_billet_pcs > 0) {
        frm.set_df_property("miss_billet_weight", "hidden", 0);
        frm.set_df_property("miss_billet_weight", "reqd", 1);
    } else {
        frm.set_df_property("miss_billet_weight", "hidden", 1);
        frm.set_df_property("miss_billet_weight", "reqd", 0);

        // Clear value using locals to avoid dirty state if form wasn't dirty
        if (!was_dirty) {
            const doc = locals[frm.doctype] && locals[frm.doctype][frm.docname];
            if (doc) {
                doc.miss_billet_weight = "";
            }
            frm.doc.miss_billet_weight = "";
            frm.refresh_field("miss_billet_weight");

            // Remove from dirty fields if it was added
            if (frm._dirty_fields) {
                const index = frm._dirty_fields.indexOf('miss_billet_weight');
                if (index > -1) {
                    frm._dirty_fields.splice(index, 1);
                }
            }
        } else {
            frm.set_value("miss_billet_weight", ""); // Use set_value if form was already dirty
        }
    }
}