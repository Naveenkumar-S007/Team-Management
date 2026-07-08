import frappe

no_cache = 1

def get_context(context):
	frappe.local.flags.redirect_location = "/team_portal"
	raise frappe.Redirect
