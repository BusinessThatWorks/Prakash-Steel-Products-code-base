// Copyright (c) 2026, Beetashoke Chakraborty and contributors
// For license information, please see license.txt

frappe.ui.form.on("Unsecured Loans and Transaction", {

    onload: function (frm) {
        load_unsecured_loan_options(frm);
    },

    refresh: function (frm) {
        load_unsecured_loan_options(frm);
    },

    financial_year: function (frm) {
        if (!frm.doc.financial_year) {
            frm.set_value("from_date", "");
            frm.set_value("to_date", "");
            return;
        }
        // Automatically fetch start and end dates based on the Fiscal Year
        frappe.db.get_doc("Fiscal Year", frm.doc.financial_year).then(r => {
            frm.set_value("from_date", r.year_start_date);
            frm.set_value("to_date", r.year_end_date);
        });
    }

});

// ----------------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------------

/**
 * Loads and groups Account options for the 'unsecured_loan' field 
 * based on specific parent accounts.
 */
async function load_unsecured_loan_options(frm) {
    try {
        const result = await frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Account",
                filters: [
                    ["parent_account", "in", [
                        "Loan From Director - PSPL",
                        "Loan From Shareholders - PSPL",
                        "Unsecured Loan - PSPL"
                    ]],
                    ["is_group", "=", 0]
                ],
                fields: ["name", "account_name", "parent_account"],
                order_by: "parent_account asc, account_name asc",
                limit: 500
            }
        });

        if (!result || !result.message) return;

        const accounts    = result.message;
        const directors   = accounts.filter(a => a.parent_account === "Loan From Director - PSPL");
        const shareholders = accounts.filter(a => a.parent_account === "Loan From Shareholders - PSPL");
        const unsecured   = accounts.filter(a => a.parent_account === "Unsecured Loan - PSPL");

        let options = [""];

        if (directors.length > 0) {
            options.push("--- Loan From Director ---");
            directors.forEach(acc => options.push(acc.name));
        }
        if (shareholders.length > 0) {
            options.push("--- Loan From Shareholders ---");
            shareholders.forEach(acc => options.push(acc.name));
        }
        if (unsecured.length > 0) {
            options.push("--- Unsecured Loan ---");
            unsecured.forEach(acc => options.push(acc.name));
        }

        frm.set_df_property("unsecured_loan", "options", options.join("\n"));

    } catch (err) {
        console.error("Unsecured Loan options load error:", err);
    }
}