# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate, nowdate


class LeaveApplication(Document):
	def validate(self):
		self.validate_dates()
		self.calculate_total_days()
		self.validate_team_membership()
		self.validate_holiday_overlap()
		self.validate_duplicate_leave()

	def validate_dates(self):
		"""Validate leave dates."""
		if self.from_date and self.to_date:
			if getdate(self.from_date) > getdate(self.to_date):
				frappe.throw(_("From Date cannot be after To Date."))

	def calculate_total_days(self):
		"""Calculate total leave days."""
		if self.from_date and self.to_date:
			days = date_diff(getdate(self.to_date), getdate(self.from_date)) + 1
			if self.half_day:
				self.total_days = 0.5
			else:
				self.total_days = days

	def validate_team_membership(self):
		"""Verify the member belongs to the selected team."""
		if self.is_new() or self.has_value_changed("team"):
			if not self.team:
				return
			is_member = frappe.db.exists(
				"Team Member",
				{"parenttype": "Team", "parent": self.team, "user": self.member, "is_active": 1},
			)
			is_head = frappe.db.get_value("Team", self.team, "team_head") == self.member
			if not is_member and not is_head:
				frappe.throw(_("The selected member is not part of this team."))

	def validate_holiday_overlap(self):
		"""Warn if the leave period overlaps with company or team holidays."""
		if not self.from_date or not self.to_date:
			return

		company_holidays = frappe.db.sql("""
			SELECT holiday_name, holiday_date
			FROM `tabHoliday`
			WHERE (is_company_wide = 1 OR team = %(team)s OR team IS NULL)
			AND holiday_date BETWEEN %(from_date)s AND %(to_date)s
		""", {
			"team": self.team,
			"from_date": self.from_date,
			"to_date": self.to_date,
		}, as_dict=1)

		if company_holidays:
			holiday_names = ", ".join([h.holiday_name for h in company_holidays])
			holiday_dates = ", ".join([str(h.holiday_date) for h in company_holidays])
			frappe.msgprint(
				_("Note: Your leave period overlaps with the following holidays:<br>"
				  "<b>{0}</b> on {1}.<br>"
				  "Total days may include holiday(s).").format(holiday_names, holiday_dates),
				indicator="orange",
				alert=True,
			)

	def validate_duplicate_leave(self):
		"""Check for overlapping leave applications."""
		if not self.member or not self.from_date or not self.to_date:
			return
		
		existing = frappe.get_all(
			"Leave Application",
			filters={
				"member": self.member,
				"name": ["!=", self.name],
				"status": ["!=", "Rejected"],
				"from_date": ["<=", self.to_date],
				"to_date": [">=", self.from_date],
			},
			pluck="name"
		)
		
		if existing:
			frappe.throw(
				_("An overlapping leave application already exists: {0}").format(existing[0])
			)

	def on_update(self):
		"""Track approval after workflow transitions."""
		if self.is_new():
			return

		old_doc = self.get_doc_before_save()
		if not old_doc:
			return

		if old_doc.status == "Pending Approval" and self.status in ("Approved", "Rejected"):
			roles = frappe.get_roles(frappe.session.user)
			if "Team Head" not in roles and "System Manager" not in roles and "HR Manager" not in roles:
				frappe.throw(_("Only Team Head, HR Manager, or System Manager can approve or reject leave applications."))

			if not self.approved_by:
				self.db_set("approved_by", frappe.session.user)
				self.db_set("approval_date", nowdate())
