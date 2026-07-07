# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class WorkRequirement(Document):
	def validate(self):
		if self.due_date and self.due_date < frappe.utils.nowdate():
			frappe.msgprint(
				_("Warning: Due Date is in the past."), indicator="orange", alert=True
			)

	def on_update(self):
		# Keep status in sync if it has been fully assigned/completed via child assignment
		pass
