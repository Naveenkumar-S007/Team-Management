# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

"""
Demo data generation for Team Management app.
Run after bench migrate to create sample data.
"""

import frappe
from frappe import _


def _create_demo_data():
	"""Create demo data for testing."""
	# This function is called after migrate to generate demo data
	# Uncomment the following to create demo data on migrate
	
	# _create_demo_team()
	# _create_demo_users()
	
	frappe.db.commit()
