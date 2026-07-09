# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TeamMember(Document):
	def validate(self):
		self.validate_no_duplicate_members()
		self.validate_active_member()
		self.validate_employee_link()

	def validate_no_duplicate_members(self):
		"""Prevent adding the same member twice to the same team."""
		if not self.parent or not self.user:
			return
		existing = frappe.get_all(
			"Team Member",
			filters={
				"parenttype": "Team",
				"parent": self.parent,
				"user": self.user,
				"name": ["!=", self.name],
				"is_active": 1,
			},
			pluck="name",
		)
		if existing:
			frappe.throw(
				_("{0} is already an active member of this team.").format(
					frappe.bold(self.user)
				)
			)

	def validate_active_member(self):
		"""Validate that date_left_team is after date_joined_team."""
		if self.date_left_team and self.date_joined_team:
			if self.date_left_team < self.date_joined_team:
				frappe.throw(
					_("Date Left Team cannot be before Date Joined Team.")
				)

	def validate_employee_link(self):
		"""Validate employee link if provided."""
		if self.employee:
			if not frappe.db.exists("Employee", self.employee):
				frappe.throw(_("Employee {0} does not exist.").format(self.employee))
			
			if not self.user:
				self.user = frappe.db.get_value("Employee", self.employee, "user_id")

	def after_insert(self):
		"""Add Team Member role to user when added to team."""
		if self.user and self.is_active:
			self.add_team_member_role()

	def on_trash(self):
		"""Clean up user permissions when member is removed."""
		if self.user:
			self.remove_user_permission()

	def add_team_member_role(self):
		"""Add Team Member role to the user."""
		if not frappe.db.exists("Has Role", {"parent": self.user, "role": "Team Member"}):
			frappe.get_doc({
				"doctype": "Has Role",
				"parent": self.user,
				"parenttype": "User",
				"role": "Team Member",
			}).insert(ignore_permissions=True)

	def remove_user_permission(self):
		"""Remove user permission for this team."""
		frappe.db.delete("User Permission", {
			"user": self.user,
			"allow": "Team",
			"for_value": self.parent,
		})
