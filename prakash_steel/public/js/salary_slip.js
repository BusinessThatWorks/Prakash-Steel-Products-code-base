frappe.ui.form.on('Salary Slip', {
    custom_extra_payable_days: function(frm) {
        // Get user input
        let extra_days = frm.doc.custom_extra_payable_days || 0;

        // Base amount (replace with your actual field)
        let monthly_amount = frm.doc.custom_monthly_amount || 0;

        // Get month from a date field or current date
        let base_date = frm.doc.posting_date || frappe.datetime.now_date();

        // Calculate days in that month
        let dateObj = new Date(base_date);
        let year = dateObj.getFullYear();
        let month = dateObj.getMonth() + 1; // JS months are 0-based
        let days_in_month = new Date(year, month, 0).getDate();

        // Calculate prorated amount
        let daily_rate = monthly_amount / days_in_month;
        let extra_amount = daily_rate * extra_days;

        // Set the calculated amount
        frm.set_value('custom_extra_payable_amount', extra_amount);
    }
});
