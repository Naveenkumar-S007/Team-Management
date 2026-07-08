# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TeamUpdate(Document):
	def validate(self):
		self.validate_team_membership()

	def validate_team_membership(self):
		"""Ensure the member belongs to the selected team."""
		if self.is_new() or self.has_value_changed("team"):
			if not self.team:
				return
			# Team Head can post updates for any team they head
			roles = frappe.get_roles(frappe.session.user)
			if "System Manager" in roles:
				return

			is_member = frappe.db.exists(
				"Team Member",
				{"parenttype": "Team", "parent": self.team, "user": self.member},
			)
			is_head = frappe.db.get_value("Team", self.team, "team_head") == self.member

			if not is_member and not is_head:
				frappe.throw(_("You are not a member of this team."))
