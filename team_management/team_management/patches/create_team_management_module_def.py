import frappe
from frappe.utils.fixtures import sync_fixtures


def execute():
	"""Patch: Ensure Team Management Module Def exists and workspace is synced.
	
	This ensures the workspace card appears on the Frappe v15 homepage
	alongside other modules like HR, Accounting, etc.
	"""
	if not frappe.db.exists("Module Def", {"module_name": "Team Management"}):
		module_def = frappe.get_doc({
			"doctype": "Module Def",
			"module_name": "Team Management",
			"app_name": "team_management",
			"custom": 1,
		})
		module_def.insert(ignore_permissions=True)

	# Force-sync fixtures to ensure workspace, roles, and other records exist
	sync_fixtures("team_management")
