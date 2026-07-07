# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	user = frappe.session.user
	roles = frappe.get_roles(user)

	if "Team Head" in roles or "System Manager" in roles:
		data = get_team_wide_data(filters, user, roles)
	else:
		data = get_own_data(filters, user)

	return columns, data


def get_columns():
	return [
		{"label": _("Member"), "fieldname": "member_name", "fieldtype": "Data", "width": 180},
		{"label": _("Team"), "fieldname": "team", "fieldtype": "Link", "options": "Team", "width": 150},
		{"label": _("Completed"), "fieldname": "completed", "fieldtype": "Int", "width": 100},
		{"label": _("In Progress"), "fieldname": "in_progress", "fieldtype": "Int", "width": 100},
		{"label": _("Pending"), "fieldname": "pending", "fieldtype": "Int", "width": 100},
		{"label": _("Total Hours Logged"), "fieldname": "total_hours", "fieldtype": "Float", "width": 150},
	]


def get_team_wide_data(filters, user, roles):
	"""Team Head sees every member of every team they head. System Manager sees all teams."""
	conditions = ""
	values = {}

	if "System Manager" not in roles:
		# restrict to teams headed by this user
		team_names = frappe.get_all("Team", filters={"team_head": user}, pluck="name")
		if not team_names:
			return []
		conditions += " AND wl.team in %(teams)s"
		values["teams"] = team_names

	if filters.get("team"):
		conditions += " AND wl.team = %(team)s"
		values["team"] = filters.get("team")

	if filters.get("from_date"):
		conditions += " AND wl.date >= %(from_date)s"
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions += " AND wl.date <= %(to_date)s"
		values["to_date"] = filters.get("to_date")

	return frappe.db.sql(
		f"""
		SELECT
			u.full_name AS member_name,
			wl.team AS team,
			SUM(CASE WHEN wl.status = 'Completed' THEN 1 ELSE 0 END) AS completed,
			SUM(CASE WHEN wl.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
			SUM(CASE WHEN wl.status = 'Pending' THEN 1 ELSE 0 END) AS pending,
			SUM(wl.hours_spent) AS total_hours
		FROM `tabWork Log` wl
		JOIN `tabUser` u ON u.name = wl.member
		WHERE 1=1 {conditions}
		GROUP BY wl.member, wl.team
		ORDER BY completed DESC
		""",
		values,
		as_dict=1,
	)


def get_own_data(filters, user):
	"""A Team Member only ever sees their own row - never other members' data."""
	conditions = " AND wl.member = %(user)s"
	values = {"user": user}

	if filters.get("from_date"):
		conditions += " AND wl.date >= %(from_date)s"
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions += " AND wl.date <= %(to_date)s"
		values["to_date"] = filters.get("to_date")

	return frappe.db.sql(
		f"""
		SELECT
			u.full_name AS member_name,
			wl.team AS team,
			SUM(CASE WHEN wl.status = 'Completed' THEN 1 ELSE 0 END) AS completed,
			SUM(CASE WHEN wl.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
			SUM(CASE WHEN wl.status = 'Pending' THEN 1 ELSE 0 END) AS pending,
			SUM(wl.hours_spent) AS total_hours
		FROM `tabWork Log` wl
		JOIN `tabUser` u ON u.name = wl.member
		WHERE 1=1 {conditions}
		GROUP BY wl.member, wl.team
		""",
		values,
		as_dict=1,
	)
