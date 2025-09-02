// // Put this whole block in a Client Script for the parent doctype (e.g. Billet Cutting)
// frappe.ui.form.on('Billet Cutting', {
//     refresh(frm) {
//         // On form load/refresh, adjust every existing row
//         frm.fields_dict.items.grid.grid_rows.forEach(row => {
//             row.toggle_editable('miss_billet_weight', !!row.doc.miss_billet_pcs);
//         });
//     }
// });

// frappe.ui.form.on('Billet Cutting Item', {
//     billet_weight(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
//         if (row.total_billet_cutting_pcs && row.billet_weight) {
//             frappe.model.set_value(
//                 cdt,
//                 cdn,
//                 "cutting_weight",
//                 row.billet_weight / row.total_billet_cutting_pcs
//             );
//         }
//     },

//     total_billet_cutting_pcs(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
//         // Update total raw material pcs
//         frappe.model.set_value(
//             cdt,
//             cdn,
//             "total_raw_material_pcs",
//             (row.total_billet_cutting_pcs || 0) + (row.miss_billet_pcs || 0)
//         );

//         // Recalculate cutting_weight
//         if (row.total_billet_cutting_pcs && row.billet_weight) {
//             frappe.model.set_value(
//                 cdt,
//                 cdn,
//                 "cutting_weight",
//                 row.billet_weight / row.total_billet_cutting_pcs
//             );
//         }
//     },

//     miss_billet_pcs(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];

//         // Update total raw material pcs
//         frappe.model.set_value(
//             cdt,
//             cdn,
//             "total_raw_material_pcs",
//             (row.total_billet_cutting_pcs || 0) + (row.miss_billet_pcs || 0)
//         );

//         // Enable or disable weight based on pcs
//         const grid_row = frm.fields_dict.items.grid.grid_rows_by_docname[cdn];
//         if (grid_row) {
//             grid_row.toggle_editable('miss_billet_weight', !!row.miss_billet_pcs);
//         }

//         // If pcs removed, clear weight so there's no stale value
//         if (!row.miss_billet_pcs && row.miss_billet_weight) {
//             frappe.model.set_value(cdt, cdn, 'miss_billet_weight', '');
//         }
//     },

//     // Safety check: prevent entering weight without pcs (e.g. via API or copy/paste)
//     miss_billet_weight(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
//         if (!row.miss_billet_pcs && row.miss_billet_weight) {
//             frappe.throw(__('Please enter Miss Billet Pcs before entering Miss Billet Weight.'));
//         }
//     },

//     // When opening the child row form (dialog), fix the field's editability state
//     form_render(frm, cdt, cdn) {
//         const row = locals[cdt][cdn];
//         const grid_row = frm.fields_dict.items.grid.grid_rows_by_docname[cdn];
//         if (grid_row) {
//             grid_row.toggle_editable('miss_billet_weight', !!row.miss_billet_pcs);
//         }
//     }
// });










frappe.ui.form.on('Billet Cutting', {
    refresh(frm) {
        console.log('[refresh] called');
        // give the grid a tiny tick to be ready
        setTimeout(() => {
            const grid = frm.fields_dict?.table_ovvx?.grid;
            console.log('[refresh] grid?', !!grid);

            if (!grid) {
                console.log('[refresh] no grid found for table_ovvx');
                return;
            }

            grid.grid_rows.forEach(row => {
                console.log(`[refresh] row ${row.doc.name} miss_billet_pcs=${row.doc.miss_billet_pcs}`);
                // hide/show according to pcs
                row.toggle_display('miss_billet_weight', !!row.doc.miss_billet_pcs);
            });
        }, 80);
    },

    // ensure new rows also get proper visibility
    table_ovvx_add(frm, cdt, cdn) {
        console.log('[table_ovvx_add] new child row added', cdn);
        setTimeout(() => {
            const grid = frm.fields_dict?.table_ovvx?.grid;
            const gr = grid?.grid_rows_by_docname?.[cdn];
            if (gr) {
                console.log('[table_ovvx_add] toggle_display for', cdn, 'value=', !!locals[cdt][cdn].miss_billet_pcs);
                gr.toggle_display('miss_billet_weight', !!locals[cdt][cdn].miss_billet_pcs);
            } else {
                console.log('[table_ovvx_add] grid_row not ready for', cdn);
            }
        }, 60);
    }
});

frappe.ui.form.on('Billet Cutting Item', {
    billet_weight(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        console.log('[billet_weight] row', cdn, 'billet_weight=', row.billet_weight);

        if (row.total_billet_cutting_pcs && row.billet_weight) {
            const cutting = row.billet_weight / row.total_billet_cutting_pcs;
            frappe.model.set_value(cdt, cdn, "cutting_weight", cutting);
            console.log('[billet_weight] set cutting_weight=', cutting);
        }
    },

    total_billet_cutting_pcs(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        console.log('[total_billet_cutting_pcs] row', cdn, 'total_billet_cutting_pcs=', row.total_billet_cutting_pcs);

        // Update total raw material pcs
        frappe.model.set_value(
            cdt, cdn, "total_raw_material_pcs",
            (row.total_billet_cutting_pcs || 0) + (row.miss_billet_pcs || 0)
        );

        // Recalculate cutting_weight
        if (row.total_billet_cutting_pcs && row.billet_weight) {
            const cutting = row.billet_weight / row.total_billet_cutting_pcs;
            frappe.model.set_value(cdt, cdn, "cutting_weight", cutting);
            console.log('[total_billet_cutting_pcs] recalculated cutting_weight=', cutting);
        }
    },

    miss_billet_pcs(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        console.log('[miss_billet_pcs] row', cdn, 'miss_billet_pcs=', row.miss_billet_pcs);

        // Update total raw material pcs
        frappe.model.set_value(
            cdt, cdn, "total_raw_material_pcs",
            (row.total_billet_cutting_pcs || 0) + (row.miss_billet_pcs || 0)
        );

        // Hide/show weight field in the grid (and dialog)
        const grid = frm.fields_dict?.table_ovvx?.grid;
        const gr = grid?.grid_rows_by_docname?.[cdn];
        const show = !!row.miss_billet_pcs;

        if (gr) {
            console.log('[miss_billet_pcs] toggle_display (direct) for', cdn, 'show=', show);
            gr.toggle_display('miss_billet_weight', show);
        } else {
            console.log('[miss_billet_pcs] grid_row not ready, will retry for', cdn);
            setTimeout(() => {
                const gr2 = frm.fields_dict?.table_ovvx?.grid?.grid_rows_by_docname?.[cdn];
                if (gr2) {
                    console.log('[miss_billet_pcs][retry] toggle_display for', cdn, 'show=', show);
                    gr2.toggle_display('miss_billet_weight', show);
                } else {
                    console.log('[miss_billet_pcs][retry] still no grid_row for', cdn);
                }
            }, 60);
        }

        // If pcs removed, clear weight so there's no stale value
        if (!show && row.miss_billet_weight) {
            frappe.model.set_value(cdt, cdn, 'miss_billet_weight', '');
            console.log('[miss_billet_pcs] cleared miss_billet_weight for', cdn);
        }
    },

    // Lightweight defensive handler: if someone pastes weight without pcs, silently clear it
    miss_billet_weight(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        console.log('[miss_billet_weight] row', cdn, 'miss_billet_weight=', row.miss_billet_weight);

        if (!row.miss_billet_pcs && row.miss_billet_weight) {
            // no throw; user asked no validation — just clear and log
            frappe.model.set_value(cdt, cdn, 'miss_billet_weight', '');
            console.log('[miss_billet_weight] cleared value because miss_billet_pcs is empty for', cdn);
        }
    },

    // When opening the child row dialog, ensure visibility is correct there too
    form_render(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        console.log('[form_render] row dialog opened for', cdn, 'miss_billet_pcs=', row.miss_billet_pcs);

        const gr = frm.fields_dict?.table_ovvx?.grid?.grid_rows_by_docname?.[cdn];
        if (gr) {
            console.log('[form_render] toggling display in dialog for', cdn);
            gr.toggle_display('miss_billet_weight', !!row.miss_billet_pcs);
        } else {
            console.log('[form_render] grid_row not ready in dialog, retrying for', cdn);
            setTimeout(() => {
                const gr2 = frm.fields_dict?.table_ovvx?.grid?.grid_rows_by_docname?.[cdn];
                if (gr2) {
                    console.log('[form_render][retry] toggling display for', cdn);
                    gr2.toggle_display('miss_billet_weight', !!row.miss_billet_pcs);
                } else {
                    console.log('[form_render][retry] still no grid_row for', cdn);
                }
            }, 80);
        }
    }
});

