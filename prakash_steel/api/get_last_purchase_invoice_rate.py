import frappe


@frappe.whitelist()
def get_last_purchase_invoice_rate(item_code, company=None):
    """
    Fetch the latest purchase rate for an item.

    How the rate is determined:
      Uses the 'last_purchase_rate' field from the Item master, which is
      automatically maintained by ERPNext whenever a Purchase Order,
      Purchase Receipt, or Purchase Invoice is submitted. This ensures
      the rate is always up-to-date regardless of which purchase document
      type was used for the most recent purchase.

      Previous implementation only queried Purchase Invoice Items, which
      returned 0 for items that were purchased via Purchase Orders or
      Purchase Receipts but had no corresponding Purchase Invoice yet.

    Args:
        item_code (str): The Item code to look up.
        company  (str, optional): Accepted for backward compatibility
            but not used — Item.last_purchase_rate is a global field
            maintained by ERPNext at the item level.

    Returns:
        float: The last purchase rate from the Item master, or 0 if not set.
    """
    if not item_code:
        return 0

    # Fetch last_purchase_rate directly from the Item master.
    # This field is updated by ERPNext core on submission of
    # Purchase Order, Purchase Receipt, or Purchase Invoice —
    # whichever was submitted most recently.
    rate = frappe.db.get_value("Item", item_code, "last_purchase_rate")

    return rate or 0
