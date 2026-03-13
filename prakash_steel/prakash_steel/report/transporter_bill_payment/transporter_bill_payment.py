import frappe
from frappe.utils import flt, getdate


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": "Bill Date",
            "fieldname": "bill_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "Vendor Name",
            "fieldname": "vendor_name",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Bill Number",
            "fieldname": "bill_no",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": "Truck No",
            "fieldname": "truck_no",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": "Transporter Name",
            "fieldname": "transporter_name",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Billing Quantity",
            "fieldname": "billing_qty",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": "Receiving Quantity",
            "fieldname": "receiving_qty",
            "fieldtype": "Float",
            "width": 140,
        },
        {
            "label": "Shortage Quantity",
            "fieldname": "shortage_qty",
            "fieldtype": "Float",
            "width": 140,
        },
    ]


def get_data(filters):
    conditions = ["pi.docstatus = 1", "ifnull(pi.transporter_name, '') != ''"]
    values = {}

    # Date range filter on posting_date (Bill Date)
    if filters.get("from_date"):
        conditions.append("pi.posting_date >= %(from_date)s")
        values["from_date"] = getdate(filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("pi.posting_date <= %(to_date)s")
        values["to_date"] = getdate(filters.get("to_date"))

    # Transporter Name filter
    if filters.get("transporter_name"):
        conditions.append("pi.transporter_name = %(transporter_name)s")
        values["transporter_name"] = filters.get("transporter_name")

    where_clause = " AND ".join(conditions)

    # We fetch data at the Purchase Invoice Item level so that
    # Billing Qty comes from the item.qty and Receiving Qty from
    # the linked Purchase Receipt.
    #
    # Assumptions (based on your description):
    # - `vehicle_no` is on Purchase Invoice (pi.vehicle_no)
    # - `transporter_name` is on Purchase Invoice (pi.transporter_name)
    # - `bill_no` is on Purchase Invoice (pi.bill_no)
    # - `purchase_receipt` is on Purchase Invoice Item (pii.purchase_receipt)
    # - Receiving qty is taken from Purchase Receipt Item.qty for that receipt & item

    query = f"""
        SELECT
            pi.posting_date AS bill_date,
            pi.supplier AS vendor_name,
            pi.bill_no AS bill_no,
            pi.vehicle_no AS truck_no,
            pi.transporter_name AS transporter_name,
            pii.qty AS billing_qty,
            -- Receiving qty from Purchase Receipt Item
            IFNULL(
                (
                    SELECT SUM(pri.qty)
                    FROM `tabPurchase Receipt Item` pri
                    WHERE pri.parent = pii.purchase_receipt
                      AND pri.item_code = pii.item_code
                ),
                0
            ) AS receiving_qty
        FROM
            `tabPurchase Invoice` pi
        INNER JOIN
            `tabPurchase Invoice Item` pii
        ON
            pi.name = pii.parent
        WHERE
            {where_clause}
        ORDER BY
            pi.posting_date ASC,
            pi.name ASC
    """

    result = frappe.db.sql(query, values=values, as_dict=True)

    for row in result:
        billing_qty = flt(row.get("billing_qty") or 0)
        receiving_qty = flt(row.get("receiving_qty") or 0)
        row["shortage_qty"] = billing_qty - receiving_qty

    return result

