"""
Sales Invoice Automation
This module handles automatic Stock Entry creation when a Sales Invoice is submitted.
"""

import frappe
from frappe import _


def validate_sales_order_items_required(doc, method=None):
    """
    Validate that all Sales Invoice Items must have sales_order field populated.
    This ensures that only items coming from Sales Order can exist in the Sales Invoice.

    Args:
            doc: Sales Invoice document
            method: Event method (validate)
    """
    # Skip if no items
    if not doc.items:
        return

    # Check if this is a Sales Order-based invoice
    # (at least one item has sales_order populated)
    has_sales_order_items = any(item.get("sales_order") for item in doc.items)

    # If this is a Sales Order-based invoice, validate all items
    if has_sales_order_items:
        invalid_items = []
        for idx, item in enumerate(doc.items, start=1):
            if not item.get("sales_order"):
                invalid_items.append(
                    _("Row {0}: Item {1}").format(
                        idx, item.item_code or item.item_name or _("N/A")
                    )
                )

        if invalid_items:
            error_message = _(
                "Only items linked to Sales Order are allowed in this Sales Invoice."
            )
            error_message += "\n\n" + _("Items without Sales Order reference:")
            error_message += "\n" + "\n".join(invalid_items)
            frappe.throw(error_message, title=_("Validation Error"))


def create_stock_entries_on_submit(doc, method=None):
    """
    Automatically create two Stock Entries when Sales Invoice is submitted:
    1. Material Receipt (Stock In)
    2. Material Issue (Stock Out)

    Args:
            doc: Sales Invoice document
            method: Event method (on_submit)
    """
    # Skip if no items
    if not doc.items:
        return

    # Check if Stock Entries already created (prevent duplicates)
    existing_stock_entries = frappe.db.exists(
        "Stock Entry",
        {
            "sales_invoice": doc.name,
            "docstatus": ["!=", 2],  # Exclude cancelled entries
        },
    )

    if existing_stock_entries:
        frappe.msgprint(_("Stock Entries already exist for this Sales Invoice."))
        return

    try:
        # Step 1: Create Material Receipt Stock Entry
        material_receipt = create_material_receipt(doc)

        # Step 2: Create Material Issue Stock Entry
        material_issue = create_material_issue(doc)

        # Success message
        frappe.msgprint(
            _(
                "Stock Entries created successfully: {0} (Material Receipt) and {1} (Material Issue)"
            ).format(material_receipt.name, material_issue.name),
            indicator="green",
        )

    except Exception as e:
        frappe.log_error(
            title=_("Stock Entry Creation Failed for Sales Invoice {0}").format(
                doc.name
            ),
            message=frappe.get_traceback(),
        )
        frappe.throw(
            _(
                "Failed to create Stock Entries for Sales Invoice {0}. Error: {1}"
            ).format(doc.name, str(e))
        )


def create_material_receipt(sales_invoice):
    """
    Create Material Receipt Stock Entry from Sales Invoice

    Args:
            sales_invoice: Sales Invoice document

    Returns:
            Stock Entry document (Material Receipt)
    """
    # Create new Stock Entry
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Receipt"
    stock_entry.purpose = "Material Receipt"
    stock_entry.company = sales_invoice.company
    stock_entry.posting_date = sales_invoice.posting_date
    stock_entry.posting_time = sales_invoice.posting_time

    # Link to Sales Invoice using standard field
    stock_entry.sales_invoice = sales_invoice.name

    # Set remarks
    stock_entry.set_posting_time = 1
    stock_entry.remarks = _(
        "Material Receipt created automatically from Sales Invoice {0}"
    ).format(sales_invoice.name)

    # Add items from Sales Invoice
    for item in sales_invoice.items:
        # Skip items where custom_tolerance_qty is 0 or empty
        if not item.get("custom_tolerance_qty") or item.custom_tolerance_qty == 0:
            continue

        stock_entry.append(
            "items",
            {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "description": item.description,
                "qty": item.custom_tolerance_qty,
                "uom": item.uom,
                "stock_uom": item.stock_uom,
                "conversion_factor": item.conversion_factor or 1,
                "t_warehouse": "Virtual Warehouse - PSPL",  # Target warehouse for Material Receipt
                "basic_rate": item.rate,
                "basic_amount": item.amount,
                "expense_account": item.expense_account,
                "cost_center": item.cost_center,
            },
        )

    # Check if any items were added
    if not stock_entry.items:
        frappe.throw(
            _("No items with custom_tolerance_qty found in Sales Invoice {0}").format(
                sales_invoice.name
            )
        )

    # Insert and submit the Stock Entry
    stock_entry.insert(ignore_permissions=True)
    stock_entry.submit()

    return stock_entry


def create_material_issue(sales_invoice):
    """
    Create Material Issue Stock Entry from Sales Invoice

    Args:
            sales_invoice: Sales Invoice document

    Returns:
            Stock Entry document (Material Issue)
    """
    # Create new Stock Entry
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Issue"
    stock_entry.purpose = "Material Issue"
    stock_entry.company = sales_invoice.company
    stock_entry.posting_date = sales_invoice.posting_date
    stock_entry.posting_time = sales_invoice.posting_time

    # Link to Sales Invoice using standard field
    stock_entry.sales_invoice = sales_invoice.name

    # Set remarks
    stock_entry.set_posting_time = 1
    stock_entry.remarks = _(
        "Material Issue created automatically from Sales Invoice {0}"
    ).format(sales_invoice.name)

    # Add items from Sales Invoice
    for item in sales_invoice.items:
        # Skip items where custom_tolerance_qty is 0 or empty
        if not item.get("custom_tolerance_qty") or item.custom_tolerance_qty == 0:
            continue

        stock_entry.append(
            "items",
            {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "description": item.description,
                "qty": item.custom_tolerance_qty,
                "uom": item.uom,
                "stock_uom": item.stock_uom,
                "conversion_factor": item.conversion_factor or 1,
                "s_warehouse": "Virtual Warehouse - PSPL",  # Source warehouse for Material Issue
                "basic_rate": item.rate,
                "basic_amount": item.amount,
                "expense_account": item.expense_account,
                "cost_center": item.cost_center,
            },
        )

    # Check if any items were added
    if not stock_entry.items:
        frappe.throw(
            _("No items with custom_tolerance_qty found in Sales Invoice {0}").format(
                sales_invoice.name
            )
        )

    # Insert and submit the Stock Entry
    stock_entry.insert(ignore_permissions=True)
    stock_entry.submit()

    return stock_entry
