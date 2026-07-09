# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class WorkLog(Document):
	def validate(self):
		self.set_team_from_assignment()
		self.set_member_from_assignment()
		self.restrict_edit_to_owner_or_head()
		self.validate_hours()

	def set_team_from_assignment(self):
		"""Auto-set team from work assignment if not provided."""
		if self.work_assignment and not self.team:
			self.team = frappe.db.get_value("Work Assignment", self.work_assignment, "team")

	def set_member_from_assignment(self):
		"""Auto-set member from work assignment if not provided."""
		if self.work_assignment and not self.member:
			self.member = frappe.db.get_value("Work Assignment", self.work_assignment, "assigned_to")

	def restrict_edit_to_owner_or_head(self):
		"""Ensure only owner or team head can edit work log."""
		roles = frappe.get_roles(frappe.session.user)
		if "Team Head" in roles or "System Manager" in roles:
			return
		if not self.is_new() and self.owner != frappe.session.user:
			frappe.throw(_("You can only edit your own work log entries."))

	def validate_hours(self):
		"""Validate hours spent."""
		if self.hours_spent and self.hours_spent < 0:
			frappe.throw(_("Hours spent cannot be negative."))
		if self.hours_spent and self.hours_spent > 24:
			frappe.msgprint(
				_("Warning: Hours spent exceeds 24 hours."), indicator="orange", alert=True
			)

	def on_update(self):
		"""Update work assignment actual hours when log is updated."""
		if self.work_assignment:
			self.update_assignment_hours()

	def update_assignment_hours(self):
		"""Calculate and update actual hours on work assignment."""
		total_hours = frappe.db.sql("""
			SELECT COALESCE(SUM(hours_spent), 0)
			FROM `tabWork Log`
			WHERE work_assignment = %s
		""", [self.work_assignment])[0][0] or 0
		
		frappe.db.set_value("Work Assignment", self.work_assignment, "actual_hours", total_hours)
