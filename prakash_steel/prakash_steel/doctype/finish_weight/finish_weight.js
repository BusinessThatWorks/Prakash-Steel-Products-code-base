frappe.ui.form.on("Finish Weight", {
    billet_cutting_id: function(frm) {
        console.log("Finish Weight - billet_cutting_id changed:", frm.doc.billet_cutting_id);
        calculate_finish_pcs_from_hourly_production(frm).then(function() {
            // After finish_pcs is calculated, calculate fg_per_pcs_weight if finish_weight exists
            if (frm.doc.finish_weight && frm.doc.finish_pcs && frm.doc.finish_pcs > 0) {
                let fg_per_pcs_weight = frm.doc.finish_weight / frm.doc.finish_pcs;
                // Round to 2 decimal places
                fg_per_pcs_weight = Math.round(fg_per_pcs_weight * 100) / 100;
                console.log("Calculating fg_per_pcs_weight after billet_cutting_id change - Original:", frm.doc.finish_weight / frm.doc.finish_pcs, "Rounded to 2 decimals:", fg_per_pcs_weight);
                frm.set_value("fg_per_pcs_weight", fg_per_pcs_weight);
            }
            // Fetch colour_code based on grade
            fetch_colour_code_from_grade(frm);
        });
    },
    item_code: function(frm) {
        console.log("Finish Weight - item_code changed:", frm.doc.item_code);
        // Wait for grade to be fetched from item_code, then fetch colour_code
        setTimeout(function() {
            fetch_colour_code_from_grade(frm);
        }, 500);
    },
    grade: function(frm) {
        console.log("Finish Weight - grade changed:", frm.doc.grade);
        fetch_colour_code_from_grade(frm);
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
                // Round to 2 decimal places
                fg_per_pcs_weight = Math.round(fg_per_pcs_weight * 100) / 100;
                console.log("Calculating fg_per_pcs_weight - Original:", frm.doc.finish_weight / frm.doc.finish_pcs, "Rounded to 2 decimals:", fg_per_pcs_weight);
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
            // Round to 2 decimal places
            fg_per_pcs_weight = Math.round(fg_per_pcs_weight * 100) / 100;
            console.log("Calculating fg_per_pcs_weight after finish_pcs change - Original:", frm.doc.finish_weight / frm.doc.finish_pcs, "Rounded to 2 decimals:", fg_per_pcs_weight);
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
                    // Round to 2 decimal places
                    fg_per_pcs_weight = Math.round(fg_per_pcs_weight * 100) / 100;
                    console.log("Calculating fg_per_pcs_weight on refresh - Original:", frm.doc.finish_weight / frm.doc.finish_pcs, "Rounded to 2 decimals:", fg_per_pcs_weight);
                    frm.set_value("fg_per_pcs_weight", fg_per_pcs_weight);
                }
            });
        } else if (frm.doc.finish_weight && frm.doc.finish_pcs && frm.doc.finish_pcs > 0) {
            // If no billet_cutting_id but we have values, just calculate fg_per_pcs_weight
            let fg_per_pcs_weight = frm.doc.finish_weight / frm.doc.finish_pcs;
            // Round to 2 decimal places
            fg_per_pcs_weight = Math.round(fg_per_pcs_weight * 100) / 100;
            console.log("Calculating fg_per_pcs_weight on refresh (no billet_cutting_id) - Original:", frm.doc.finish_weight / frm.doc.finish_pcs, "Rounded to 2 decimals:", fg_per_pcs_weight);
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
        console.log("No billet_cutting_id, setting all totals to 0 and clearing item_code");
        frm.set_value("finish_pcs", 0);
        frm.set_value("total_miss_roll_pcs", 0);
        frm.set_value("total_miss_ingot_pcs", 0);
        frm.set_value("total_miss_roll_weight", 0);
        frm.set_value("total_miss_ingot_weight", 0);
        frm.set_value("item_code", "");
        return Promise.resolve();
    }

    // Query Hourly Production documents with the same billet_cutting_id
    return frappe.db.get_list("Hourly Production", {
        filters: {
            billet_cutting_id: frm.doc.billet_cutting_id,
            docstatus: ["<", 2] // Include submitted and draft documents
        },
        fields: ["finish_item_pcs", "finish_item", "name", "production_date", "time_from", "miss_roll_pcs", "miss_ingot_pcs", "miss_roll_weight", "miss_ingot__billet_weight"],
        order_by: "production_date asc, time_from asc, creation asc" // Order to get the first document chronologically
    }).then(function(docs) {
        console.log("=".repeat(50));
        console.log("Hourly Production docs found:", docs.length, "documents");
        console.log("Raw docs data:", JSON.stringify(docs, null, 2));
        let total_finish_pcs = 0;
        let total_miss_roll_pcs = 0;
        let total_miss_ingot_pcs = 0;
        let total_miss_roll_weight = 0;
        let total_miss_ingot_weight = 0;
        let first_doc_finish_item = null;
        
        if (docs && docs.length > 0) {
            // Get the first document's finish_item (first one in the ordered list)
            first_doc_finish_item = docs[0].finish_item;
            console.log("First Hourly Production doc:", docs[0].name);
            console.log("First Hourly Production doc finish_item:", first_doc_finish_item);
            console.log("First Hourly Production doc miss_roll_pcs:", docs[0].miss_roll_pcs, "Type:", typeof docs[0].miss_roll_pcs);
            
            // Calculate totals from all documents
            docs.forEach(function(doc, index) {
                console.log(`--- Processing doc ${index + 1}: ${doc.name} ---`);
                console.log(`  finish_item_pcs: ${doc.finish_item_pcs} (type: ${typeof doc.finish_item_pcs})`);
                console.log(`  miss_roll_pcs: ${doc.miss_roll_pcs} (type: ${typeof doc.miss_roll_pcs})`);
                console.log(`  miss_ingot_pcs: ${doc.miss_ingot_pcs} (type: ${typeof doc.miss_ingot_pcs})`);
                console.log(`  miss_roll_weight: ${doc.miss_roll_weight} (type: ${typeof doc.miss_roll_weight})`);
                console.log(`  miss_ingot__billet_weight: ${doc.miss_ingot__billet_weight} (type: ${typeof doc.miss_ingot__billet_weight})`);
                
                // Calculate finish_item_pcs
                if (doc.finish_item_pcs) {
                    let finish_pcs_value = parseInt(doc.finish_item_pcs) || 0;
                    total_finish_pcs += finish_pcs_value;
                    console.log(`  Added finish_item_pcs: ${finish_pcs_value}, Running total: ${total_finish_pcs}`);
                }
                
                // Calculate miss_roll_pcs
                if (doc.miss_roll_pcs !== null && doc.miss_roll_pcs !== undefined && doc.miss_roll_pcs !== "") {
                    let miss_roll_pcs_value = parseInt(doc.miss_roll_pcs) || 0;
                    total_miss_roll_pcs += miss_roll_pcs_value;
                    console.log(`  Added miss_roll_pcs: ${miss_roll_pcs_value}, Running total: ${total_miss_roll_pcs}`);
                } else {
                    console.log(`  Skipped miss_roll_pcs (null/undefined/empty): ${doc.miss_roll_pcs}`);
                }
                
                // Calculate miss_ingot_pcs
                if (doc.miss_ingot_pcs !== null && doc.miss_ingot_pcs !== undefined && doc.miss_ingot_pcs !== "") {
                    let miss_ingot_pcs_value = parseInt(doc.miss_ingot_pcs) || 0;
                    total_miss_ingot_pcs += miss_ingot_pcs_value;
                    console.log(`  Added miss_ingot_pcs: ${miss_ingot_pcs_value}, Running total: ${total_miss_ingot_pcs}`);
                } else {
                    console.log(`  Skipped miss_ingot_pcs (null/undefined/empty): ${doc.miss_ingot_pcs}`);
                }
                
                // Calculate miss_roll_weight
                if (doc.miss_roll_weight !== null && doc.miss_roll_weight !== undefined && doc.miss_roll_weight !== "") {
                    let miss_roll_weight_value = parseInt(doc.miss_roll_weight) || 0;
                    total_miss_roll_weight += miss_roll_weight_value;
                    console.log(`  Added miss_roll_weight: ${miss_roll_weight_value}, Running total: ${total_miss_roll_weight}`);
                } else {
                    console.log(`  Skipped miss_roll_weight (null/undefined/empty): ${doc.miss_roll_weight}`);
                }
                
                // Calculate miss_ingot__billet_weight
                if (doc.miss_ingot__billet_weight !== null && doc.miss_ingot__billet_weight !== undefined && doc.miss_ingot__billet_weight !== "") {
                    let miss_ingot_weight_value = parseInt(doc.miss_ingot__billet_weight) || 0;
                    total_miss_ingot_weight += miss_ingot_weight_value;
                    console.log(`  Added miss_ingot__billet_weight: ${miss_ingot_weight_value}, Running total: ${total_miss_ingot_weight}`);
                } else {
                    console.log(`  Skipped miss_ingot__billet_weight (null/undefined/empty): ${doc.miss_ingot__billet_weight}`);
                }
            });
            
            // Set item_code from the first document's finish_item
            if (first_doc_finish_item) {
                console.log("Setting item_code to first Hourly Production finish_item:", first_doc_finish_item);
                frm.set_value("item_code", first_doc_finish_item).then(function() {
                    // After item_code is set, wait for grade to be fetched, then fetch colour_code
                    setTimeout(function() {
                        fetch_colour_code_from_grade(frm);
                    }, 500);
                });
            } else {
                console.log("Warning: First Hourly Production document has no finish_item, clearing item_code");
                frm.set_value("item_code", "");
            }
        } else {
            console.log("No Hourly Production documents found for billet_cutting_id:", frm.doc.billet_cutting_id, "- clearing item_code");
            frm.set_value("item_code", "");
        }
        console.log("=".repeat(50));
        console.log("FINAL CALCULATIONS:");
        console.log("Total finish_pcs calculated:", total_finish_pcs);
        console.log("Total miss_roll_pcs calculated:", total_miss_roll_pcs);
        console.log("Total miss_ingot_pcs calculated:", total_miss_ingot_pcs);
        console.log("Total miss_roll_weight calculated:", total_miss_roll_weight);
        console.log("Total miss_ingot_weight calculated:", total_miss_ingot_weight);
        console.log("Setting finish_pcs to:", total_finish_pcs);
        console.log("Setting total_miss_roll_pcs to:", total_miss_roll_pcs);
        console.log("Setting total_miss_ingot_pcs to:", total_miss_ingot_pcs);
        console.log("Setting total_miss_roll_weight to:", total_miss_roll_weight);
        console.log("Setting total_miss_ingot_weight to:", total_miss_ingot_weight);
        console.log("=".repeat(50));
        frm.set_value("finish_pcs", total_finish_pcs);
        frm.set_value("total_miss_roll_pcs", total_miss_roll_pcs);
        frm.set_value("total_miss_ingot_pcs", total_miss_ingot_pcs);
        frm.set_value("total_miss_roll_weight", total_miss_roll_weight);
        frm.set_value("total_miss_ingot_weight", total_miss_ingot_weight);
        return Promise.resolve();
    }).catch(function(error) {
        console.error("Error calculating totals:", error);
        frm.set_value("finish_pcs", 0);
        frm.set_value("total_miss_roll_pcs", 0);
        frm.set_value("total_miss_ingot_pcs", 0);
        frm.set_value("total_miss_roll_weight", 0);
        frm.set_value("total_miss_ingot_weight", 0);
        frm.set_value("item_code", "");
        return Promise.reject(error);
    });
}

function calculate_fg_weight(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    if (row.finish_weight && row.finish_pcs) {
        let fg_per_pcs_weight = row.finish_weight / row.finish_pcs;
        // Round to 2 decimal places
        fg_per_pcs_weight = Math.round(fg_per_pcs_weight * 100) / 100;
        console.log("calculate_fg_weight - Original value:", row.finish_weight / row.finish_pcs, "Rounded to 2 decimals:", fg_per_pcs_weight);
        frappe.model.set_value(cdt, cdn, "fg_per_pcs_weight", fg_per_pcs_weight);
    } else {
        frappe.model.set_value(cdt, cdn, "fg_per_pcs_weight", 0);
    }
}

function fetch_colour_code_from_grade(frm) {
    console.log("fetch_colour_code_from_grade called");
    console.log("Current grade:", frm.doc.grade);
    
    if (!frm.doc.grade) {
        console.log("No grade found, cannot fetch colour_code");
        return Promise.resolve();
    }

    // Query Item Grade wise Colour Code doctype to find colour_code for this grade
    return frappe.db.get_list("Item Grade wise Colour Code", {
        filters: {
            item_grade: frm.doc.grade
        },
        fields: ["colour_code"],
        limit: 1
    }).then(function(docs) {
        if (docs && docs.length > 0) {
            let colour_code = docs[0].colour_code;
            console.log("Found colour_code for grade", frm.doc.grade, ":", colour_code);
            frm.set_value("colour_code", colour_code);
        } else {
            console.log("No Item Grade wise Colour Code found for grade:", frm.doc.grade);
        }
        return Promise.resolve();
    }).catch(function(error) {
        console.error("Error fetching colour_code from grade:", error);
        return Promise.reject(error);
    });
}
