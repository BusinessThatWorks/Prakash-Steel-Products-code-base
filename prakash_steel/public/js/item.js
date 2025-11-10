// Item Doctype Custom Implementation
frappe.ui.form.on("Item", {
    refresh: function (frm) {
        // Initialize field visibility on form load
        toggle_fields_visibility(frm);
        toggle_group_for_sub_assemblies_visibility(frm);
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

