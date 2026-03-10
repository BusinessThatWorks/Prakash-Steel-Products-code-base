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

function calculate_row_interest(frm, cdt, cdn) {


let row = locals[cdt][cdn];
let daily_rate = get_daily_rate(frm);

let closing_balance = parseFloat(row.closing_balance || 0);
let interest_amount = closing_balance * daily_rate;

frappe.model.set_value(cdt, cdn, "day_interest", daily_rate * 100);
frappe.model.set_value(cdt, cdn, "interest_amount", interest_amount.toFixed(2));


}

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

async function load_unsecured_loan_options(frm) {


try {
    const result = await frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Account',
            filters: [
                ['parent_account', 'in', [
                    'Loan From Director - PSPL',
                    'Loan From Shareholders - PSPL',
                    'Unsecured Loan - PSPL'
                ]],
                ['is_group', '=', 0]
            ],
            fields: ['name', 'account_name', 'parent_account'],
            order_by: 'parent_account asc, account_name asc',
            limit: 500
        }
    });

    if (!result || !result.message) return;

    const accounts = result.message;

    const directors    = accounts.filter(a => a.parent_account === 'Loan From Director - PSPL');
    const shareholders = accounts.filter(a => a.parent_account === 'Loan From Shareholders - PSPL');
    const unsecured    = accounts.filter(a => a.parent_account === 'Unsecured Loan - PSPL');

    let options = [''];

    if (directors.length > 0) {
        options.push('--- Loan From Director ---');
        directors.forEach(acc => options.push(acc.name));
    }

    if (shareholders.length > 0) {
        options.push('--- Loan From Shareholders ---');
        shareholders.forEach(acc => options.push(acc.name));
    }

    if (unsecured.length > 0) {
        options.push('--- Unsecured Loan ---');
        unsecured.forEach(acc => options.push(acc.name));
    }

    frm.set_df_property('unsecured_loan', 'options', options.join('\n'));

} catch (err) {
    console.error('Unsecured Loan options load error:', err);
}


}
