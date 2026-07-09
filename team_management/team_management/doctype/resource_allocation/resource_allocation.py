# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, getdate, date_diff


class ResourceAllocation(Document):
	def validate(self):
		self.validate_dates()
		self.validate_team_link()
		self.calculate_allocated_hours()

	def validate_dates(self):
		"""Validate start and end dates."""
		if self.start_date and self.end_date:
			if getdate(self.start_date) > getdate(self.end_date):
				frappe.throw(_("Start Date cannot be after End Date."))

	def validate_team_link(self):
		"""Auto-link team from employee if not set."""
		if self.employee and not self.team:
			team_member = frappe.get_all(
				"Team Member",
				filters={"user": frappe.db.get_value("Employee", self.employee, "user_id")},
				pluck="parent"
			)
			if team_member:
				self.team = team_member[0]

	def calculate_allocated_hours(self):
		"""Calculate total allocated hours based on allocation type."""
		if not self.start_date or not self.end_date:
			return
		
		days = date_diff(self.end_date, self.start_date) + 1
		
		if self.allocation_type == "Full Time":
			self.allocated_hours = days * 8
		elif self.allocation_type == "Part Time":
			self.allocated_hours = days * (self.hourly_allocation or 4)
		elif self.allocation_type == "Hourly":
			# Keep allocated_hours as is for hourly
			pass
		elif self.allocation_type == "Over-time":
			self.allocated_hours = days * 10

	def on_submit(self):
		"""Set status to Active when submitted."""
		self.db_set("status", "Active")

	def approve_allocation(self):
		"""Approve the resource allocation."""
		roles = frappe.get_roles(frappe.session.user)
		allowed_roles = ["System Manager", "Project Manager", "Team Head"]
		if not any(role in roles for role in allowed_roles):
			frappe.throw(_("Only Project Manager or Team Head can approve resource allocations."))
		
		self.db_set("approved_by", frappe.session.user)
		self.db_set("approval_date", today())
		self.db_set("status", "Active")

	def get_utilization_report(self):
		"""Get utilization report for this resource allocation."""
		if not self.project:
			return {}
		
		# Get work logs for this employee on this project
		logged_hours = frappe.db.sql("""
			SELECT COALESCE(SUM(wl.hours_spent), 0) as total_hours
			FROM `tabWork Log` wl
			JOIN `tabWork Assignment` wa ON wa.name = wl.work_assignment
			WHERE wl.member = %s AND wa.project = %s
			AND wl.date BETWEEN %s AND %s
		""", [self.user, self.project, self.start_date, self.end_date or today()])
		
		total_hours = logged_hours[0][0] if logged_hours else 0
		utilization = (total_hours / self.allocated_hours * 100) if self.allocated_hours else 0
		
		return {
			"allocated_hours": self.allocated_hours,
			"logged_hours": total_hours,
			"utilization_percentage": utilization
		}
