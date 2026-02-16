# Copyright (c) 2025, Prakash Steel and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from erpnext.accounts.doctype.payment_reconciliation.payment_reconciliation import PaymentReconciliation


class CustomPaymentReconciliation(PaymentReconciliation):
	"""Custom Payment Reconciliation that populates custom_supplier_invoice_no from Purchase Invoice bill_no"""

	def add_invoice_entries(self, non_reconciled_invoices):
		# Populate 'invoices' with JVs and Invoices to reconcile against
		self.set("invoices", [])

		# Collect Purchase Invoice names to fetch bill_no in batch
		purchase_invoice_names = [
			entry.get("voucher_no")
			for entry in non_reconciled_invoices
			if entry.get("voucher_type") == "Purchase Invoice"
		]

		# Fetch bill_no for all Purchase Invoices in one query
		bill_no_map = {}
		if purchase_invoice_names:
			bill_no_list = frappe.db.get_all(
				"Purchase Invoice",
				filters={"name": ("in", purchase_invoice_names)},
				fields=["name", "bill_no"],
				as_list=1,
			)
			# Convert list of tuples to dictionary
			bill_no_map = {name: bill_no for name, bill_no in bill_no_list}

		for entry in non_reconciled_invoices:
			inv = self.append("invoices", {})
			inv.invoice_type = entry.get("voucher_type")
			inv.invoice_number = entry.get("voucher_no")
			inv.invoice_date = entry.get("posting_date")
			inv.amount = flt(entry.get("invoice_amount"))
			inv.currency = entry.get("currency")
			inv.outstanding_amount = flt(entry.get("outstanding_amount"))
			
			# Populate custom_supplier_invoice_no from Purchase Invoice bill_no
			if entry.get("voucher_type") == "Purchase Invoice":
				inv.custom_supplier_invoice_no = bill_no_map.get(entry.get("voucher_no"))

