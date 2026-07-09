# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, getdate


class GoalSetting(Document):
	def validate(self):
		self.validate_dates()
		self.validate_team_link()
		self.calculate_overall_progress()

	def validate_dates(self):
		"""Validate start and end dates."""
		if self.start_date and self.end_date:
			if getdate(self.start_date) > getdate(self.end_date):
				frappe.throw(_("Start Date cannot be after End Date."))

	def validate_team_link(self):
		"""Auto-link team from employee if not set."""
		if self.employee and not self.team:
			self.team = frappe.db.get_value("Team Member", 
				{"user": frappe.db.get_value("Employee", self.employee, "user_id")},
				"team")

	def calculate_overall_progress(self):
		"""Calculate overall progress from all goal items."""
		if not self.goals:
			self.overall_progress = 0
			return
		
		total_progress = sum(g.progress or 0 for g in self.goals)
		self.overall_progress = total_progress / len(self.goals) if self.goals else 0

	def on_submit(self):
		"""Set status to Active when submitted."""
		self.db_set("status", "Active")

	def approve_goals(self):
		"""Approve the goal setting document."""
		roles = frappe.get_roles(frappe.session.user)
		allowed_roles = ["System Manager", "HR Manager", "Team Head"]
		if not any(role in roles for role in allowed_roles):
			frappe.throw(_("Only HR Manager or Team Head can approve goals."))
		
		self.db_set("approved_by", frappe.session.user)
		self.db_set("approval_date", today())
		self.db_set("status", "Active")
