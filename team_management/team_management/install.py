# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.modules.utils import sync_customizations


def after_install():
	"""Run after app installation."""
	create_module_def()
	frappe.msgprint(_("Team Management app installed successfully!"))


def after_app_installed(app_name):
	"""Run after app is installed via bench."""
	if app_name == "team_management":
		after_install()


def create_module_def():
	"""Create Module Def for Team Management if it doesn't exist.
	This ensures the workspace card appears on the Frappe v15 homepage
	alongside other modules like HR, Accounting, etc.

	Also re-syncs fixtures so the workspace record and other fixtures
	are guaranteed to exist in the database."""
	if not frappe.db.exists("Module Def", {"module_name": "Team Management"}):
		module_def = frappe.get_doc({
			"doctype": "Module Def",
			"module_name": "Team Management",
			"app_name": "team_management",
			"custom": 1,
		})
		module_def.insert(ignore_permissions=True)

	# Force-sync fixtures to ensure workspace record exists
	sync_customizations("team_management")


def create_team_dashboard_page():
	"""Patch: Create Team Dashboard page and set up module.
	This is a migration patch referenced in patches.txt."""
	create_module_def()


def create_team_management_module_def():
	"""Patch: Ensure Team Management Module Def exists.
	Run via: bench --site [site] migrate
	This is needed so the workspace card shows on the Frappe v15 homepage."""
	create_module_def()
