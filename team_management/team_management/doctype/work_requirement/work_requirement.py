# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, nowdate


class WorkRequirement(Document):
	def validate(self):
		self.validate_dates()
		self.validate_team_access()

	def validate_dates(self):
		"""Validate that due date is reasonable."""
		if self.due_date and getdate(self.due_date) < getdate(today()):
			frappe.msgprint(
				_("Warning: Due Date is in the past."), indicator="orange", alert=True
			)
		
		if self.expected_start_date and self.due_date:
			if getdate(self.expected_start_date) > getdate(self.due_date):
				frappe.throw(_("Expected Start Date cannot be after Due Date."))

	def validate_team_access(self):
		"""Ensure user has access to the selected team."""
		if not self.team:
			return
		roles = frappe.get_roles(frappe.session.user)
		if "System Manager" in roles or "HR Manager" in roles:
			return
		
		# Check if user is team head or member
		is_head = frappe.db.get_value("Team", self.team, "team_head") == frappe.session.user
		is_member = frappe.db.exists(
			"Team Member",
			{"parenttype": "Team", "parent": self.team, "user": frappe.session.user, "is_active": 1}
		)
		
		if not is_head and not is_member:
			frappe.throw(_("You don't have access to this team."))

	def on_update(self):
		"""Track status changes and sync with assignments."""
		if self.has_value_changed("status") and self.status == "Completed":
			self.update_actual_hours()

	def update_actual_hours(self):
		"""Calculate and update actual hours from work logs."""
		if self.linked_assignment:
			hours = frappe.db.sql("""
				SELECT COALESCE(SUM(wl.hours_spent), 0)
				FROM `tabWork Log` wl
				WHERE wl.work_assignment = %s
			""", [self.linked_assignment])[0][0] or 0
			self.db_set("actual_hours", hours)
