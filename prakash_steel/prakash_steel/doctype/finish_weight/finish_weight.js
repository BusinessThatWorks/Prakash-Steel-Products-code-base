frappe.ui.form.on("Finish Weight Item", {
    finish_weight: function(frm, cdt, cdn) {
        calculate_fg_weight(frm, cdt, cdn);
    },
    finish_pcs: function(frm, cdt, cdn) {
        calculate_fg_weight(frm, cdt, cdn);
    }
});

function calculate_fg_weight(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    if (row.finish_weight && row.finish_pcs) {
        frappe.model.set_value(cdt, cdn, "fg_per_pcs_weight", row.finish_weight / row.finish_pcs);
    } else {
        frappe.model.set_value(cdt, cdn, "fg_per_pcs_weight", 0);
    }
}
