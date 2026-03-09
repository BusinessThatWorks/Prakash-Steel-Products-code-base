import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime
from datetime import datetime


class FinishWeight(Document):
	def on_submit(self):

		try:
			if not self.item_code:
				frappe.throw(_("Item Code is required to create Stock Entry"))
			if not self.finish_weight or self.finish_weight <= 0:
				frappe.throw(_("Finish Weight must be greater than 0"))
			if not self.fg_target_warehouse:
				frappe.throw(_("FG Target Warehouse is required to create Stock Entry"))

			warehouse_doc = frappe.get_doc("Warehouse", self.fg_target_warehouse)
			company = warehouse_doc.company
			item_doc = frappe.get_doc("Item", self.item_code)
			stock_uom = item_doc.stock_uom or "Nos"

			posting_date = self.posting_date or frappe.utils.today()
			if self.production_plan:
				pp_doc = frappe.get_doc("Production Plan", self.production_plan)
				posting_date = pp_doc.posting_date or posting_date

			items = [
				{
					"item_code": self.item_code,
					"qty": self.finish_weight,
					"t_warehouse": self.fg_target_warehouse,
					"stock_uom": stock_uom,
					"uom": stock_uom,
					"conversion_factor": 1.0,
				}
			]

			if getattr(self, "melting_item", None) and getattr(self, "miss_roll_item", None):
				if self.melting_item != self.miss_roll_item:
					frappe.throw(
						_("Melting Item ({0}) must equal Miss Roll Item ({1})").format(
							self.melting_item, self.miss_roll_item
						)
					)
				total_miss_roll_weight = flt(getattr(self, "total_miss_roll_weight", 0))
				melting_qty = total_miss_roll_weight + flt(getattr(self, "melting_weight", 0))
				if total_miss_roll_weight > 0:
					m_doc = frappe.get_doc("Item", self.melting_item)
					items.append(
						{
							"item_code": self.melting_item,
							"qty": melting_qty,
							"t_warehouse": self.fg_target_warehouse,
							"stock_uom": m_doc.stock_uom or "Kg",
							"uom": m_doc.stock_uom or "Kg",
							"conversion_factor": 1.0,
						}
					)

			if getattr(self, "miss_billet_item", None):
				total_miss_ingot = flt(getattr(self, "total_miss_ingot_weight", 0))
				if total_miss_ingot > 0:
					mb_doc = frappe.get_doc("Item", self.miss_billet_item)
					items.append(
						{
							"item_code": self.miss_billet_item,
							"qty": total_miss_ingot,
							"t_warehouse": self.fg_target_warehouse,
							"stock_uom": mb_doc.stock_uom or "Kg",
							"uom": mb_doc.stock_uom or "Kg",
							"conversion_factor": 1.0,
						}
					)

			stock_entry = frappe.get_doc(
				{
					"doctype": "Stock Entry",
					"stock_entry_type": "Material Receipt",
					"company": company,
					"set_posting_time": 1,
					"posting_date": posting_date,
					"posting_time": frappe.utils.nowtime(),
					"items": items,
				}
			)
			stock_entry.set_posting_time = 1
			stock_entry.posting_date = posting_date
			stock_entry.insert()
			stock_entry.set_posting_time = 1
			stock_entry.posting_date = posting_date
			stock_entry.submit()

			if stock_entry.posting_date != posting_date:
				frappe.db.sql(
					"UPDATE `tabStock Entry` SET posting_date=%s WHERE name=%s",
					(posting_date, stock_entry.name),
				)
				frappe.db.commit()

			self.custom_stock_entry_id = stock_entry.name
			frappe.db.set_value("Finish Weight", self.name, "custom_stock_entry_id", stock_entry.name)
			frappe.db.commit()

			frappe.msgprint(
				_("Stock Entry {0} created and submitted successfully").format(frappe.bold(stock_entry.name)),
				indicator="green",
				alert=True,
			)

		except Exception as e:
			frappe.log_error(
				f"Stock Entry creation failed for Finish Weight {self.name}: {e}",
				"Finish Weight Stock Entry Error",
			)
			frappe.throw(_("Error creating Stock Entry: {0}").format(str(e)))

		try:
			if getattr(self, "cooling_pit", None) == "Transferred":
				now = now_datetime()
				p_date = str(self.posting_date)
				time_part = now.strftime("%H:%M:%S")
				mat_in = datetime.strptime(f"{p_date} {time_part}", "%Y-%m-%d %H:%M:%S")

				cp = frappe.new_doc("Cooling PIT")
				cp.item_code = self.item_code
				cp.finish_weight = self.name
				cp.material_in_time = mat_in

				cp.insert(ignore_permissions=True)
				frappe.db.commit()

				frappe.msgprint(
					_("Cooling PIT {0} ").format(frappe.bold(cp.name)), indicator="blue", alert=True
				)

		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				f"Cooling PIT creation failed for Finish Weight {self.name}: {e}",
			)
			frappe.msgprint(_("Warning:  Error: {0}").format(str(e)), indicator="orange", alert=True)

	def before_cancel(self):
		"""Block cancel if linked Stock Entry is still active."""
		cmd = getattr(frappe.local, "form_dict", {}).get("cmd")
		if cmd == "frappe.desk.form.linked_with.cancel_all_linked_docs":
			return
		se_id = getattr(self, "custom_stock_entry_id", None)
		if not se_id:
			return
		docstatus = frappe.db.get_value("Stock Entry", se_id, "docstatus")
		if docstatus in (0, 1):
			frappe.throw(
				_("Please cancel Stock Entry {0} before cancelling this document.").format(frappe.bold(se_id))
			)

	def on_cancel(self):

		if getattr(self, "custom_stock_entry_id", None):
			self.custom_stock_entry_id = ""
			frappe.db.set_value(self.doctype, self.name, "custom_stock_entry_id", "")
