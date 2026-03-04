# Copyright (c) 2026
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, flt, add_days
import calendar


class UnsecuredLoansandTransaction(Document):

    def validate(self):
        self.set_from_to_dates()
        self.populate_interest_details()
        self.calculate_total_interest()

    def set_from_to_dates(self):
        if self.financial_year:
            fy = frappe.get_doc("Fiscal Year", self.financial_year)
            self.from_date = fy.year_start_date
            self.to_date = fy.year_end_date

    def calculate_total_interest(self):
        self.total_interest_amount = round(
            sum(flt(row.interest_amount) for row in self.interest_details),
            2
        )

    def populate_interest_details(self):

        if not (self.month and self.unsecured_loan and self.from_date and self.to_date and self.interest_percent):
            return

        month_number = get_month_number(self.month)
        fy_start_date = getdate(self.from_date)
        fy_end_date = getdate(self.to_date)

        # FY logic (April–March)
        entry_year = fy_end_date.year if month_number <= 3 else fy_start_date.year

        days_in_month = calendar.monthrange(entry_year, month_number)[1]

        month_start_date = getdate(f"{entry_year}-{month_number:02d}-01")
        month_end_date = getdate(f"{entry_year}-{month_number:02d}-{days_in_month}")

        annual_percent = flt(self.interest_percent)

        days_in_year = 366 if calendar.isleap(entry_year) else 365

        self.interest_details = []

        current = month_start_date

        while current <= month_end_date:

            has_transaction = frappe.db.exists("GL Entry", {
                "account": self.unsecured_loan,
                "posting_date": current,
                "is_cancelled": 0,
                "docstatus": 1
            })

            if has_transaction:
                closing_bal = get_cumulative_balance(self.unsecured_loan, current)

                interest_amt = (closing_bal * annual_percent) / 100.0 / days_in_year
            else:
                closing_bal = 0.0
                interest_amt = 0.0

            self.append("interest_details", {
                "date": current,
                "closing_balance": round(closing_bal),
                "day_interest": round(annual_percent / days_in_year, 6),
                "interest_amount": round(interest_amt,2)
            })

            current = add_days(current, 1)


def get_month_number(month_name):
    months = {
        "January": 1, "February": 2, "March": 3,
        "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9,
        "October": 10, "November": 11, "December": 12
    }
    return months.get(month_name)


def get_cumulative_balance(account, date):

    if not account:
        return 0.0

    result = frappe.db.sql("""
        SELECT 
            COALESCE(SUM(credit),0) - COALESCE(SUM(debit),0) AS balance
        FROM `tabGL Entry`
        WHERE account = %(account)s
        AND posting_date <= %(date)s
        AND is_cancelled = 0
        AND docstatus = 1
    """, {
        "account": account,
        "date": str(date)
    }, as_dict=True)

    if result and result[0]["balance"] is not None:
        return abs(flt(result[0]["balance"]))

    return 0.0