# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class Project(Document):
	def validate(self):
		self.validate_dates()

	def validate_dates(self):
		if self.start_date and self.end_date:
			if getdate(self.start_date) > getdate(self.end_date):
				frappe.throw(_("Start Date cannot be after End Date."))

	def on_update(self):
		self.update_linked_requirement_status()

	def update_linked_requirement_status(self):
		"""When project is Completed or Cancelled, update linked work requirements."""
		if self.status in ("Completed", "Cancelled"):
			requirements = frappe.get_all(
				"Work Requirement",
				filters={"project": self.name, "status": ["!=", self.status]},
				pluck="name"
			)
			for req in requirements:
				frappe.db.set_value("Work Requirement", req, "status", self.status)
