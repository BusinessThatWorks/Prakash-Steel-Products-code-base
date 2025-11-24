// Item Doctype Custom Implementation
frappe.ui.form.on("Item", {
    refresh: function (frm) {
        // Initialize field visibility on form load
        toggle_fields_visibility(frm);
        toggle_group_for_sub_assemblies_visibility(frm);
        toggle_buffer_fields_visibility(frm);

        // Calculate and display decoupled lead time if item has BOM
        update_decoupled_lead_time(frm);
    },

    custom_store_item: function (frm) {
        // Toggle field visibility when custom_store_item checkbox changes
        toggle_fields_visibility(frm);
        toggle_group_for_sub_assemblies_visibility(frm);
    },

    custom_item_size: function (frm) {
        // Generate item_code and item_name when custom_item_size changes
        generate_item_code_and_name(frm);
    },

    custom_shape: function (frm) {
        // Generate item_code and item_name when custom_shape changes
        generate_item_code_and_name(frm);
    },

    custom_grade: function (frm) {
        // Generate item_code and item_name when custom_grade changes
        generate_item_code_and_name(frm);
    },

    custom_category_name: function (frm) {
        // Generate item_code and item_name when custom_category_name changes
        generate_item_code_and_name(frm);
    },

    item_group: function (frm) {
        // Toggle custom_group_for_sub_assemblies visibility when item_group changes
        toggle_group_for_sub_assemblies_visibility(frm);
    },

    lead_time_days: function (frm) {
        // Recalculate decoupled lead time when lead_time_days changes
        update_decoupled_lead_time(frm);
    },

    custom_buffer_flag: function (frm) {
        // Toggle safety_stock visibility and mandatory status when custom_buffer_flag changes
        toggle_buffer_fields_visibility(frm);

        // Clear calculated fields if switching to Non-Buffer
        if (frm.doc.custom_buffer_flag !== 'Buffer') {
            frm.set_value('safety_stock', null);
            frm.set_value('custom_top_of_red', null);
            frm.set_value('custom_top_of_yellow', null);
        }
    },

    safety_stock: function (frm) {
        // Calculate custom_top_of_red and custom_top_of_yellow when safety_stock changes
        calculate_buffer_fields(frm);
    }
});

function toggle_fields_visibility(frm) {
    // List of fields to hide when custom_store_item is checked
    const fields_to_hide = [
        'custom_item_type',
        'custom_category_name',
        'custom_item_size',
        'custom_grade',
        'custom_shape',
        'custom_mto_or_mta',
        'custom_item_group_batch_qty',
        'custom_item_sub_group_batch_',
        'custom_box',
        'custom_desc_code',
        'custom_mqp',
        'min_order_qty',
        'custom_per_hour_production_qty',
        'custom_group_for_sub_assemblies',
        'custom_item_sub_group_batch_qty'
    ];

    // Check if custom_store_item is selected (checked)
    const is_store_item = frm.doc.custom_store_item || 0;

    // Toggle visibility for each field
    fields_to_hide.forEach(function (fieldname) {
        if (frm.fields_dict[fieldname]) {
            if (is_store_item) {
                // Hide the field if custom_store_item is checked
                frm.set_df_property(fieldname, 'hidden', 1);
            } else {
                // Show the field if custom_store_item is unchecked
                frm.set_df_property(fieldname, 'hidden', 0);
            }
        }
    });
}

function generate_item_code_and_name(frm) {
    // Only generate if custom_store_item is not checked (fields are visible)
    if (frm.doc.custom_store_item) {
        return;
    }

    // Get values from the fields
    const category_name = frm.doc.custom_category_name || '';
    const item_size = frm.doc.custom_item_size || '';
    const shape = frm.doc.custom_shape || '';
    const grade = frm.doc.custom_grade || '';

    // Check if all three required fields are filled
    if (item_size && shape && grade) {
        // List of category names that require "B" prefix
        const bright_categories = [
            'Bright Squares',
            'Bright Rounds',
            'Bright Hex',
            'Bright Flats'
        ];

        // Check if category_name is one of the bright categories
        const is_bright_category = bright_categories.includes(category_name);

        // Build the generated value
        let generated_value = item_size + ' ' + shape + ' ' + grade;

        // Prepend "B " if category is one of the bright categories
        if (is_bright_category) {
            generated_value = 'B ' + generated_value;
        }

        // Set item_code and item_name
        frm.set_value('item_code', generated_value);
        frm.set_value('item_name', generated_value);
    }
}

function toggle_group_for_sub_assemblies_visibility(frm) {
    // Only show if custom_store_item is not checked (field is visible)
    if (frm.doc.custom_store_item) {
        return;
    }

    // Check if custom_group_for_sub_assemblies field exists
    if (frm.fields_dict['custom_group_for_sub_assemblies']) {
        // Show only if item_group is "Sub Assemblies"
        const is_sub_assemblies = frm.doc.item_group === 'Sub Assemblies';

        if (is_sub_assemblies) {
            frm.set_df_property('custom_group_for_sub_assemblies', 'hidden', 0);
        } else {
            frm.set_df_property('custom_group_for_sub_assemblies', 'hidden', 1);
        }
    }
}

function update_decoupled_lead_time(frm) {
    // Only calculate if item_code exists (not a new item)
    if (!frm.doc.item_code) {
        console.log("[Lead Time] No item_code, skipping calculation");
        return;
    }

    // Check if custom_decoupled_lead_time field exists
    if (!frm.fields_dict['custom_decoupled_lead_time']) {
        console.log("[Lead Time] custom_decoupled_lead_time field not found");
        return;
    }

    console.log("========================================");
    console.log("[Lead Time] Starting calculation for item:", frm.doc.item_code);
    console.log("[Lead Time] Item details:", {
        item_code: frm.doc.item_code,
        lead_time_days: frm.doc.lead_time_days,
        custom_buffer_flag: frm.doc.custom_buffer_flag,
        current_decoupled_lead_time: frm.doc.custom_decoupled_lead_time
    });

    // Store the current dirty state before updating
    const was_dirty = frm.is_dirty();

    // Call server method to calculate decoupled lead time
    frappe.call({
        method: "prakash_steel.api.get_decoupled_lead_time.get_decoupled_lead_time",
        args: {
            item_code: frm.doc.item_code
        },
        callback: function (r) {
            console.log("[Lead Time] Server response:", r);

            if (r.message !== undefined && r.message !== null) {
                // Only update if value is different to avoid unnecessary updates
                const current_value = frm.doc.custom_decoupled_lead_time;
                const new_value = r.message;

                console.log("[Lead Time] Calculation result:", {
                    current_value: current_value,
                    new_value: new_value,
                    changed: current_value !== new_value
                });

                if (current_value !== new_value) {
                    // Update the doc value directly in locals to avoid triggering dirty state
                    const doc = locals[frm.doctype][frm.docname];
                    if (doc) {
                        doc.custom_decoupled_lead_time = new_value;
                    }

                    // Also update in form doc
                    frm.doc.custom_decoupled_lead_time = new_value;

                    // Refresh the field
                    frm.refresh_field('custom_decoupled_lead_time');

                    console.log("[Lead Time] Updated custom_decoupled_lead_time to:", new_value);

                    // If form wasn't dirty before, restore that state
                    if (!was_dirty) {
                        // Remove from modified fields if it was added
                        if (frm._dirty_fields) {
                            const index = frm._dirty_fields.indexOf('custom_decoupled_lead_time');
                            if (index > -1) {
                                frm._dirty_fields.splice(index, 1);
                            }
                        }

                        // Reset dirty state if no other changes
                        setTimeout(function () {
                            if (!was_dirty && frm.is_dirty && frm.is_dirty()) {
                                // Check if there are any other modified fields
                                const has_other_changes = frm._dirty_fields && frm._dirty_fields.length > 0;
                                if (!has_other_changes) {
                                    frm.dirty(false);
                                }
                            }
                        }, 100);
                    }
                } else {
                    console.log("[Lead Time] Value unchanged, no update needed");
                }
            } else {
                console.warn("[Lead Time] Server returned null/undefined value");
            }

            // Also call debug function to get detailed information
            get_lead_time_debug_info(frm);
        },
        error: function (err) {
            console.error("========================================");
            console.error("[Lead Time] ERROR fetching decoupled lead time:");
            console.error("Item Code:", frm.doc.item_code);
            console.error("Error:", err);
            if (err.exc) {
                console.error("Exception:", err.exc);
            }
            if (err.exc_type) {
                console.error("Exception Type:", err.exc_type);
            }
            console.error("========================================");
        }
    });
}

function get_lead_time_debug_info(frm) {
    // Only get debug info if item_code exists
    if (!frm.doc.item_code) {
        return;
    }

    console.log("[Lead Time] Fetching debug information...");

    frappe.call({
        method: "prakash_steel.utils.lead_time.debug_lead_time_calculation",
        args: {
            item_code: frm.doc.item_code
        },
        callback: function (r) {
            console.log("========================================");
            console.log("[Lead Time] DEBUG INFORMATION:");
            console.log("========================================");

            if (r.message) {
                const debug = r.message;

                if (debug.error) {
                    console.error("[Lead Time] Debug Error:", debug.error);
                    if (debug.traceback) {
                        console.error("[Lead Time] Traceback:", debug.traceback);
                    }
                } else {
                    console.log("Item Code:", debug.item_code);
                    console.log("Lead Time Days:", debug.lead_time_days);
                    console.log("Buffer Flag:", debug.custom_buffer_flag);
                    console.log("Is Buffer:", debug.is_buffer);
                    console.log("Has BOM:", debug.has_bom);
                    console.log("BOM Name:", debug.bom_name);
                    console.log("Calculated Decoupled Lead Time:", debug.calculated_decoupled_lead_time);

                    // Log raw trace data for debugging
                    console.log("Raw Calculation Trace:", debug.calculation_trace);

                    // Display detailed calculation trace
                    if (debug.calculation_trace && debug.calculation_trace.length > 0) {
                        console.log("\n[Lead Time] DETAILED CALCULATION BREAKDOWN:");
                        console.log("========================================");
                        debug.calculation_trace.forEach((trace, index) => {
                            const indent = "  ".repeat(trace.level);
                            console.log(`${indent}Level ${trace.level}: ${trace.item_code}`);
                            console.log(`${indent}  Own Lead Time: ${trace.own_lead_time || 0}`);
                            console.log(`${indent}  Is Buffer: ${trace.is_buffer}`);

                            if (trace.is_buffer) {
                                console.log(`${indent}  → Result: 0 (buffer item)`);
                            } else if (!trace.has_bom) {
                                console.log(`${indent}  → Result: ${trace.own_lead_time} (no BOM)`);
                            } else {
                                console.log(`${indent}  BOM: ${trace.bom_name || 'N/A'}`);

                                if (trace.bom_items && trace.bom_items.length > 0) {
                                    console.log(`${indent}  BOM Items:`);
                                    trace.bom_items.forEach((item, idx) => {
                                        if (item.error) {
                                            console.log(`${indent}    ${idx + 1}. ${item.item_code}: ERROR - ${item.error}`);
                                        } else {
                                            const bufferNote = item.is_buffer ? " (BUFFER - IGNORED)" : "";
                                            console.log(`${indent}    ${idx + 1}. ${item.item_code}: Lead Time = ${item.lead_time}${bufferNote}`);
                                        }
                                    });
                                }

                                if (trace.max_lead_time_at_level !== null && trace.max_lead_time_at_level !== undefined) {
                                    console.log(`${indent}  Max Lead Time at Level: ${trace.max_lead_time_at_level}`);
                                    if (trace.items_with_max && trace.items_with_max.length > 0) {
                                        console.log(`${indent}  Item(s) with Max: ${trace.items_with_max.join(", ")}`);
                                    }
                                }

                                if (trace.recursive_contribution !== null && trace.recursive_contribution !== undefined) {
                                    console.log(`${indent}  Recursive Contribution: ${trace.recursive_contribution}`);
                                }

                                console.log(`${indent}  → Calculation: ${trace.own_lead_time || 0} + ${trace.max_lead_time_at_level || 0} + ${trace.recursive_contribution || 0} = ${trace.total}`);
                            }
                            console.log("");
                        });
                        console.log("========================================");
                    }

                    if (debug.bom_items && debug.bom_items.length > 0) {
                        console.log("\n[Lead Time] BOM Items Summary:");
                        debug.bom_items.forEach((item, index) => {
                            if (item.error) {
                                console.error(`  ${index + 1}. ${item.item_code}: ERROR - ${item.error}`);
                            } else {
                                console.log(`  ${index + 1}. ${item.item_code}:`, {
                                    lead_time_days: item.lead_time_days,
                                    buffer_flag: item.custom_buffer_flag,
                                    is_buffer: item.is_buffer
                                });
                            }
                        });
                    } else if (debug.has_bom) {
                        console.log("[Lead Time] BOM has no items or all items are buffer");
                    }
                }
            } else {
                console.warn("[Lead Time] No debug information returned");
            }

            console.log("========================================");
        },
        error: function (err) {
            console.error("[Lead Time] Error fetching debug info:", err);
        }
    });
}

function toggle_buffer_fields_visibility(frm) {
    // Check if custom_buffer_flag field exists
    if (!frm.fields_dict['custom_buffer_flag']) {
        return;
    }

    const is_buffer = frm.doc.custom_buffer_flag === 'Buffer';

    // Toggle safety_stock visibility
    if (frm.fields_dict['safety_stock']) {
        frm.set_df_property('safety_stock', 'hidden', !is_buffer);
        frm.set_df_property('safety_stock', 'reqd', is_buffer);
    }

    // Toggle custom_top_of_red visibility
    if (frm.fields_dict['custom_top_of_red']) {
        frm.set_df_property('custom_top_of_red', 'hidden', !is_buffer);
    }

    // Toggle custom_top_of_yellow visibility
    if (frm.fields_dict['custom_top_of_yellow']) {
        frm.set_df_property('custom_top_of_yellow', 'hidden', !is_buffer);
    }

    // Validate safety_stock if Buffer is selected
    if (is_buffer && frm.doc.safety_stock !== null && frm.doc.safety_stock !== undefined) {
        if (frm.doc.safety_stock <= 0) {
            frappe.msgprint({
                title: __('Validation Error'),
                indicator: 'red',
                message: __('Safety Stock must be greater than 0 when Buffer Flag is set to Buffer.')
            });
            frm.set_value('safety_stock', null);
        }
    }
}

function calculate_buffer_fields(frm) {
    // Only calculate if custom_buffer_flag is "Buffer"
    if (frm.doc.custom_buffer_flag !== 'Buffer') {
        return;
    }

    // Get safety_stock value
    const safety_stock = frm.doc.safety_stock;

    // Validate safety_stock is greater than 0
    if (safety_stock !== null && safety_stock !== undefined) {
        if (safety_stock <= 0) {
            frappe.msgprint({
                title: __('Validation Error'),
                indicator: 'red',
                message: __('Safety Stock must be greater than 0.')
            });
            frm.set_value('safety_stock', null);
            frm.set_value('custom_top_of_red', null);
            frm.set_value('custom_top_of_yellow', null);
            return;
        }

        // Calculate custom_top_of_red = round(1/3 * safety_stock)
        const top_of_red = Math.round((1 / 3) * safety_stock);

        // Calculate custom_top_of_yellow = round(2/3 * safety_stock)
        const top_of_yellow = Math.round((2 / 3) * safety_stock);

        // Set the calculated values
        frm.set_value('custom_top_of_red', top_of_red);
        frm.set_value('custom_top_of_yellow', top_of_yellow);
    } else {
        // Clear calculated fields if safety_stock is empty
        frm.set_value('custom_top_of_red', null);
        frm.set_value('custom_top_of_yellow', null);
    }
}

