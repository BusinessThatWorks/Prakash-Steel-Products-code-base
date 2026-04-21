// Copyright (c) 2026, Beetashoke Chakraborty and contributors
// For license information, please see license.txt

frappe.ui.form.on("Production Planning", {
    refresh: function (frm) {
        frm.set_query("default_bom", "production_plan", function (doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            return {
                filters: {
                    item: row.fg_item,
                    docstatus: 1,
                    is_active: 1,
                },
            };
        });

        if (frm.doc.docstatus === 1 && frm.has_perm("write")) {
            frm.add_custom_button(__("Update Items"), function () {
                _update_production_plan(frm);
            });
        }
    },
});

frappe.ui.form.on("Production Planning FG Table", {
    fg_item: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.fg_item) return;

        // Clear dependent fields first
        frappe.model.set_value(cdt, cdn, "default_bom", null);
        frappe.model.set_value(cdt, cdn, "raw_material", null);
        frappe.model.set_value(cdt, cdn, "rm_qty_required", 0);

        frappe.call({
            method: "prakash_steel.utils.lead_time.get_default_bom",
            args: { item_code: row.fg_item },
            callback: function (r) {
                if (!r.message) return;

                frappe.model.set_value(cdt, cdn, "default_bom", r.message);

                // Fetch BOM details (raw material + qty ratios)
                frappe.call({
                    method: "prakash_steel.utils.lead_time.get_bom_details",
                    args: { bom_name: r.message },
                    callback: function (res) {
                        if (!res.message) return;

                        frappe.model.set_value(cdt, cdn, "raw_material", res.message.raw_material);

                        // Recalculate if qty already entered
                        let current_row = locals[cdt][cdn];
                        if (current_row.fg_production_qty) {
                            _calc_rm_qty(cdt, cdn, current_row.fg_production_qty, res.message);
                        }
                    },
                });
            },
        });
    },

    default_bom: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.default_bom) return;

        frappe.call({
            method: "prakash_steel.utils.lead_time.get_bom_details",
            args: { bom_name: row.default_bom },
            callback: function (r) {
                if (!r.message) return;

                frappe.model.set_value(cdt, cdn, "raw_material", r.message.raw_material);

                let current_row = locals[cdt][cdn];
                if (current_row.fg_production_qty) {
                    _calc_rm_qty(cdt, cdn, current_row.fg_production_qty, r.message);
                }
            },
        });
    },

    fg_production_qty: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.default_bom || !row.fg_production_qty) return;

        frappe.call({
            method: "prakash_steel.utils.lead_time.get_bom_details",
            args: { bom_name: row.default_bom },
            callback: function (r) {
                if (!r.message) return;
                _calc_rm_qty(cdt, cdn, row.fg_production_qty, r.message);
            },
        });
    },
});

function _update_production_plan(frm) {
    frappe.model.with_doctype("Production Planning FG Table", function () {
        const dialog_data = (frm.doc.production_plan || []).map((row, i) => ({
            idx: i + 1,
            name: row.name,
            docname: row.name,
            fg_item: row.fg_item,
            default_bom: row.default_bom,
            fg_production_qty: row.fg_production_qty,
            raw_material: row.raw_material,
            rm_qty_required: row.rm_qty_required,
        }));

        let update_dialog = null;

        function refresh_grid() {
            if (update_dialog && update_dialog.fields_dict.production_plan_items) {
                update_dialog.fields_dict.production_plan_items.grid.refresh();
            }
        }

        function _df_data() {
            if (update_dialog && update_dialog.fields_dict.production_plan_items) {
                const df = update_dialog.fields_dict.production_plan_items.df;
                if (!df.data) {
                    df.data = dialog_data;
                }
                return df.data;
            }
            return dialog_data;
        }

        function _find_row_by_grid_idx(row_idx) {
            const data = _df_data();
            if (!data || row_idx == null || row_idx === "") return null;
            return data.find((doc) => cint(doc.idx) === cint(row_idx)) || null;
        }

        function _grid_idx_from_target($el) {
            const raw = $el.closest(".grid-row").attr("data-idx");
            return raw == null || raw === "" ? null : cint(raw);
        }

        function fetch_bom_chain_for_grid_idx(row_idx, fg_item_code) {
            if (!fg_item_code || row_idx == null) return;
            const row = _find_row_by_grid_idx(row_idx);
            if (!row) return;

            row.default_bom = null;
            row.raw_material = null;
            row.rm_qty_required = 0;

            frappe.call({
                method: "prakash_steel.utils.lead_time.get_default_bom",
                args: { item_code: fg_item_code },
                callback: function (r) {
                    const rdoc = _find_row_by_grid_idx(row_idx);
                    if (!rdoc) return;
                    if (!r.message) {
                        refresh_grid();
                        return;
                    }
                    rdoc.default_bom = r.message;
                    frappe.call({
                        method: "prakash_steel.utils.lead_time.get_bom_details",
                        args: { bom_name: r.message },
                        callback: function (res) {
                            const rdoc2 = _find_row_by_grid_idx(row_idx);
                            if (!rdoc2) return;
                            if (!res.message) {
                                refresh_grid();
                                return;
                            }
                            rdoc2.raw_material = res.message.raw_material;
                            const fg_qty = cint(rdoc2.fg_production_qty);
                            if (fg_qty && res.message.bom_fg_qty) {
                                rdoc2.rm_qty_required = Math.ceil(
                                    (fg_qty / res.message.bom_fg_qty) * res.message.bom_rm_qty
                                );
                            }
                            refresh_grid();
                        },
                    });
                },
            });
        }

        function _bind_dom_events() {
            const $root = update_dialog.$wrapper;
            $root.off(".ppUpdItems");

            $root.on("change.ppUpdItems", "input[data-fieldname='fg_production_qty']", function () {
                const row_idx = _grid_idx_from_target($(this));
                const qty = cint($(this).val());
                const row = _find_row_by_grid_idx(row_idx);
                if (!row || !row.default_bom || !qty || qty <= 0) return;

                frappe.call({
                    method: "prakash_steel.utils.lead_time.get_bom_details",
                    args: { bom_name: row.default_bom },
                    callback: function (r) {
                        if (!r.message || !r.message.bom_fg_qty) return;
                        const target = _find_row_by_grid_idx(row_idx);
                        if (!target) return;
                        target.rm_qty_required = Math.ceil(
                            (qty / r.message.bom_fg_qty) * r.message.bom_rm_qty
                        );
                        refresh_grid();
                    },
                });
            });

            $root.on(
                "change.ppUpdItems awesomplete-selectcomplete.ppUpdItems",
                "input[data-fieldname='fg_item']",
                function () {
                    const row_idx = _grid_idx_from_target($(this));
                    const v = ($(this).val() || "").trim();
                    if (!v) return;
                    fetch_bom_chain_for_grid_idx(row_idx, v);
                }
            );
        }

        const table_fields = [
            {
                fieldname: "name",
                fieldtype: "Data",
                label: "name",
                hidden: 1,
                read_only: 1,
            },
            {
                fieldname: "fg_item",
                fieldtype: "Link",
                options: "Item",
                label: __("FG Item"),
                in_list_view: 1,
                reqd: 1,
                columns: 2,
            },
            {
                fieldname: "default_bom",
                fieldtype: "Link",
                options: "BOM",
                label: __("Default BOM"),
                in_list_view: 1,
                reqd: 1,
                columns: 2,
                get_query: function () {
                    let row_idx = null;
                    const $el = this.$input || this.$wrapper;
                    if ($el) {
                        row_idx = _grid_idx_from_target($el);
                    }
                    const row = _find_row_by_grid_idx(row_idx);
                    const fg = row ? row.fg_item : this.doc && this.doc.fg_item;
                    return {
                        filters: {
                            item: fg,
                            docstatus: 1,
                            is_active: 1,
                        },
                    };
                },
            },
            {
                fieldname: "fg_production_qty",
                fieldtype: "Int",
                label: __("FG Production Qty"),
                in_list_view: 1,
                reqd: 1,
                columns: 2,
            },
            {
                fieldname: "raw_material",
                fieldtype: "Link",
                options: "Item",
                label: __("Raw Material"),
                in_list_view: 1,
                read_only: 1,
                columns: 2,
            },
            {
                fieldname: "rm_qty_required",
                fieldtype: "Int",
                label: __("RM Qty Required"),
                in_list_view: 1,
                columns: 2,
            },
        ];

        update_dialog = new frappe.ui.Dialog({
            title: __("Update Items"),
            size: "extra-large",
            fields: [
                {
                    fieldname: "production_plan_items",
                    fieldtype: "Table",
                    label: __("Production Plan Items"),
                    cannot_add_rows: false,
                    cannot_delete_rows: false,
                    in_place_edit: false,
                    reqd: 1,
                    data: dialog_data,
                    get_data: function () {
                        return dialog_data;
                    },
                    fields: table_fields,
                },
            ],
            primary_action_label: __("Update"),
            primary_action: function () {
                const items = (this.get_values().production_plan_items || []).filter(
                    (d) => !!d.fg_item
                );
                const dlg = this;

                frappe.call({
                    method: "prakash_steel.prakash_steel.doctype.production_planning.production_planning.update_production_plan",
                    args: {
                        source_name: frm.doc.name,
                        items: items,
                    },
                    callback: function (r) {
                        if (!r.exc) {
                            dlg.hide();
                            frm.reload_doc();
                            frappe.show_alert({
                                message: __("Items updated successfully"),
                                indicator: "green",
                            });
                        }
                    },
                });
            },
        });

        update_dialog.fields_dict.production_plan_items.df.data = dialog_data;
        update_dialog.show();
        _bind_dom_events();
    });
}

function _calc_rm_qty(cdt, cdn, fg_production_qty, bom_details) {
    let bom_fg_qty = bom_details.bom_fg_qty;
    let bom_rm_qty = bom_details.bom_rm_qty;

    if (!bom_fg_qty) return;

    let rm_qty = Math.ceil((fg_production_qty / bom_fg_qty) * bom_rm_qty);
    frappe.model.set_value(cdt, cdn, "rm_qty_required", rm_qty);
}
