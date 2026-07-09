# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today


class Project(Document):
	def validate(self):
		self.validate_dates()
		self.calculate_progress()

	def validate_dates(self):
		"""Validate project dates."""
		if self.start_date and self.end_date:
			if getdate(self.start_date) > getdate(self.end_date):
				frappe.throw(_("Start Date cannot be after End Date."))

	def calculate_progress(self):
		"""Calculate project progress from milestones."""
		if not self.milestones:
			self.progress = 0
			return
		
		completed = len([m for m in self.milestones if m.status == "Completed"])
		total = len(self.milestones)
		self.progress = (completed / total) * 100 if total > 0 else 0
		
		# Auto-update status based on milestones
		if completed == total and total > 0 and self.status not in ("Completed", "Cancelled"):
			self.status = "Completed"
			if not self.completion_date:
				self.completion_date = today()
		elif completed > 0 and completed < total and self.status == "Planning":
			self.status = "Active"

	def on_update(self):
		self.update_linked_requirement_status()
		self.notify_project_update()

	def update_linked_requirement_status(self):
		"""When project is Completed or Cancelled, update linked work requirements."""
		if self.status in ("Completed", "Cancelled"):
			requirements = frappe.get_all(
				"Work Requirement",
				filters={"project": self.name, "status": ["not in", [self.status, "Cancelled"]]},
				pluck="name"
			)
			for req in requirements:
				frappe.db.set_value("Work Requirement", req, "status", self.status)

	def notify_project_update(self):
		"""Send notification on project status change."""
		if self.has_value_changed("status"):
			frappe.publish_realtime(
				event="project_status_changed",
				message={"project": self.name, "status": self.status},
				after_commit=True
			)

	def get_team_members(self):
		"""Get all team members for this project."""
		return frappe.get_all(
			"Team Member",
			filters={"parent": self.team, "is_active": 1},
			pluck="user"
		)

	def get_project_stats(self):
		"""Get project statistics."""
		stats = {
			"total_requirements": frappe.db.count("Work Requirement", {"project": self.name}),
			"completed_requirements": frappe.db.count("Work Requirement", {"project": self.name, "status": "Completed"}),
			"total_assignments": frappe.db.count("Work Assignment", {"project": self.name}),
			"completed_assignments": frappe.db.count("Work Assignment", {"project": self.name, "status": "Completed"}),
			"total_hours_logged": frappe.db.sql("""
				SELECT COALESCE(SUM(wl.hours_spent), 0)
				FROM `tabWork Log` wl
				JOIN `tabWork Assignment` wa ON wa.name = wl.work_assignment
				WHERE wa.project = %s
			""", [self.name])[0][0] or 0,
		}
		return stats
