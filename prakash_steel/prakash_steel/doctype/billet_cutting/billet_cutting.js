// Put this whole block in a Client Script for the parent doctype (e.g. Billet Cutting)
frappe.ui.form.on('Billet Cutting', {
    refresh(frm) {
        // On form load/refresh, adjust every existing row
        frm.fields_dict.items.grid.grid_rows.forEach(row => {
            row.toggle_editable('miss_billet_weight', !!row.doc.miss_billet_pcs);
        });
    }
});

frappe.ui.form.on('Billet Cutting Item', {
    billet_weight(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.total_billet_cutting_pcs && row.billet_weight) {
            frappe.model.set_value(
                cdt,
                cdn,
                "cutting_weight",
                row.billet_weight / row.total_billet_cutting_pcs
            );
        }
    },

    total_billet_cutting_pcs(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        // Update total raw material pcs
        frappe.model.set_value(
            cdt,
            cdn,
            "total_raw_material_pcs",
            (row.total_billet_cutting_pcs || 0) + (row.miss_billet_pcs || 0)
        );

        // Recalculate cutting_weight
        if (row.total_billet_cutting_pcs && row.billet_weight) {
            frappe.model.set_value(
                cdt,
                cdn,
                "cutting_weight",
                row.billet_weight / row.total_billet_cutting_pcs
            );
        }
    },

    miss_billet_pcs(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // Update total raw material pcs
        frappe.model.set_value(
            cdt,
            cdn,
            "total_raw_material_pcs",
            (row.total_billet_cutting_pcs || 0) + (row.miss_billet_pcs || 0)
        );

        // Enable or disable weight based on pcs
        const grid_row = frm.fields_dict.items.grid.grid_rows_by_docname[cdn];
        if (grid_row) {
            grid_row.toggle_editable('miss_billet_weight', !!row.miss_billet_pcs);
        }

        // If pcs removed, clear weight so there's no stale value
        if (!row.miss_billet_pcs && row.miss_billet_weight) {
            frappe.model.set_value(cdt, cdn, 'miss_billet_weight', '');
        }
    },

    // Safety check: prevent entering weight without pcs (e.g. via API or copy/paste)
    miss_billet_weight(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.miss_billet_pcs && row.miss_billet_weight) {
            frappe.throw(__('Please enter Miss Billet Pcs before entering Miss Billet Weight.'));
        }
    },

    // When opening the child row form (dialog), fix the field's editability state
    form_render(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const grid_row = frm.fields_dict.items.grid.grid_rows_by_docname[cdn];
        if (grid_row) {
            grid_row.toggle_editable('miss_billet_weight', !!row.miss_billet_pcs);
        }
    }
});
