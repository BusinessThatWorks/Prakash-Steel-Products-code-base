# # Copyright (c) 2025, beetashoke chakraborty and contributors
# # For license information, please see license.txt

# import frappe
# from frappe import _
# from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
# from frappe.utils import flt, nowdate, nowtime
# from erpnext.stock.stock_ledger import get_previous_sle
# from prakash_steel.prakash_steel.api.adu import update_adu_for_sales_invoice


# class CustomSalesInvoice(SalesInvoice):
# 	"""Custom Sales Invoice that automatically creates Material Receipt Stock Entry
# 	for items with insufficient stock when custom_stock_in_for_weight_variance is checked.
# 	"""

# 	def on_submit(self):
# 		"""Run standard submit, then complete extra-qty Sales Orders and update ADU (custom)."""
# 		# Call parent on_submit to continue with normal submit process
# 		super().on_submit()

# 		# Force-complete any extra Sales Orders created during before_submit
# 		for so_name in getattr(self, "_extra_sales_orders", []) or []:
# 			try:
# 				# Mark header as fully billed and delivered
# 				frappe.db.set_value("Sales Order", so_name, "per_billed", 100)
# 				frappe.db.set_value("Sales Order", so_name, "per_delivered", 100)
# 				frappe.db.set_value("Sales Order", so_name, "status", "Completed")
# 				# Optional detail fields used in newer versions
# 				frappe.db.set_value("Sales Order", so_name, "billing_status", "Fully Billed")
# 				frappe.db.set_value("Sales Order", so_name, "delivery_status", "Completed")

# 				# Also mark each Sales Order Item as fully delivered: delivered_qty = qty
# 				so_doc = frappe.get_doc("Sales Order", so_name)
# 				total_delivered = 0
# 				for it in so_doc.get("items", []):
# 					if getattr(it, "delivered_qty", None) is not None:
# 						frappe.db.set_value("Sales Order Item", it.name, "delivered_qty", it.qty)
# 						total_delivered += it.qty or 0

# 				# If Sales Order has a delivered_qty summary field, try to update it as well
# 				try:
# 					frappe.db.set_value("Sales Order", so_name, "delivered_qty", total_delivered)
# 				except Exception:
# 					pass
# 			except Exception:
# 				# If this fails, we at least keep the Sales Order usable
# 				pass

# 		# Recalculate ADU for all items in this invoice based on ADU Horizon setting
# 		try:
# 			update_adu_for_sales_invoice(self)
# 		except Exception:
# 			# Do not block invoice submission if ADU calculation fails
# 			frappe.log_error(
# 				title=_("Error updating ADU for Sales Invoice {0}").format(self.name),
# 				message=frappe.get_traceback(),
# 			)

# 	def on_cancel(self):
# 		"""Recalculate ADU for items when Sales Invoice is cancelled."""
# 		# Call parent on_cancel to perform standard cancellation
# 		super().on_cancel()

# 		# After cancellation, the cancelled invoice is excluded from ADU horizon,
# 		# so recalculate ADU for all items in this invoice.
# 		try:
# 			update_adu_for_sales_invoice(self)
# 		except Exception:
# 			# Do not block cancellation if ADU calculation fails
# 			frappe.log_error(
# 				title=_("Error updating ADU on cancel for Sales Invoice {0}").format(self.name),
# 				message=frappe.get_traceback(),
# 			)

# 	def before_submit(self):
# 		"""Run stock-entry (conditional) and always run extra-qty Sales Order logic before submit."""
# 		custom_field_value = self.get("custom_stock_in_for_weight_variance")

# 		# 1) Stock entry only depends on the checkbox + update_stock
# 		if custom_field_value and custom_field_value not in [None, "", 0, "0", "No"]:
# 			if self.update_stock:
# 				self.create_material_receipt_for_insufficient_stock()

# 		# 2) Always handle extra quantity vs Sales Order and create a new Sales Order
# 		#    (independent of the checkbox)
# 		self.split_extra_qty_and_create_sales_order()

# 		# Preserve any parent before_submit behaviour
# 		super().before_submit()

# 	def split_extra_qty_and_create_sales_order(self):
# 		"""Split invoice items that exceed their linked Sales Order qty and
# 		create a new Sales Order for the extra quantity.

# 		Example:
# 		- Item A: SO qty 300, Invoice qty 400  ->  300 (old SO), 100 (new SO)
# 		- Item B: SO qty 200, Invoice qty 300  ->  200 (old SO), 100 (new SO)
# 		New SO will have Item A 100 and Item B 100, and the extra rows in Sales Invoice
# 		will be linked to this new Sales Order.
# 		"""
# 		if not self.items:
# 			return

# 		extra_mappings = []

# 		for item in self.get("items"):
# 			# Only consider rows that are linked to a Sales Order line
# 			if not (getattr(item, "sales_order", None) and getattr(item, "so_detail", None)):
# 				continue

# 			if not item.item_code:
# 				continue

# 			# Work in stock UOM to be safe with UOM conversions
# 			inv_cf = flt(getattr(item, "conversion_factor", 1.0)) or 1.0
# 			inv_qty = flt(getattr(item, "qty", 0) or 0, item.precision("qty"))
# 			inv_stock_qty = (
# 				flt(getattr(item, "stock_qty", 0) or 0, item.precision("stock_qty")) or inv_qty * inv_cf
# 			)

# 			if inv_stock_qty <= 0:
# 				continue

# 			# Get the linked Sales Order Item quantities
# 			so_item = frappe.db.get_value(
# 				"Sales Order Item",
# 				item.so_detail,
# 				["qty", "stock_qty", "conversion_factor", "uom", "stock_uom"],
# 				as_dict=True,
# 			)

# 			if not so_item:
# 				# Safety: if SO item cannot be found, do not attempt to split
# 				continue

# 			so_cf = flt(so_item.conversion_factor or 1.0) or 1.0
# 			so_qty = flt(so_item.qty or 0)
# 			so_stock_qty = flt(so_item.stock_qty or 0) or so_qty * so_cf

# 			# No extra if invoice stock qty is within Sales Order stock qty (with tiny tolerance)
# 			if inv_stock_qty <= so_stock_qty + 0.0001:
# 				continue

# 			extra_stock_qty = inv_stock_qty - so_stock_qty
# 			original_stock_qty = inv_stock_qty - extra_stock_qty

# 			# Convert back to invoice UOM
# 			original_qty = original_stock_qty / inv_cf
# 			extra_qty = extra_stock_qty / inv_cf

# 			if extra_qty <= 0:
# 				continue

# 			# Update the existing item row to hold only the original Sales Order qty
# 			item.stock_qty = original_stock_qty
# 			item.qty = original_qty

# 			# Track data needed to create new SO + extra SI rows
# 			extra_mappings.append(
# 				{
# 					"si_item": item,
# 					"item_code": item.item_code,
# 					"item_name": getattr(item, "item_name", None),
# 					"description": getattr(item, "description", None),
# 					"uom": item.uom,
# 					"stock_uom": getattr(item, "stock_uom", None),
# 					"conversion_factor": inv_cf,
# 					"warehouse": getattr(item, "warehouse", None),
# 					"income_account": getattr(item, "income_account", None),
# 					"expense_account": getattr(item, "expense_account", None),
# 					"cost_center": getattr(item, "cost_center", None) or getattr(self, "cost_center", None),
# 					"rate": flt(getattr(item, "rate", 0)),
# 					"net_rate": flt(getattr(item, "net_rate", 0)),
# 					"discount_percentage": flt(getattr(item, "discount_percentage", 0)),
# 					"pricing_rule": getattr(item, "pricing_rule", None),
# 					"extra_qty": extra_qty,
# 					"extra_stock_qty": extra_stock_qty,
# 				}
# 			)

# 		# If no extras, nothing to do
# 		if not extra_mappings:
# 			return

# 		# Create a single new Sales Order that will hold all the extra quantities
# 		try:
# 			new_so = frappe.new_doc("Sales Order")
# 			new_so.customer = self.customer
# 			new_so.company = self.company
# 			new_so.transaction_date = self.posting_date or nowdate()

# 			# Try to copy important header fields from one of the source Sales Orders
# 			source_so_name = None
# 			for mapping in extra_mappings:
# 				so_name = getattr(mapping["si_item"], "sales_order", None)
# 				if so_name:
# 					source_so_name = so_name
# 					break

# 			if source_so_name:
# 				try:
# 					source_so = frappe.get_doc("Sales Order", source_so_name)
# 					for fname in ("custom_loading_and_cutting", "custom_special_condition"):
# 						if hasattr(source_so, fname):
# 							setattr(new_so, fname, getattr(source_so, fname))
# 				except Exception:
# 					# If copying fails, we still proceed and let normal validation handle it
# 					pass

# 			# Use due_date / posting_date as delivery reference
# 			delivery_date = getattr(self, "due_date", None) or self.posting_date or nowdate()
# 			# Try to preserve order_type when available
# 			if hasattr(self, "order_type") and self.order_type:
# 				new_so.order_type = self.order_type

# 			# Map each extra mapping to an item row in the new Sales Order
# 			for mapping in extra_mappings:
# 				so_item_row = new_so.append(
# 					"items",
# 					{
# 						"item_code": mapping["item_code"],
# 						"item_name": mapping["item_name"],
# 						"description": mapping["description"],
# 						"qty": mapping["extra_qty"],
# 						"uom": mapping["uom"],
# 						"conversion_factor": mapping["conversion_factor"],
# 						"stock_uom": mapping["stock_uom"],
# 						"warehouse": mapping["warehouse"],
# 						"delivery_date": delivery_date,
# 						"rate": mapping["rate"],
# 						"net_rate": mapping["net_rate"],
# 						"discount_percentage": mapping["discount_percentage"],
# 						"pricing_rule": mapping["pricing_rule"],
# 						"income_account": mapping["income_account"],
# 						"expense_account": mapping["expense_account"],
# 						"cost_center": mapping["cost_center"],
# 					},
# 				)
# 				# Remember the linked Sales Order Item row for this mapping
# 				mapping["new_so_detail"] = so_item_row.name

# 			# Insert and submit the new Sales Order
# 			new_so.flags.ignore_permissions = True
# 			new_so.insert()
# 			new_so.submit()

# 			# Remember this Sales Order so we can force-complete it after submit
# 			extra_list = getattr(self, "_extra_sales_orders", []) or []
# 			extra_list.append(new_so.name)
# 			self._extra_sales_orders = extra_list

# 			# Create the extra item rows in the Sales Invoice linked to the new Sales Order
# 			for mapping in extra_mappings:
# 				orig = mapping["si_item"]
# 				extra_row = self.append("items", {})

# 				# Copy over relevant fields from the original item
# 				for fieldname in [
# 					"item_code",
# 					"item_name",
# 					"description",
# 					"uom",
# 					"stock_uom",
# 					"conversion_factor",
# 					"warehouse",
# 					"income_account",
# 					"expense_account",
# 					"cost_center",
# 					"rate",
# 					"net_rate",
# 					"discount_percentage",
# 					"pricing_rule",
# 					"batch_no",
# 					"serial_no",
# 					"item_group",
# 				]:
# 					if hasattr(orig, fieldname):
# 						extra_row.set(fieldname, getattr(orig, fieldname))

# 				extra_row.qty = mapping["extra_qty"]
# 				extra_row.stock_qty = mapping["extra_stock_qty"]

# 				# Link to the newly created Sales Order + its item row
# 				extra_row.sales_order = new_so.name
# 				extra_row.so_detail = mapping.get("new_so_detail")

# 			# Recalculate totals now that quantities/rows changed,
# 			# so that the parent SalesInvoice on_submit logic sees correct values.
# 			if hasattr(self, "calculate_taxes_and_totals"):
# 				self.calculate_taxes_and_totals()

# 			# Inform the user which Sales Order was created
# 			frappe.msgprint(
# 				_(
# 					"New Sales Order {0} created automatically for extra quantities "
# 					"entered in Sales Invoice {1}."
# 				).format(frappe.bold(new_so.name), frappe.bold(self.name)),
# 				indicator="green",
# 				alert=True,
# 			)

# 		except Exception:
# 			# If anything goes wrong here, fail the submission – this flow is critical.
# 			frappe.log_error(
# 				title=_("Error creating extra-quantity Sales Order for Sales Invoice {0}").format(self.name),
# 				message=frappe.get_traceback(),
# 			)
# 			frappe.throw(
# 				_(
# 					"Failed to create Sales Order for extra quantity entered against Sales Orders "
# 					"in this Sales Invoice. Please contact your System Administrator."
# 				),
# 				title=_("Sales Order Creation Failed"),
# 			)

# 	def before_cancel(self):
# 		"""Ensure cancel reason is provided before allowing cancellation."""
# 		if not (self.custom_cancel_reason or "").strip():
# 			frappe.throw(
# 				_("Please enter Cancel Reason before cancelling this Sales Invoice."),
# 				title=_("Cancel Reason Required"),
# 			)

# 		# Continue with standard cancellation flow
# 		super().before_cancel()

# 	def create_material_receipt_for_insufficient_stock(self):
# 		"""Create Material Receipt Stock Entry for items with insufficient stock in warehouse."""
# 		if not self.items:
# 			return

# 		items_to_receipt = []
# 		stock_entry_items = []

# 		# Check each item for insufficient stock
# 		for item in self.get("items"):
# 			if not item.item_code or not item.warehouse:
# 				continue

# 			# Skip if item is not a stock item
# 			if not frappe.get_cached_value("Item", item.item_code, "is_stock_item"):
# 				continue

# 			# Get required quantity in stock UOM
# 			# Use stock_qty if available (already in stock UOM), otherwise convert qty to stock UOM
# 			if hasattr(item, "stock_qty") and item.stock_qty:
# 				required_qty = flt(item.stock_qty, item.precision("stock_qty"))
# 			else:
# 				# Convert qty to stock UOM using conversion_factor
# 				conversion_factor = flt(item.conversion_factor) or 1.0
# 				required_qty = flt(item.qty, item.precision("qty")) * conversion_factor

# 			if required_qty <= 0:
# 				continue

# 			# Get available stock from warehous
# 			available_qty = self.get_available_stock(item.item_code, item.warehouse)

# 			# Validation: If any item has 0 quantity in warehouse, throw error and prevent submission
# 			if available_qty == 0:
# 				frappe.throw(
# 					_(
# 						"Item {0} has 0 quantity in warehouse {1}. Cannot create Material Receipt for items with zero stock. Please add stock manually before submitting."
# 					).format(frappe.bold(item.item_code), frappe.bold(item.warehouse)),
# 					title=_("Zero Stock Error"),
# 				)

# 			# Check if stock is insufficient
# 			if available_qty < required_qty:
# 				shortage_qty = required_qty - available_qty
# 				items_to_receipt.append(
# 					{
# 						"item": item,
# 						"shortage_qty": shortage_qty,
# 						"available_qty": available_qty,
# 						"required_qty": required_qty,
# 					}
# 				)

# 		# If no items need stock receipt, return
# 		if not items_to_receipt:
# 			return

# 		# Create Material Receipt Stock Entry
# 		try:
# 			# Get company from Sales Invoice
# 			company = self.company

# 			# Get posting date and time
# 			posting_date = self.posting_date or nowdate()
# 			posting_time = self.posting_time or nowtime()

# 			# Prepare items for Stock Entry
# 			for receipt_item in items_to_receipt:
# 				item = receipt_item["item"]
# 				shortage_qty = receipt_item["shortage_qty"]

# 				# Get item details
# 				item_doc = frappe.get_doc("Item", item.item_code)
# 				stock_uom = item_doc.stock_uom or item.uom or "Nos"

# 				# Calculate rate in stock UOM if needed
# 				conversion_factor = flt(item.conversion_factor) or 1.0
# 				rate_in_stock_uom = (
# 					flt(item.rate or 0) / conversion_factor if conversion_factor > 0 else flt(item.rate or 0)
# 				)

# 				# Add to stock entry items (shortage_qty is already in stock UOM)
# 				stock_entry_items.append(
# 					{
# 						"item_code": item.item_code,
# 						"item_name": item.item_name,
# 						"description": item.description,
# 						"qty": shortage_qty,
# 						"uom": stock_uom,  # Use stock UOM for Material Receipt
# 						"stock_uom": stock_uom,
# 						"conversion_factor": 1.0,  # Already in stock UOM
# 						"t_warehouse": item.warehouse,  # Target warehouse for Material Receipt
# 						"basic_rate": rate_in_stock_uom,
# 						"basic_amount": flt(shortage_qty * rate_in_stock_uom),
# 						"expense_account": item.expense_account,
# 						"cost_center": item.cost_center or self.cost_center,
# 					}
# 				)

# 			# Create Stock Entry
# 			stock_entry = frappe.get_doc(
# 				{
# 					"doctype": "Stock Entry",
# 					"stock_entry_type": "Material Receipt",
# 					"company": company,
# 					"set_posting_time": 1,
# 					"posting_date": posting_date,
# 					"posting_time": posting_time,
# 					"items": stock_entry_items,
# 					"remarks": _(
# 						"Auto-created Material Receipt for insufficient stock in Sales Invoice {0}"
# 					).format(self.name),
# 				}
# 			)

# 			# Explicitly set posting time and date
# 			stock_entry.set_posting_time = 1
# 			stock_entry.posting_date = posting_date
# 			stock_entry.posting_time = posting_time

# 			# Insert the stock entry
# 			stock_entry.insert(ignore_permissions=True)

# 			# Submit the stock entry
# 			stock_entry.set_posting_time = 1
# 			stock_entry.posting_date = posting_date
# 			stock_entry.submit()

# 			# Final check - if posting_date was changed, force set it via SQL
# 			if stock_entry.posting_date != posting_date:
# 				frappe.db.sql(
# 					"UPDATE `tabStock Entry` SET posting_date = %s WHERE name = %s",
# 					(posting_date, stock_entry.name),
# 				)
# 				frappe.db.commit()
# 				stock_entry.reload()

# 			# Save Stock Entry ID to custom field
# 			self.custom_stock_entry_id = stock_entry.name
# 			# Update the field in database since we're in on_submit
# 			frappe.db.set_value("Sales Invoice", self.name, "custom_stock_entry_id", stock_entry.name)
# 			frappe.db.commit()

# 			# Show success message
# 			item_list = ", ".join([f"{r['item'].item_code} ({r['shortage_qty']})" for r in items_to_receipt])
# 			frappe.msgprint(
# 				_(
# 					"Material Receipt {0} created and submitted automatically for insufficient stock items: {1}"
# 				).format(frappe.bold(stock_entry.name), item_list),
# 				indicator="green",
# 				alert=True,
# 			)

# 		except Exception as e:
# 			frappe.log_error(
# 				title=_("Error creating Material Receipt for Sales Invoice {0}").format(self.name),
# 				message=frappe.get_traceback(),
# 			)
# 			frappe.throw(
# 				_("Error creating Material Receipt for insufficient stock: {0}").format(str(e)),
# 				title=_("Stock Entry Creation Failed"),
# 			)

# 	def get_available_stock(self, item_code, warehouse):
# 		"""Get available stock quantity for an item in a warehouse.

# 		Uses Stock Ledger Entry to get accurate stock as of the posting date.
# 		"""
# 		try:
# 			# Use get_previous_sle to get accurate stock as of posting date
# 			previous_sle = get_previous_sle(
# 				{
# 					"item_code": item_code,
# 					"warehouse": warehouse,
# 					"posting_date": self.posting_date or nowdate(),
# 					"posting_time": self.posting_time or nowtime(),
# 				}
# 			)

# 			# Get actual stock quantity
# 			actual_qty = flt(previous_sle.get("qty_after_transaction") or 0)

# 			return actual_qty

# 		except Exception:
# 			# Fallback to Bin table if SLE method fails
# 			try:
# 				bin_data = frappe.db.sql(
# 					"""
# 					SELECT actual_qty
# 					FROM `tabBin`
# 					WHERE item_code = %s AND warehouse = %s
# 					LIMIT 1
# 					""",
# 					(item_code, warehouse),
# 					as_dict=True,
# 				)

# 				if bin_data:
# 					return flt(bin_data[0].get("actual_qty") or 0)

# 			except Exception:
# 				pass

# 			return 0
