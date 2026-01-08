frappe.ui.form.on("Finish Weight", {
    billet_cutting_id: function(frm) {
        calculate_finish_pcs_from_hourly_production(frm);
    },
    refresh: function(frm) {
        // Recalculate on refresh if billet_cutting_id is already set
        if (frm.doc.billet_cutting_id) {
            calculate_finish_pcs_from_hourly_production(frm);
        }
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
    if (!frm.doc.billet_cutting_id) {
        frm.set_value("finish_pcs", 0);
        return;
    }

    frappe.db.get_list("Hourly Production", {
        filters: {
            billet_cutting_id: frm.doc.billet_cutting_id,
            docstatus: ["<", 2] // Include submitted and draft documents
        },
        fields: ["finish_item_pcs"]
    }).then(function(docs) {
        let total_finish_pcs = 0;
        if (docs && docs.length > 0) {
            docs.forEach(function(doc) {
                if (doc.finish_item_pcs) {
                    total_finish_pcs += parseInt(doc.finish_item_pcs) || 0;
                }
            });
        }
        frm.set_value("finish_pcs", total_finish_pcs);
    }).catch(function(error) {
        console.error("Error calculating finish_pcs:", error);
        frm.set_value("finish_pcs", 0);
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
