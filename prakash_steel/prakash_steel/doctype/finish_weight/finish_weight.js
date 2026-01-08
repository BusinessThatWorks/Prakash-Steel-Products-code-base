frappe.ui.form.on("Finish Weight", {
    billet_cutting_id: function(frm) {
        console.log("Finish Weight - billet_cutting_id changed:", frm.doc.billet_cutting_id);
        calculate_finish_pcs_from_hourly_production(frm).then(function() {
            // After finish_pcs is calculated, calculate fg_per_pcs_weight if finish_weight exists
            if (frm.doc.finish_weight && frm.doc.finish_pcs && frm.doc.finish_pcs > 0) {
                let fg_per_pcs_weight = frm.doc.finish_weight / frm.doc.finish_pcs;
                console.log("Calculating fg_per_pcs_weight after billet_cutting_id change:", fg_per_pcs_weight);
                frm.set_value("fg_per_pcs_weight", fg_per_pcs_weight);
            }
        });
    },
    finish_weight: function(frm) {
        console.log("=".repeat(50));
        console.log("Finish Weight - finish_weight changed:", frm.doc.finish_weight);
        console.log("Calling calculate_finish_pcs_from_hourly_production...");
        
        // Call calculate_finish_pcs_from_hourly_production to get finish_pcs
        calculate_finish_pcs_from_hourly_production(frm).then(function() {
            console.log("calculate_finish_pcs_from_hourly_production completed");
            console.log("Finish Pcs:", frm.doc.finish_pcs);
            console.log("Finish Weight:", frm.doc.finish_weight);
            
            // Calculate fg_per_pcs_weight = finish_weight / finish_pcs
            if (frm.doc.finish_weight && frm.doc.finish_pcs && frm.doc.finish_pcs > 0) {
                let fg_per_pcs_weight = frm.doc.finish_weight / frm.doc.finish_pcs;
                console.log("Calculating fg_per_pcs_weight:", fg_per_pcs_weight);
                frm.set_value("fg_per_pcs_weight", fg_per_pcs_weight);
            } else {
                console.log("Cannot calculate fg_per_pcs_weight - missing values or finish_pcs is 0");
                frm.set_value("fg_per_pcs_weight", 0);
            }
            console.log("=".repeat(50));
        }).catch(function(error) {
            console.error("Error in finish_weight handler:", error);
            console.log("=".repeat(50));
        });
    },
    finish_pcs: function(frm) {
        console.log("Finish Weight - finish_pcs changed:", frm.doc.finish_pcs);
        // Calculate fg_per_pcs_weight = finish_weight / finish_pcs
        if (frm.doc.finish_weight && frm.doc.finish_pcs && frm.doc.finish_pcs > 0) {
            let fg_per_pcs_weight = frm.doc.finish_weight / frm.doc.finish_pcs;
            console.log("Calculating fg_per_pcs_weight after finish_pcs change:", fg_per_pcs_weight);
            frm.set_value("fg_per_pcs_weight", fg_per_pcs_weight);
        } else {
            console.log("Cannot calculate fg_per_pcs_weight - missing finish_weight or finish_pcs is 0");
            frm.set_value("fg_per_pcs_weight", 0);
        }
    },
    refresh: function(frm) {
        console.log("Finish Weight - refresh called");
        console.log("Finish Weight Document:", frm.doc.name);
        console.log("Item Code:", frm.doc.item_code);
        console.log("Finish Weight:", frm.doc.finish_weight);
        console.log("FG Target Warehouse:", frm.doc.fg_target_warehouse);
        console.log("FG Per Pcs Weight:", frm.doc.fg_per_pcs_weight);
        // Recalculate on refresh if billet_cutting_id is already set
        if (frm.doc.billet_cutting_id) {
            calculate_finish_pcs_from_hourly_production(frm).then(function() {
                // After finish_pcs is calculated, calculate fg_per_pcs_weight if finish_weight exists
                if (frm.doc.finish_weight && frm.doc.finish_pcs && frm.doc.finish_pcs > 0) {
                    let fg_per_pcs_weight = frm.doc.finish_weight / frm.doc.finish_pcs;
                    console.log("Calculating fg_per_pcs_weight on refresh:", fg_per_pcs_weight);
                    frm.set_value("fg_per_pcs_weight", fg_per_pcs_weight);
                }
            });
        } else if (frm.doc.finish_weight && frm.doc.finish_pcs && frm.doc.finish_pcs > 0) {
            // If no billet_cutting_id but we have values, just calculate fg_per_pcs_weight
            let fg_per_pcs_weight = frm.doc.finish_weight / frm.doc.finish_pcs;
            console.log("Calculating fg_per_pcs_weight on refresh (no billet_cutting_id):", fg_per_pcs_weight);
            frm.set_value("fg_per_pcs_weight", fg_per_pcs_weight);
        }
    },
    before_save: function(frm) {
        console.log("Finish Weight - before_save called");
        console.log("Item Code:", frm.doc.item_code);
        console.log("Finish Weight:", frm.doc.finish_weight);
        console.log("FG Target Warehouse:", frm.doc.fg_target_warehouse);
    },
    validate: function(frm) {
        console.log("Finish Weight - validate called");
        console.log("Item Code:", frm.doc.item_code);
        console.log("Finish Weight:", frm.doc.finish_weight);
        console.log("FG Target Warehouse:", frm.doc.fg_target_warehouse);
    },
    on_submit: function(frm) {
        console.log("=".repeat(50));
        console.log("Finish Weight - on_submit (client-side) called");
        console.log("Finish Weight Document:", frm.doc.name);
        console.log("Item Code:", frm.doc.item_code);
        console.log("Finish Weight (qty):", frm.doc.finish_weight);
        console.log("FG Target Warehouse:", frm.doc.fg_target_warehouse);
        console.log("Posting Date:", frm.doc.posting_date);
        console.log("=".repeat(50));
    },
    after_submit: function(frm) {
        console.log("=".repeat(50));
        console.log("Finish Weight - after_submit (client-side) called");
        console.log("Finish Weight Document:", frm.doc.name);
        console.log("=".repeat(50));
    }
});

frappe.ui.form.on("Finish Weight Item", {
    finish_weight: function(frm, cdt, cdn) {
        calculate_fg_weight(frm, cdt, cdn);
    },
    finish_pcs: function(frm, cdt, cdn) {
        calculate_fg_weight(frm, cdt, cdn);
    }
});

function calculate_finish_pcs_from_hourly_production(frm) {
    console.log("calculate_finish_pcs_from_hourly_production called");
    console.log("billet_cutting_id:", frm.doc.billet_cutting_id);
    
    if (!frm.doc.billet_cutting_id) {
        console.log("No billet_cutting_id, setting finish_pcs to 0");
        frm.set_value("finish_pcs", 0);
        return Promise.resolve();
    }

    return frappe.db.get_list("Hourly Production", {
        filters: {
            billet_cutting_id: frm.doc.billet_cutting_id,
            docstatus: ["<", 2] // Include submitted and draft documents
        },
        fields: ["finish_item_pcs"]
    }).then(function(docs) {
        console.log("Hourly Production docs found:", docs);
        let total_finish_pcs = 0;
        if (docs && docs.length > 0) {
            docs.forEach(function(doc) {
                if (doc.finish_item_pcs) {
                    total_finish_pcs += parseInt(doc.finish_item_pcs) || 0;
                }
            });
        }
        console.log("Total finish_pcs calculated:", total_finish_pcs);
        frm.set_value("finish_pcs", total_finish_pcs);
        return Promise.resolve();
    }).catch(function(error) {
        console.error("Error calculating finish_pcs:", error);
        frm.set_value("finish_pcs", 0);
        return Promise.reject(error);
    });
}

function calculate_fg_weight(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    if (row.finish_weight && row.finish_pcs) {
        frappe.model.set_value(cdt, cdn, "fg_per_pcs_weight", row.finish_weight / row.finish_pcs);
    } else {
        frappe.model.set_value(cdt, cdn, "fg_per_pcs_weight", 0);
    }
}
