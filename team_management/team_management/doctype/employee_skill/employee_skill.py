# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class EmployeeSkill(Document):
	def validate(self):
		self.validate_employee_access()
		self.validate_unique_skill()

	def validate_employee_access(self):
		"""Ensure user can only manage their own skills (unless HR/Manager)."""
		if self.is_new():
			roles = frappe.get_roles(frappe.session.user)
			allowed_roles = ["System Manager", "HR Manager", "Team Head"]
			if not any(role in roles for role in allowed_roles):
				if self.employee != frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name"):
					frappe.throw(_("You can only add skills for yourself."))

	def validate_unique_skill(self):
		"""Prevent duplicate skills for the same employee."""
		if not self.employee or not self.skill_name:
			return
		existing = frappe.get_all(
			"Employee Skill",
			filters={
				"employee": self.employee,
				"skill_name": self.skill_name,
				"name": ["!=", self.name],
			},
			pluck="name",
		)
		if existing:
			frappe.throw(
				_("Skill '{0}' already exists for this employee.").format(self.skill_name)
			)

	def on_update(self):
		"""Track verification changes."""
		if self.is_verified and not self.verified_by:
			self.db_set("verified_by", frappe.session.user)
			self.db_set("verified_on", today())
