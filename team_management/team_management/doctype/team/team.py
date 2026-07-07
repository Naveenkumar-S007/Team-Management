# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Team(Document):
	def validate(self):
		self.validate_team_head_is_member()
		self.sync_roles_to_members()

	def validate_team_head_is_member(self):
		"""Ensure the Team Head is always listed as a member of their own team."""
		member_users = [row.user for row in self.members]
		if self.team_head not in member_users:
			self.append("members", {"user": self.team_head})

	def sync_roles_to_members(self):
		"""Automatically grant the 'Team Member' role to every user added here,
		and 'Team Head' role to the designated head, so permissions apply instantly."""
		if self.team_head:
			user = frappe.get_doc("User", self.team_head)
			if not any(r.role == "Team Head" for r in user.roles):
				user.append("roles", {"role": "Team Head"})
				user.save(ignore_permissions=True)

		for row in self.members:
			user = frappe.get_doc("User", row.user)
			if not any(r.role == "Team Member" for r in user.roles):
				user.append("roles", {"role": "Team Member"})
				user.save(ignore_permissions=True)

			# Maintain a User Permission so a Team Head only ever sees
			# data belonging to their own team (used by list/report filters)
			self.add_user_permission_for_team(row.user)

	def add_user_permission_for_team(self, user):
		exists = frappe.db.exists(
			"User Permission",
			{"user": user, "allow": "Team", "for_value": self.name},
		)
		if not exists:
			frappe.get_doc(
				{
					"doctype": "User Permission",
					"user": user,
					"allow": "Team",
					"for_value": self.name,
					"apply_to_all_doctypes": 0,
					"applicable_for": "",
				}
			).insert(ignore_permissions=True)
