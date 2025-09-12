// // Parent Doctype: Material Request
// frappe.ui.form.on("Material Request", {
//     refresh: function(frm) {
//         console.log("=== Material Request Form Refreshed ===");
//         console.log("Parent Doc:", frm.doc);

//         // Optional: log existing child table rows on refresh
//         frm.doc.items.forEach(function(row) {
//             console.log("Child row on refresh:", row.item_code, row.name);
//         });
//     }
// });

// // Child Table: Material Request Item
// frappe.ui.form.on('Material Request Item', {
//     item_code: function(frm, cdt, cdn) {
//         const row = locals[cdt][cdn];

//         console.log("=== Material Request Item Code Triggered ===");
//         console.log("Row data:", row);
//         console.log("CDT:", cdt, "CDN:", cdn);

//         // Check if item_code exists
//         if (!row.item_code) {
//             console.log("No Item Code selected. Setting available stock to 0");
//             frappe.model.set_value(cdt, cdn, 'custom_quantity_available_in_kg', 0);
//             frm.refresh_field("items");
//             return;
//         }

//         console.log("Selected Item Code:", row.item_code);
//         console.log("Calling Server Script API: get_available_stock");

//         // Call the whitelisted Python method
//         frappe.call({
//             method: "prakash_steel.api.get_available_stock.get_available_stock", // Only sending item_code
//             args: {
//                 item_code: row.item_code
//             },
//             callback: function(res) {
//                 console.log("Server response:", res);

//                 if (res.message !== undefined) {
//                     console.log("Available stock received:", res.message);
//                     frappe.model.set_value(cdt, cdn, 'custom_quantity_available_in_kg', res.message);
//                 } else {
//                     console.log("No stock returned from server. Setting 0");
//                     frappe.model.set_value(cdt, cdn, 'custom_quantity_available_in_kg', 0);
//                 }

//                 frm.refresh_field("items");
//             },
//             error: function(err) {
//                 console.error("Error fetching stock from server:", err);
//                 frappe.model.set_value(cdt, cdn, 'custom_quantity_available_in_kg', 0);
//                 frm.refresh_field("items");
//             }
//         });
//     }
// });





frappe.ui.form.on("Material Request", {
    refresh: function (frm) {
        console.log("=== Material Request Form Refreshed ===");
        console.log("Parent Doc:", frm.doc);

        // Optional: log existing child table rows on refresh
        frm.doc.items.forEach(function (row) {
            console.log("Child row on refresh:", row.item_code, row.name);
        });
    }
});

frappe.ui.form.on("Material Request Item", {
    item_code: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        console.log("=== Material Request Item Code Triggered ===");
        console.log("[Step 0] Item Code Changed:", row.item_code);
        console.log("Row data:", row);
        console.log("CDT:", cdt, "CDN:", cdn);

        if (!row.item_code) {
            console.log("[Step 1] No item_code provided, exiting.");
            console.log("No Item Code selected. Setting available stock to 0");
            frappe.model.set_value(cdt, cdn, 'custom_quantity_available_in_kg', 0);
            frm.refresh_field("items");
            return;
        }

        console.log("[Step 2] Calling server method to get last rate...");
        frappe.call({
            method: "prakash_steel.api.get_last_purchase_invoice_rate.get_last_purchase_invoice_rate",
            args: { item_code: row.item_code },
            callback: function (r) {
                console.log("[Step 3] Server response for last rate:", r.message);
                frappe.model.set_value(cdt, cdn, "custom_last_rate", r.message);
            }
        });

        console.log("Calling Server Script API: get_available_stock");
        frappe.call({
            method: "prakash_steel.api.get_available_stock.get_available_stock",
            args: {
                item_code: row.item_code
            },
            callback: function (res) {
                console.log("Server response for stock:", res); // Corrected typo
                if (res.message !== undefined) {
                    console.log("Available stock received:", res.message);
                    frappe.model.set_value(cdt, cdn, 'custom_quantity_available_in_kg', res.message);
                } else {
                    console.log("No stock returned from server. Setting 0");
                    frappe.model.set_value(cdt, cdn, 'custom_quantity_available_in_kg', 0);
                }
                frm.refresh_field("items");
            },
            error: function (err) {
                console.error("Error fetching stock from server:", err);
                frappe.model.set_value(cdt, cdn, 'custom_quantity_available_in_kg', 0);
                frm.refresh_field("items");
            }
        });
    }
});