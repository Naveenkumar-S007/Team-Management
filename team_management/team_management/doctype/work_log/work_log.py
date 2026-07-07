# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class WorkLog(Document):
	def validate(self):
		self.set_team_from_assignment()
		self.restrict_edit_to_owner_or_head()

	def set_team_from_assignment(self):
		if self.work_assignment and not self.team:
			self.team = frappe.db.get_value("Work Assignment", self.work_assignment, "team")

	def restrict_edit_to_owner_or_head(self):
		roles = frappe.get_roles(frappe.session.user)
		if "Team Head" in roles or "System Manager" in roles:
			return
		if not self.is_new() and self.owner != frappe.session.user:
			frappe.throw(_("You can only edit your own work log entries."))
