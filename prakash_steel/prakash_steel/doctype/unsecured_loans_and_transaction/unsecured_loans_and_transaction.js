frappe.ui.form.on("Unsecured Loans and Transaction", {

    // refresh: function (frm) {

       
    //     frm.clear_custom_buttons();

    //     if (
    //         frm.doc.docstatus === 0 &&
    //         frm.doc.unsecured_loan &&
    //         frm.doc.interest_per_annum
    //     ) {
    //         frm.add_custom_button(__("Fetch Today's Interest"), function () {

    //             frappe.call({
    //                 method: "prakash_steel.prakash_steel.doctype.unsecured_loans_and_transaction.unsecured_loans_and_transaction.fetch_today_interest_for_single_doc",
    //                 args: {
    //                     docname: frm.doc.name
    //                 },
    //                 freeze: true,
    //                 freeze_message: __("Fetching interest..."),
    //                 callback: function (r) {
    //                     frm.reload_doc();
    //                     frappe.msgprint(__("Today's interest fetched successfully!"));
    //                 }
    //             });

    //         }, __("Actions"));
    //     }
    // },

    financial_year: function (frm) {

        if (!frm.doc.financial_year) {
            frm.set_value("from_date", "");
            frm.set_value("to_date", "");
            return;
        }

        frappe.db.get_doc("Fiscal Year", frm.doc.financial_year)
            .then(r => {
                frm.set_value("from_date", r.year_start_date);
                frm.set_value("to_date", r.year_end_date);
            });
    },

    interest_per_annum: function (frm) {
        recalculate_interest_amounts(frm);
    }

});


frappe.ui.form.on("Interest Details", {

    closing_balance: function (frm, cdt, cdn) {
        calculate_row_interest(frm, cdt, cdn);
    }

});



function get_daily_rate(frm) {

    if (!frm.doc.from_date || !frm.doc.to_date || !frm.doc.interest_per_annum) {
        return 0;
    }

    let total_days = frappe.datetime.get_day_diff(
        frm.doc.to_date,
        frm.doc.from_date
    ) + 1;

    if (total_days <= 0) return 0;

    return (parseFloat(frm.doc.interest_per_annum) / 100) / total_days;
}


// Single Row Calculation
function calculate_row_interest(frm, cdt, cdn) {

    let row = locals[cdt][cdn];
    let daily_rate = get_daily_rate(frm);

    let closing_balance = parseFloat(row.closing_balance || 0);
    let interest_amount = closing_balance * daily_rate;

    frappe.model.set_value(cdt, cdn, "day_interest", daily_rate * 100);
    frappe.model.set_value(cdt, cdn, "interest_amount", interest_amount.toFixed(2));
}


// Recalculate All Rows
function recalculate_interest_amounts(frm) {

    let daily_rate = get_daily_rate(frm);

    if (!frm.doc.interest_details || frm.doc.interest_details.length === 0) {
        return;
    }

    frm.doc.interest_details.forEach(row => {

        let closing_balance = parseFloat(row.closing_balance || 0);
        let interest_amount = closing_balance * daily_rate;

        frappe.model.set_value(
            row.doctype,
            row.name,
            "day_interest",
            daily_rate * 100
        );

        frappe.model.set_value(
            row.doctype,
            row.name,
            "interest_amount",
            interest_amount.toFixed(2)
        );
    });

}