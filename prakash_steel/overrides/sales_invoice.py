# Copyright (c) 2025, beetashoke chakraborty and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from frappe.utils import flt, nowdate, nowtime
from erpnext.stock.stock_ledger import get_previous_sle


class CustomSalesInvoice(SalesInvoice):
	"""Custom Sales Invoice that automatically creates Material Receipt Stock Entry
	for items with insufficient stock when custom_stock_in_for_weight_variance is checked.
	"""

	def on_submit(self):
		"""Override on_submit to create Material Receipt for items with insufficient stock
		before the normal submit process runs.
		"""
		# Check if custom_stock_in_for_weight_variance is set (works for both checkbox and select field)
		custom_field_value = self.get("custom_stock_in_for_weight_variance")
		if custom_field_value and custom_field_value not in [None, "", 0, "0", "No"]:
			# Only process if update_stock is enabled
			if self.update_stock:
				self.create_material_receipt_for_insufficient_stock()

		# Call parent on_submit to continue with normal submit process
		super().on_submit()

	def create_material_receipt_for_insufficient_stock(self):
		"""Create Material Receipt Stock Entry for items with insufficient stock in warehouse."""
		if not self.items:
			return

		items_to_receipt = []
		stock_entry_items = []

		# Check each item for insufficient stock
		for item in self.get("items"):
			if not item.item_code or not item.warehouse:
				continue

			# Skip if item is not a stock item
			if not frappe.get_cached_value("Item", item.item_code, "is_stock_item"):
				continue

			# Get required quantity in stock UOM
			# Use stock_qty if available (already in stock UOM), otherwise convert qty to stock UOM
			if hasattr(item, 'stock_qty') and item.stock_qty:
				required_qty = flt(item.stock_qty, item.precision("stock_qty"))
			else:
				# Convert qty to stock UOM using conversion_factor
				conversion_factor = flt(item.conversion_factor) or 1.0
				required_qty = flt(item.qty, item.precision("qty")) * conversion_factor
			
			if required_qty <= 0:
				continue

			# Get available stock from warehouse
			available_qty = self.get_available_stock(item.item_code, item.warehouse)

			# Validation: If any item has 0 quantity in warehouse, throw error and prevent submission
			if available_qty == 0:
				frappe.throw(
					_("Item {0} has 0 quantity in warehouse {1}. Cannot create Material Receipt for items with zero stock. Please add stock manually before submitting.").format(
						frappe.bold(item.item_code),
						frappe.bold(item.warehouse)
					),
					title=_("Zero Stock Error")
				)

			# Check if stock is insufficient
			if available_qty < required_qty:
				shortage_qty = required_qty - available_qty
				items_to_receipt.append({
					"item": item,
					"shortage_qty": shortage_qty,
					"available_qty": available_qty,
					"required_qty": required_qty
				})

		# If no items need stock receipt, return
		if not items_to_receipt:
			return

		# Create Material Receipt Stock Entry
		try:
			# Get company from Sales Invoice
			company = self.company

			# Get posting date and time
			posting_date = self.posting_date or nowdate()
			posting_time = self.posting_time or nowtime()

			# Prepare items for Stock Entry
			for receipt_item in items_to_receipt:
				item = receipt_item["item"]
				shortage_qty = receipt_item["shortage_qty"]

				# Get item details
				item_doc = frappe.get_doc("Item", item.item_code)
				stock_uom = item_doc.stock_uom or item.uom or "Nos"
				
				# Calculate rate in stock UOM if needed
				conversion_factor = flt(item.conversion_factor) or 1.0
				rate_in_stock_uom = flt(item.rate or 0) / conversion_factor if conversion_factor > 0 else flt(item.rate or 0)

				# Add to stock entry items (shortage_qty is already in stock UOM)
				stock_entry_items.append({
					"item_code": item.item_code,
					"item_name": item.item_name,
					"description": item.description,
					"qty": shortage_qty,
					"uom": stock_uom,  # Use stock UOM for Material Receipt
					"stock_uom": stock_uom,
					"conversion_factor": 1.0,  # Already in stock UOM
					"t_warehouse": item.warehouse,  # Target warehouse for Material Receipt
					"basic_rate": rate_in_stock_uom,
					"basic_amount": flt(shortage_qty * rate_in_stock_uom),
					"expense_account": item.expense_account,
					"cost_center": item.cost_center or self.cost_center,
				})

			# Create Stock Entry
			stock_entry = frappe.get_doc({
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Receipt",
				"company": company,
				"set_posting_time": 1,
				"posting_date": posting_date,
				"posting_time": posting_time,
				"items": stock_entry_items,
				"remarks": _("Auto-created Material Receipt for insufficient stock in Sales Invoice {0}").format(
					self.name
				),
			})

			# Explicitly set posting time and date
			stock_entry.set_posting_time = 1
			stock_entry.posting_date = posting_date
			stock_entry.posting_time = posting_time

			# Insert the stock entry
			stock_entry.insert(ignore_permissions=True)

			# Submit the stock entry
			stock_entry.set_posting_time = 1
			stock_entry.posting_date = posting_date
			stock_entry.submit()

			# Final check - if posting_date was changed, force set it via SQL
			if stock_entry.posting_date != posting_date:
				frappe.db.sql(
					"UPDATE `tabStock Entry` SET posting_date = %s WHERE name = %s",
					(posting_date, stock_entry.name),
				)
				frappe.db.commit()
				stock_entry.reload()

			# Save Stock Entry ID to custom field
			self.custom_stock_entry_id = stock_entry.name
			# Update the field in database since we're in on_submit
			frappe.db.set_value("Sales Invoice", self.name, "custom_stock_entry_id", stock_entry.name)
			frappe.db.commit()

			# Show success message
			item_list = ", ".join([f"{r['item'].item_code} ({r['shortage_qty']})" for r in items_to_receipt])
			frappe.msgprint(
				_("Material Receipt {0} created and submitted automatically for insufficient stock items: {1}").format(
					frappe.bold(stock_entry.name),
					item_list
				),
				indicator="green",
				alert=True,
			)

		except Exception as e:
			frappe.log_error(
				title=_("Error creating Material Receipt for Sales Invoice {0}").format(self.name),
				message=frappe.get_traceback(),
			)
			frappe.throw(
				_("Error creating Material Receipt for insufficient stock: {0}").format(str(e)),
				title=_("Stock Entry Creation Failed"),
			)

	def get_available_stock(self, item_code, warehouse):
		"""Get available stock quantity for an item in a warehouse.
		
		Uses Stock Ledger Entry to get accurate stock as of the posting date.
		"""
		try:
			# Use get_previous_sle to get accurate stock as of posting date
			previous_sle = get_previous_sle(
				{
					"item_code": item_code,
					"warehouse": warehouse,
					"posting_date": self.posting_date or nowdate(),
					"posting_time": self.posting_time or nowtime(),
				}
			)

			# Get actual stock quantity
			actual_qty = flt(previous_sle.get("qty_after_transaction") or 0)

			return actual_qty

		except Exception:
			# Fallback to Bin table if SLE method fails
			try:
				bin_data = frappe.db.sql(
					"""
					SELECT actual_qty
					FROM `tabBin`
					WHERE item_code = %s AND warehouse = %s
					LIMIT 1
					""",
					(item_code, warehouse),
					as_dict=True,
				)

				if bin_data:
					return flt(bin_data[0].get("actual_qty") or 0)

			except Exception:
				pass

			return 0

