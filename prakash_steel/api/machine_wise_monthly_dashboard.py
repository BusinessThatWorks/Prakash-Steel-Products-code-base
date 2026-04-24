import frappe
from frappe.utils import cint
from frappe.utils import flt, getdate


MONTH_LABELS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


@frappe.whitelist()
def get_machine_wise_monthly_data(fiscal_year=None, machine_name=None):
    fiscal_year_doc = _get_fiscal_year_doc(fiscal_year)
    month_periods = _get_fiscal_month_periods(fiscal_year_doc)

    machine_conditions = ""
    machine_params = {}
    if machine_name:
        machine_conditions = "WHERE name = %(machine_name)s"
        machine_params["machine_name"] = machine_name

    machine_rows = frappe.db.sql(
        f"""
        SELECT name
        FROM `tabMachine Master`
        {machine_conditions}
        ORDER BY name
        """,
        machine_params,
        as_dict=True,
    )
    machine_names = [row.name for row in machine_rows if row.get("name")]

    production_conditions = ""
    production_params = {
        "from_date": fiscal_year_doc.year_start_date,
        "to_date": fiscal_year_doc.year_end_date,
    }
    if machine_name:
        production_conditions = "AND machine_name = %(machine_name)s"
        production_params["machine_name"] = machine_name

    production_rows = frappe.db.sql(
        f"""
        SELECT
            production_date,
            MONTH(production_date) AS month_number,
            machine_name,
            fg_weight
        FROM `tabBright Bar Production`
        WHERE docstatus = 1
          AND production_date BETWEEN %(from_date)s AND %(to_date)s
          AND machine_name IS NOT NULL
          AND machine_name != ''
          {production_conditions}
        ORDER BY production_date ASC
        """,
        production_params,
        as_dict=True,
    )

    used_machines = []
    for row in production_rows:
        machine_name = row.get("machine_name")
        if machine_name and machine_name not in used_machines:
            used_machines.append(machine_name)

    for machine in used_machines:
        if machine not in machine_names:
            machine_names.append(machine)

    matrix = {
        period["month_number"]: {
            machine: {"fg_weight": 0, "amount": 0}
            for machine in machine_names
        }
        for period in month_periods
    }

    rate_lookup = _build_machine_rate_lookup(machine_names)
    for row in production_rows:
        month_number = cint(row.get("month_number"))
        machine_name = row.get("machine_name")
        if month_number in matrix and machine_name in matrix[month_number]:
            fg_weight = flt(row.get("fg_weight"))
            production_date = getdate(row.get("production_date"))
            rate = _get_rate_for_date(rate_lookup.get(machine_name, []), production_date)
            matrix[month_number][machine_name]["fg_weight"] += fg_weight
            matrix[month_number][machine_name]["amount"] += fg_weight * rate

    data = []
    for period in month_periods:
        month_no = period["month_number"]
        row = {"month": period["label"], "month_number": month_no}
        for machine in machine_names:
            row[f"{machine}__fg_weight"] = matrix[month_no][machine]["fg_weight"]
            row[f"{machine}__amount"] = matrix[month_no][machine]["amount"]
        data.append(row)

    return {
        "fiscal_year": fiscal_year_doc.name,
        "from_date": fiscal_year_doc.year_start_date,
        "to_date": fiscal_year_doc.year_end_date,
        "machines": machine_names,
        "rows": data,
    }


def _get_fiscal_year_doc(fiscal_year=None):
    if fiscal_year:
        return frappe.get_doc("Fiscal Year", fiscal_year)

    default_fy = (
        frappe.defaults.get_user_default("fiscal_year")
        or frappe.defaults.get_global_default("fiscal_year")
    )
    if default_fy:
        return frappe.get_doc("Fiscal Year", default_fy)

    today = frappe.utils.nowdate()
    fy_name = frappe.db.get_value(
        "Fiscal Year",
        {
            "year_start_date": ("<=", today),
            "year_end_date": (">=", today),
        },
        "name",
    )
    if fy_name:
        return frappe.get_doc("Fiscal Year", fy_name)

    # Final fallback to latest fiscal year.
    latest_fy = frappe.db.get_value("Fiscal Year", {}, "name", order_by="year_end_date desc")
    if latest_fy:
        return frappe.get_doc("Fiscal Year", latest_fy)

    frappe.throw("No Fiscal Year found. Please create Fiscal Year first.")


def _get_fiscal_month_periods(fiscal_year_doc):
    periods = []
    current = fiscal_year_doc.year_start_date
    for _ in range(12):
        periods.append(
            {
                "month_number": current.month,
                "label": current.strftime("%b-%Y"),
            }
        )
        current = frappe.utils.add_months(current, 1)
    return periods


def _build_machine_rate_lookup(machine_names):
    if not machine_names:
        return {}

    rate_rows = frappe.db.sql(
        """
        SELECT
            parent AS machine_name,
            rate_application_date,
            rate
        FROM `tabMachine Master Table`
        WHERE parent IN %(machine_names)s
        ORDER BY parent, rate_application_date ASC, idx ASC
        """,
        {"machine_names": tuple(machine_names)},
        as_dict=True,
    )

    lookup = {machine: [] for machine in machine_names}
    for row in rate_rows:
        machine_name = row.get("machine_name")
        if machine_name in lookup:
            lookup[machine_name].append(
                {
                    "rate_application_date": getdate(row.get("rate_application_date")),
                    "rate": flt(row.get("rate")),
                }
            )
    return lookup


def _get_rate_for_date(rate_rows, production_date):
    """Return latest applicable rate as on production date."""
    applicable_rate = 0
    for rate_row in rate_rows:
        if rate_row["rate_application_date"] <= production_date:
            applicable_rate = rate_row["rate"]
        else:
            break
    return applicable_rate
