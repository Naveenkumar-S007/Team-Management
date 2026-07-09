# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, getdate, now_datetime
from frappe.utils.user import get_user_fullname


class Announcement(Document):
	def validate(self):
		self.validate_dates()
		self.set_created_by()
		self.check_expiry()

	def validate_dates(self):
		"""Validate start and end dates."""
		if self.start_date and self.end_date:
			if getdate(self.start_date) > getdate(self.end_date):
				frappe.throw(_("Start Date cannot be after End Date."))

	def set_created_by(self):
		"""Set created by if new document."""
		if self.is_new() and not self.created_by:
			self.created_by = frappe.session.user
			self.creation_date = today()

	def check_expiry(self):
		"""Auto-expire announcements past end date."""
		if self.end_date and getdate(self.end_date) < getdate(today()):
			if self.is_active:
				self.db_set("is_active", 0)

	def before_save(self):
		"""Update modified info."""
		pass

	def get_recipients(self):
		"""Get list of recipients for this announcement."""
		if self.team:
			members = frappe.get_all(
				"Team Member",
				filters={"parent": self.team, "is_active": 1},
				pluck="user"
			)
			return members
		else:
			# Company-wide - all enabled users
			users = frappe.get_all(
				"User",
				filters={"enabled": 1, "user_type": "System User"},
				pluck="name"
			)
			return users

	def send_notification(self):
		"""Send email notification to recipients."""
		recipients = self.get_recipients()
		if not recipients:
			return

		frappe.sendmail(
			recipients=recipients,
			subject=self.title,
			message=_("New Announcement: {0}").format(self.title),
			content=self.content
		)

	def pin_announcement(self):
		"""Pin the announcement."""
		self.db_set("is_pinned", 1)

	def unpin_announcement(self):
		"""Unpin the announcement."""
		self.db_set("is_pinned", 0)

	def deactivate(self):
		"""Deactivate the announcement."""
		self.db_set("is_active", 0)
