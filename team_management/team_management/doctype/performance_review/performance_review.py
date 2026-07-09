# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class PerformanceReview(Document):
	def validate(self):
		self.validate_reviewer_access()
		self.validate_team_link()
		self.validate_ratings()

	def validate_reviewer_access(self):
		"""Ensure reviewer has appropriate permissions."""
		if not self.reviewer:
			return
		roles = frappe.get_roles(self.reviewer)
		allowed_roles = ["System Manager", "HR Manager", "Team Head"]
		if not any(role in roles for role in allowed_roles):
			frappe.throw(
				_("Reviewer must have HR Manager or Team Head role.")
			)

	def validate_team_link(self):
		"""Auto-link team from employee if not set."""
		if self.employee and not self.team:
			self.team = frappe.db.get_value("Employee", self.employee, "department")

	def validate_ratings(self):
		"""Ensure ratings are within valid range."""
		if self.goals_achieved and (self.goals_achieved < 0 or self.goals_achieved > 100):
			frappe.throw(_("Goals Achieved must be between 0 and 100."))
		
		if self.kpis_met and (self.kpis_met < 0 or self.kpis_met > 100):
			frappe.throw(_("KPIs Met must be between 0 and 100."))

	def on_submit(self):
		"""Set status to Submitted when submitted."""
		self.db_set("status", "Submitted")

	def acknowledge_review(self):
		"""Employee acknowledges the review."""
		if not self.acknowledged_by_employee:
			self.db_set("acknowledged_by_employee", 1)
			self.db_set("acknowledgment_date", today())
			self.db_set("status", "Acknowledged")
			frappe.msgprint(_("Review acknowledged successfully."))
		else:
			frappe.throw(_("Review has already been acknowledged."))

	def get_average_rating(self):
		"""Calculate average rating from goals and KPIs."""
		ratings = []
		if self.goals_achieved:
			ratings.append(self.goals_achieved)
		if self.kpis_met:
			ratings.append(self.kpis_met)
		if self.overall_rating:
			ratings.append(self.overall_rating * 20)  # Convert 5-star to percentage
		
		return sum(ratings) / len(ratings) if ratings else 0
