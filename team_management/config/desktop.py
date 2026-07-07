from frappe import _


def get_data():
	return [
		{
			"module_name": "Team Management",
			"category": "Modules",
			"label": _("Team Management"),
			"color": "#2E86DE",
			"icon": "octicon octicon-checklist",
			"type": "module",
			"description": "Manage team requirements, work assignments and work logs.",
		}
	]
