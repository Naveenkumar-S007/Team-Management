# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _


def after_install():
	"""Run after app installation."""
	frappe.msgprint(_("Team Management app installed successfully!"))


def after_app_installed(app_name):
	"""Run after app is installed via bench."""
	if app_name == "team_management":
		after_install()
