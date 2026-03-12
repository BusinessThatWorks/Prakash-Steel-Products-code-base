# Copyright (c) 2026, Beetashoke Chakraborty and contributors
# For license information, please see license.txt

import calendar
import frappe
from frappe.utils import flt, getdate, today, add_days


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 110},
        {"label": "Date", "fieldname": "detail_date", "fieldtype": "Date", "width": 110},
        {"label": "Account Head", "fieldname": "unsecured_loan", "fieldtype": "Data", "width": 250},
        {"label": "Interest % Per Annum", "fieldname": "interest_percent", "fieldtype": "Float", "width": 150},
        {"label": "Closing Balance", "fieldname": "closing_balance", "fieldtype": "Currency", "width": 150},
        {"label": "Interest per Day", "fieldname": "day_interest", "fieldtype": "Float", "width": 130},
        {"label": "Interest Amount", "fieldname": "interest_amount", "fieldtype": "Currency", "width": 150},
        {"label": "TDS (10%)", "fieldname": "tds_10", "fieldtype": "Currency", "width": 120},
        {"label": "Total Amount", "fieldname": "total_amount", "fieldtype": "Currency", "width": 150},
        {
            "label": "Voucher",
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Unsecured Loans and Transaction",
            "width": 200,
        },
    ]


def get_closing_balance(account, date):
    """Fetch cumulative closing balance from GL Entry up to given date."""
    if not account:
        return 0.0

    result = frappe.db.sql(
        """
        SELECT SUM(credit) - SUM(debit) AS balance
        FROM `tabGL Entry`
        WHERE
            account = %(account)s
            AND posting_date <= %(date)s
            AND is_cancelled = 0
            AND docstatus = 1
        """,
        {"account": account, "date": str(date)},
        as_dict=True,
    )

    if result and result[0].get("balance") is not None:
        return abs(flt(result[0]["balance"]))

    return 0.0


# Month mapping
MONTH_MAP = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def get_data(filters):
    conditions = []
    values = {}

    # Account Head Filter
    if filters.get("account_head"):
        conditions.append("unsecured_loan = %(account_head)s")
        values["account_head"] = filters["account_head"]

    # Financial Year Filter
    if filters.get("financial_year"):
        conditions.append("financial_year = %(financial_year)s")
        values["financial_year"] = filters["financial_year"]

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    records = frappe.db.sql(
        f"""
        SELECT
            name,
            unsecured_loan,
            financial_year,
            from_date,
            to_date,
            interest_percent
        FROM
            `tabUnsecured Loans and Transaction`
        {where_clause}
        ORDER BY
            unsecured_loan ASC,
            from_date ASC
        """,
        values,
        as_dict=True,
    )

    yesterday = add_days(getdate(today()), -1)

    # Month Filter
    selected_month = None
    if filters.get("month"):
        selected_month = MONTH_MAP.get(filters.get("month"))

    data = []

    for rec in records:

        from_date = getdate(rec["from_date"])
        to_date = getdate(rec["to_date"])
        interest_pct = flt(rec["interest_percent"])
        account = rec["unsecured_loan"]

        loop_start = from_date
        loop_end = min(to_date, yesterday)

        if selected_month:
            year = loop_start.year
            month_start = getdate(f"{year}-{selected_month}-01")
            month_end = add_days(month_start, calendar.monthrange(year, selected_month)[1] - 1)

            loop_start = max(loop_start, month_start)
            loop_end = min(loop_end, month_end)

        if loop_start > loop_end:
            continue

        is_first_row = True
        current = loop_start

        while current <= loop_end:

            month_name = calendar.month_name[current.month]
            days_in_month = calendar.monthrange(current.year, current.month)[1]

            # Daily Interest Calculation
            day_interest_pct = round((interest_pct / 12.0) / days_in_month, 6)

            closing_bal = get_closing_balance(account, current)

            interest_amount = round(closing_bal * (day_interest_pct / 100), 2)

            tds_10 = round(interest_amount * 0.10, 2)

            total_amount = round(interest_amount - tds_10, 2)

            row = {
                "name": rec["name"] if is_first_row else "",
                "unsecured_loan": account if is_first_row else "",
                "interest_percent": interest_pct if is_first_row else None,
                "month": month_name,
                "detail_date": current,
                "closing_balance": closing_bal,
                "day_interest": day_interest_pct,
                "interest_amount": interest_amount,
                "tds_10": tds_10,
                "total_amount": total_amount,
            }

            data.append(row)

            is_first_row = False
            current = add_days(current, 1)

    return data