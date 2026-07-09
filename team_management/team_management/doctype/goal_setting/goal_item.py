# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class GoalItem(Document):
	def validate(self):
		self.calculate_progress()
		self.update_status()

	def calculate_progress(self):
		"""Calculate progress based on current vs target value."""
		if self.target_value and self.target_value > 0:
			if self.current_value is not None:
				self.progress = min((self.current_value / self.target_value) * 100, 100)
		elif self.progress and not self.target_value:
			# Allow manual progress entry if no target value
			pass

	def update_status(self):
		"""Auto-update status based on progress."""
		if self.progress is not None:
			if self.progress >= 100:
				self.status = "Completed"
			elif self.progress > 0:
				self.status = "In Progress"
			elif self.progress == 0:
				self.status = "Not Started"
