# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, getdate


class WorkAssignment(Document):
	def validate(self):
		self.validate_dates()
		self.validate_assigned_member()
		self.restrict_member_edits()
		self.sync_parent_requirement_status()
		self.update_actual_hours()

	def validate_dates(self):
		"""Validate start and end dates."""
		if self.assigned_date and self.due_date:
			if getdate(self.assigned_date) > getdate(self.due_date):
				frappe.throw(_("Assigned Date cannot be after Due Date."))

	def validate_assigned_member(self):
		"""Validate that assigned member is a team member."""
		if not self.team or not self.assigned_to:
			return
		
		is_member = frappe.db.exists(
			"Team Member",
			{"parenttype": "Team", "parent": self.team, "user": self.assigned_to, "is_active": 1}
		)
		is_head = frappe.db.get_value("Team", self.team, "team_head") == self.assigned_to
		
		if not is_member and not is_head:
			frappe.throw(_("Assigned user is not a member of this team."))

	def restrict_member_edits(self):
		"""A Team Member can only update the 'status' field of their own
		assignment. Every other field is force-reset to the last saved
		(db) value if a member (non-head) attempts to change it."""
		if self.is_new():
			return

		roles = frappe.get_roles(frappe.session.user)
		if "Team Head" in roles or "System Manager" in roles:
			return  # Team Head / Admin can edit everything

		if frappe.session.user != self.assigned_to:
			frappe.throw(_("You are not allowed to modify this assignment."))

		old_doc = self.get_doc_before_save()
		if not old_doc:
			return

		protected_fields = [
			"work_requirement", "team", "assigned_to", "assigned_by",
			"assigned_date", "due_date", "priority", "instructions", "project",
		]
		for field in protected_fields:
			self.set(field, old_doc.get(field))

	def sync_parent_requirement_status(self):
		"""Sync status with parent work requirement."""
		if self.work_requirement:
			frappe.db.set_value("Work Requirement", self.work_requirement, "status", self.status)
			frappe.db.set_value("Work Requirement", self.work_requirement, "linked_assignment", self.name)

	def update_actual_hours(self):
		"""Calculate actual hours from work logs."""
		if self.is_new():
			return
		
		hours = frappe.db.sql("""
			SELECT COALESCE(SUM(hours_spent), 0)
			FROM `tabWork Log`
			WHERE work_assignment = %s
		""", [self.name])[0][0] or 0
		
		self.actual_hours = hours
		
		# Update progress based on hours
		if self.estimated_hours and self.estimated_hours > 0:
			self.progress = min((hours / self.estimated_hours) * 100, 100)

	def on_update(self):
		"""Send notification on status change."""
		if self.has_value_changed("status"):
			self.notify_status_change()

	def notify_status_change(self):
		"""Notify relevant parties of status change."""
		if self.status == "Completed":
			frappe.publish_realtime(
				event="assignment_completed",
				message={"assignment": self.name, "assigned_to": self.assigned_to},
				after_commit=True
			)

