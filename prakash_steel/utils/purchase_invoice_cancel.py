# import frappe
# from frappe import _


# def validate_cancel_reason(doc, method=None):
#     """Server-side guard: block cancellation if Cancel Reason is missing.

#     This runs for ALL cancellation paths, including list view bulk cancel.
#     """
#     reason = (getattr(doc, "custom_cancel_reason", "") or "").strip()
#     if not reason:
#         frappe.throw(
#             _("Please enter Cancel Reason before cancelling this Purchase Invoice."),
#             title=_("Cancel Reason Required"),
#         )


# @frappe.whitelist()
# def cancel_purchase_invoice_with_reason(name: str, reason: str):
#     """Cancel a submitted Purchase Invoice after capturing a Cancel Reason."""
#     if not reason or not str(reason).strip():
#         frappe.throw(_("Cancel Reason is required."), title=_("Missing Cancel Reason"))

#     doc = frappe.get_doc("Purchase Invoice", name)

#     if doc.docstatus != 1:
#         frappe.throw(
#             _("Only submitted Purchase Invoices can be cancelled."),
#             title=_("Invalid Document Status"),
#         )

#     # Store the reason directly in the database to bypass update-after-submit validation
#     frappe.db.set_value(
#         "Purchase Invoice",
#         name,
#         "custom_cancel_reason",
#         reason.strip(),
#         update_modified=False,
#     )

#     # Reload and perform the cancel; standard ERPNext on_cancel will run
#     doc = frappe.get_doc("Purchase Invoice", name)
#     doc.cancel()

#     return {"name": doc.name, "docstatus": doc.docstatus}




import frappe
from frappe import _


def clear_cancel_reason_on_amend(doc, method=None):
    """Clear cancel reason on an amended (draft) Purchase Invoice."""
    if doc.amended_from and doc.docstatus == 0 and doc.custom_cancel_reason:
        doc.custom_cancel_reason = ""


def validate_cancel_reason(doc, method=None):
    """Server-side guard: block cancellation if Cancel Reason is missing.

    This runs for ALL cancellation paths, including list view bulk cancel.
    """
    reason = (getattr(doc, "custom_cancel_reason", "") or "").strip()
    if not reason:
        frappe.throw(
            _("Please enter Cancel Reason before cancelling this Purchase Invoice."),
            title=_("Cancel Reason Required"),
        )


@frappe.whitelist()
def set_purchase_invoice_cancel_reason(name: str, reason: str):
    """Set cancel reason on Purchase Invoice before running standard cancel flow."""
    if not reason or not str(reason).strip():
        frappe.throw(_("Cancel Reason is required."), title=_("Missing Cancel Reason"))

    doc = frappe.get_doc("Purchase Invoice", name)

    if doc.docstatus != 1:
        frappe.throw(
            _("Only submitted Purchase Invoices can have a cancel reason set."),
            title=_("Invalid Document Status"),
        )

    frappe.db.set_value(
        "Purchase Invoice",
        name,
        "custom_cancel_reason",
        reason.strip(),
        update_modified=False,
    )

    return {"name": doc.name}


@frappe.whitelist()
def cancel_purchase_invoice_with_reason(name: str, reason: str):
    """Cancel a submitted Purchase Invoice after capturing a Cancel Reason."""
    if not reason or not str(reason).strip():
        frappe.throw(_("Cancel Reason is required."), title=_("Missing Cancel Reason"))

    doc = frappe.get_doc("Purchase Invoice", name)

    if doc.docstatus != 1:
        frappe.throw(
            _("Only submitted Purchase Invoices can be cancelled."),
            title=_("Invalid Document Status"),
        )

    # Store the reason directly in the database to bypass update-after-submit validation
    frappe.db.set_value(
        "Purchase Invoice",
        name,
        "custom_cancel_reason",
        reason.strip(),
        update_modified=False,
    )

    # Reload and perform the cancel; standard ERPNext on_cancel will run
    doc = frappe.get_doc("Purchase Invoice", name)
    doc.cancel()

    return {"name": doc.name, "docstatus": doc.docstatus}








