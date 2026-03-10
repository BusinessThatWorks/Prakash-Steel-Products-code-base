# Copyright (c) 2026, Beetashoke Chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today, flt, add_days
import calendar

class UnsecuredLoansandTransaction(Document):

    def validate(self):
        self.set_from_to_dates()
        self.populate_interest_details()
        self.calculate_totals()
    
    def calculate_totals(self):
        total_interest = 0
        total_tds = 0
        grand_total = 0

        for row in self.interest_details:
            interest_amt = flt(row.interest_amount)
            tds_amt = round(interest_amt * 0.10, 2)
            total_amt = round(interest_amt - tds_amt, 2)

            row.tds_10 = tds_amt
            row.total_amount = total_amt

            total_interest += interest_amt
            total_tds += tds_amt
            grand_total += total_amt

        self.total_interest_amount = round(total_interest, 2)
        self.total_tds_amount = round(total_tds, 2)
        self.grand_total_amount = round(grand_total, 2)

    def set_from_to_dates(self):
        if self.financial_year:
            fy = frappe.get_doc("Fiscal Year", self.financial_year)
            self.from_date = fy.year_start_date
            self.to_date = fy.year_end_date

    def get_interest_rate(self):
        possible_fields = [
            "interest_per_annum",
            "interest__per_annum",
            "interest_per_annum_",
            "interest_percent_per_annum",
            "rate_of_interest",
            "interest_rate",
            "annual_interest_rate",
        ]
        for field in possible_fields:
            val = self.get(field)
            if val is not None:
                return flt(val)

        meta = frappe.get_meta("Unsecured Loans and Transaction")
        for df in meta.fields:
            if "interest" in df.fieldname.lower() and "per" in (df.label or "").lower():
                val = self.get(df.fieldname)
                if val is not None:
                    frappe.logger().info(f"[DEBUG] Interest field found: {df.fieldname} = {val}")
                    return flt(val)

        frappe.logger().warning("[Unsecured Loan] Interest % Per Annum field not found!")
        return 0.0

    def populate_interest_details(self):
        if not self.month:
            return
        if not self.unsecured_loan:
            return
        if not self.from_date:
            return

        annual_rate = self.get_interest_rate()
        if not annual_rate:
            return

        month_number = get_month_number(self.month)
        if not month_number:
            return

        fy_start_year = getdate(self.from_date).year
        entry_year = fy_start_year if month_number >= 4 else fy_start_year + 1

        month_start_date = getdate(f"{entry_year}-{month_number:02d}-01")
        today_date = getdate(today())
        yesterday_date = add_days(today_date, -1)

        days_in_month = calendar.monthrange(entry_year, month_number)[1]
        month_end_date = getdate(f"{entry_year}-{month_number:02d}-{days_in_month:02d}")

        if month_start_date > yesterday_date:
            return

        current_month = today_date.month
        current_year = today_date.year
        is_current_month = (entry_year == current_year and month_number == current_month)

        if is_current_month:
            loop_end_date = min(yesterday_date, month_end_date)
        else:
            loop_end_date = month_end_date

        annual_percent = flt(self.interest_percent)
        monthly_percent = annual_percent / 12.0
        day_interest_percent = round(monthly_percent / days_in_month, 3)

        self.interest_details = [
            row for row in self.interest_details
            if getdate(row.date) >= month_start_date and getdate(row.date) <= month_end_date
        ]

        existing_dates = {getdate(row.date) for row in self.interest_details if row.date}

        current = month_start_date
        while current <= loop_end_date:
            if current not in existing_dates:
                closing_bal = get_closing_balance(self.unsecured_loan, current)
                interest_amt = round(closing_bal * (day_interest_percent / 100), 2)

                self.append("interest_details", {
                    "date": current,
                    "closing_balance": closing_bal,
                    "day_interest": day_interest_percent,
                    "interest_amount": interest_amt,
                })

            current = add_days(current, 1)


def get_month_number(month_name):
    months = {
        "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9,
        "October": 10, "November": 11, "December": 12,
        "January": 1, "February": 2, "March": 3
    }
    return months.get(month_name)


def get_closing_balance(account, date):
    if not account:
        return 0.0

    try:
        result = frappe.db.sql("""
            SELECT
                SUM(credit) - SUM(debit) AS balance
            FROM
                `tabGL Entry`
            WHERE
                account = %(account)s
                AND posting_date <= %(date)s
                AND is_cancelled = 0
                AND docstatus = 1
        """, {
            "account": account,
            "date": str(date)
        }, as_dict=True)

        if result and result[0].get("balance") is not None:
            return abs(flt(result[0]["balance"]))

        return 0.0

    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"GL Balance Fetch Error: {account} on {date}"
        )
        return 0.0


def debug_fieldnames():
    meta = frappe.get_meta("Unsecured Loans and Transaction")
    for df in meta.fields:
        pass


def fetch_daily_interest_for_all_active_docs():
    today_date = getdate(today())

    docs = frappe.get_all(
        "Unsecured Loans and Transaction",
        filters={"docstatus": ["in", [0, 1]]},
        fields=["name", "month", "from_date", "to_date", "financial_year", "unsecured_loan"]
    )

    for doc_info in docs:
        try:
            if doc_info.from_date and doc_info.to_date:
                if not (getdate(doc_info.from_date) <= today_date <= getdate(doc_info.to_date)):
                    continue

            if doc_info.month:
                month_number = get_month_number(doc_info.month)
                if month_number and today_date.month != month_number:
                    continue

            doc = frappe.get_doc("Unsecured Loans and Transaction", doc_info.name)

            annual_rate = doc.get_interest_rate()
            if not annual_rate:
                continue

            daily_rate = annual_rate / 100.0 / 12.0 / 30.0
            existing_dates = {getdate(row.date) for row in doc.interest_details if row.date}

            if today_date not in existing_dates:
                closing_bal = get_closing_balance(doc.unsecured_loan, today_date)
                interest_amt = round(flt(closing_bal) * daily_rate, 2)
                tds_amt = round(interest_amt * 0.10, 2)
                total_amt = round(interest_amt - tds_amt, 2)

                doc.append("interest_details", {
                    "date": today_date,
                    "closing_balance": closing_bal,
                    "day_interest": round(daily_rate * 100, 6),
                    "interest_amount": interest_amt,
                    "tds_10": tds_amt,
                    "total_amount": total_amt
                })

                doc.flags.ignore_validate = True
                doc.flags.ignore_permissions = True
                doc.save()
                frappe.db.commit()

        except Exception:
            frappe.log_error(
                message=frappe.get_traceback(),
                title=f"Interest Fetch Error: {doc_info.name}"
            )
            frappe.db.rollback()