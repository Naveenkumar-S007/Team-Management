# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, add_days


class Team(Document):
	def validate(self):
		self.validate_team_head_is_member()
		self.validate_team_size()
		self.validate_no_circular_parent()
		self.validate_team_lead()
		self.sync_roles_to_members()

	def validate_team_head_is_member(self):
		"""Ensure the Team Head is always listed as a member of their own team."""
		if not self.members:
			return
		member_users = [row.user for row in self.members if row.user and row.is_active]
		if self.team_head and self.team_head not in member_users:
			self.append("members", {
				"user": self.team_head,
				"role_in_team": "Lead",
				"is_active": 1
			})

	def validate_team_size(self):
		"""Validate team size against maximum limit."""
		if self.members and self.max_team_size:
			active_members = len([m for m in self.members if m.is_active])
			if active_members > self.max_team_size:
				frappe.throw(
					_("Team cannot have more than {0} active members. Current: {1}").format(
						self.max_team_size, active_members
					)
				)

	def validate_no_circular_parent(self):
		"""Prevent circular team hierarchy."""
		if not self.parent_team:
			return
		
		visited = {self.name}
		current = self.parent_team
		
		while current:
			if current in visited:
				frappe.throw(_("Circular team hierarchy detected. Team cannot be its own ancestor."))
			visited.add(current)
			parent = frappe.db.get_value("Team", current, "parent_team")
			current = parent if parent != self.name else None

	def validate_team_lead(self):
		"""Validate that team lead is a member of the team."""
		if self.team_lead and self.members:
			member_users = [row.user for row in self.members if row.user and row.is_active]
			if self.team_lead not in member_users:
				frappe.throw(
					_("Team Lead must be a member of the team.")
				)

	def sync_roles_to_members(self):
		"""Automatically grant the 'Team Member' role to every user added here,
		and 'Team Head' role to the designated head, so permissions apply instantly."""
		if self.team_head:
			self.grant_role(self.team_head, "Team Head")

		if self.team_lead and self.team_lead != self.team_head:
			self.grant_role(self.team_lead, "Team Lead")

		for row in self.members:
			if row.user and row.is_active:
				self.grant_role(row.user, "Team Member")
				self.add_user_permission_for_team(row.user)

	def grant_role(self, user, role):
		"""Grant a role to a user if not already present."""
		if not frappe.db.exists("Has Role", {"parent": user, "role": role}):
			frappe.get_doc({
				"doctype": "Has Role",
				"parent": user,
				"parenttype": "User",
				"role": role,
			}).insert(ignore_permissions=True)

	def add_user_permission_for_team(self, user):
		"""Add user permission for the team."""
		exists = frappe.db.exists(
			"User Permission",
			{"user": user, "allow": "Team", "for_value": self.name},
		)
		if not exists:
			frappe.get_doc({
				"doctype": "User Permission",
				"user": user,
				"allow": "Team",
				"for_value": self.name,
				"apply_to_all_doctypes": 0,
				"applicable_for": "",
			}).insert(ignore_permissions=True)

	def after_insert(self):
		"""Create default capacity planning after team creation."""
		if not self.capacity_planning:
			self.create_default_capacity_planning()

	def create_default_capacity_planning(self):
		"""Create default capacity planning entries for the next 12 months."""
		current_date = getdate(today())
		for i in range(12):
			month_start = add_days(current_date, i * 30)
			self.append("capacity_planning", {
				"month_year": month_start.strftime("%Y-%m"),
				"available_hours": 160,
				"booked_hours": 0,
				"notes": ""
			})

	def get_team_utilization(self):
		"""Calculate team utilization percentage."""
		if not self.members:
			return 0
		
		total_capacity = sum(m.capacity_hours or 0 for m in self.members if m.is_active)
		if total_capacity == 0:
			return 0
		
		# Get booked hours for current month
		current_month = today()[:7]
		booked_hours = frappe.db.sql("""
			SELECT COALESCE(SUM(wl.hours_spent), 0)
			FROM `tabWork Log` wl
			JOIN `tabTeam Member` tm ON tm.user = wl.member
			WHERE tm.parent = %s AND tm.is_active = 1
			AND wl.date LIKE %s
		""", [self.name, current_month + "%"])[0][0] or 0
		
		return (booked_hours / total_capacity) * 100 if total_capacity > 0 else 0
