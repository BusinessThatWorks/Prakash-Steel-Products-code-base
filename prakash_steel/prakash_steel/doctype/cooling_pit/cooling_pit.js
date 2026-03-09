// Copyright (c) 2026, Beetashoke Chakraborty and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Cooling PIT", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Cooling PIT', {
    posting_date: function (frm) {
        set_material_out_time(frm);
    },

    refresh: function (frm) {
        if (frm.doc.posting_date) {
            set_material_out_time(frm);
        }
        calculate_duration(frm);
    },

    material_in_time: function (frm) {
        calculate_duration(frm);
    },

    material_out_time: function (frm) {
        calculate_duration(frm);
    }
});

function set_material_out_time(frm) {
    if (!frm.doc.posting_date) return;

    // Only auto-set on new unsaved documents, never overwrite user input
    if (!frm.is_new()) return;
    if (frm.doc.material_out_time) return;

    let now_time = frappe.datetime.now_time();
    let full_datetime = frm.doc.posting_date + ' ' + now_time;

    frm.set_value('material_out_time', full_datetime);
}

function calculate_duration(frm) {
    let material_in = frm.doc.material_in_time;
    let material_out = frm.doc.material_out_time;

    console.log('--- calculate_duration called ---');
    console.log('material_in_time:', material_in);
    console.log('material_out_time:', material_out);

    if (!material_in || !material_out) {
        console.log('One or both times missing, clearing duration');
        frm.set_value('duration', 0);
        return;
    }

    let in_dt = new Date(material_in);
    let out_dt = new Date(material_out);

    console.log('Parsed in_time (Date):', in_dt);
    console.log('Parsed out_time (Date):', out_dt);

    // difference in milliseconds → convert to total seconds
    let diff_ms = out_dt - in_dt;
    let total_seconds = Math.floor(diff_ms / 1000);

    console.log('Difference in ms:', diff_ms);
    console.log('Total seconds:', total_seconds);

    if (total_seconds <= 0) {
        console.log('out_time is not after in_time — setting duration to 0');
        frm.set_value('duration', 0);
        return;
    }

    // breakdown for logging
    let days    = Math.floor(total_seconds / 86400);
    let hours   = Math.floor((total_seconds % 86400) / 3600);
    let minutes = Math.floor((total_seconds % 3600) / 60);
    let seconds = total_seconds % 60;

    console.log(`Duration breakdown: ${days}d ${hours}h ${minutes}m ${seconds}s`);
    console.log('Setting duration field to (seconds):', total_seconds);

    // Frappe Duration field stores/accepts value in seconds (integer)
    frm.set_value('duration', total_seconds);
    frm.refresh_field('duration');
}