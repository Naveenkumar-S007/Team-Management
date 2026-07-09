# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TeamCapacity(Document):
	def validate(self):
		self.calculate_utilization()

	def calculate_utilization(self):
		"""Calculate utilization percentage based on available and booked hours."""
		if self.available_hours and self.available_hours > 0:
			self.utilization_percentage = (self.booked_hours or 0) / self.available_hours * 100
		else:
			self.utilization_percentage = 0
