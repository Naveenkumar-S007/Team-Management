# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class KPI(Document):
	def validate(self):
		self.validate_dates()
		self.calculate_achievement()

	def validate_dates(self):
		"""Validate start and end dates."""
		if self.start_date and self.end_date:
			if self.start_date > self.end_date:
				frappe.throw(_("Start Date cannot be after End Date."))

	def calculate_achievement(self):
		"""Calculate achievement percentage."""
		if self.target_value and self.target_value > 0:
			if self.current_value is not None:
				self.achievement_percentage = min(
					(self.current_value / self.target_value) * 100, 100
				)
		else:
			self.achievement_percentage = 0

	def update_current_value(self, value):
		"""Update the current value and recalculate achievement."""
		self.db_set("current_value", value)
		self.reload()

	def is_achieved(self):
		"""Check if KPI is achieved (meets or exceeds target)."""
		if self.current_value is None:
			return False
		return self.current_value >= self.target_value

	def is_at_risk(self):
		"""Check if KPI is at risk (below threshold)."""
		if self.current_value is None or self.threshold_value is None:
			return False
		return self.current_value < self.threshold_value

	def get_status(self):
		"""Get KPI status."""
		if self.is_achieved():
			return "Achieved"
		elif self.is_at_risk():
			return "At Risk"
		else:
			return "In Progress"

	def auto_calculate_value(self):
		"""Auto-calculate value based on data source."""
		if self.calculation_method == "Manual":
			return
		
		# This would need custom logic based on data_source
		# For now, just return
		pass
