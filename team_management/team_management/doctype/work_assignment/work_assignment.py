# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class WorkAssignment(Document):
	def validate(self):
		self.restrict_member_edits_to_status_only()
		self.sync_parent_requirement_status()

	def restrict_member_edits_to_status_only(self):
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
			"assigned_date", "due_date", "priority", "instructions",
		]
		for field in protected_fields:
			self.set(field, old_doc.get(field))

	def sync_parent_requirement_status(self):
		if self.work_requirement:
			frappe.db.set_value("Work Requirement", self.work_requirement, "status", self.status)
			frappe.db.set_value("Work Requirement", self.work_requirement, "linked_assignment", self.name)
