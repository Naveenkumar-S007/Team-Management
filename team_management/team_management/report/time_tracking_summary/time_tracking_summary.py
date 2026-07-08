# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, add_days, add_months, getdate


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	user = frappe.session.user
	roles = frappe.get_roles(user)

	if "Team Head" in roles or "System Manager" in roles:
		data = get_team_time_data(filters, user, roles)
	else:
		data = get_own_time_data(filters, user)

	# Add total row
	if data:
		total = {
			"member_name": "<b>Total</b>",
			"total_hours": sum(d.get("total_hours", 0) or 0 for d in data),
			"billable_hours": sum(d.get("billable_hours", 0) or 0 for d in data),
			"log_count": sum(d.get("log_count", 0) or 0 for d in data),
			"avg_hours_per_day": round(
				sum(d.get("total_hours", 0) or 0 for d in data) / max(len(data), 1), 1
			),
		}
		data.append(total)

	return columns, data


def get_columns():
	return [
		{"label": _("Member"), "fieldname": "member_name", "fieldtype": "Data", "width": 180},
		{"label": _("Team"), "fieldname": "team", "fieldtype": "Link", "options": "Team", "width": 120},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
		{"label": _("Total Hours"), "fieldname": "total_hours", "fieldtype": "Float", "width": 110},
		{"label": _("Billable Hours"), "fieldname": "billable_hours", "fieldtype": "Float", "width": 120},
		{"label": _("Log Entries"), "fieldname": "log_count", "fieldtype": "Int", "width": 100},
		{"label": _("Avg Hours/Day"), "fieldname": "avg_hours_per_day", "fieldtype": "Float", "width": 120},
	]


def get_team_time_data(filters, user, roles):
	conditions = ""
	values = {}

	if "System Manager" not in roles:
		team_names = frappe.get_all("Team", filters={"team_head": user}, pluck="name")
		if not team_names:
			return []
		conditions += " AND wl.team IN %(teams)s"
		values["teams"] = team_names

	if filters.get("team"):
		conditions += " AND wl.team = %(team)s"
		values["team"] = filters.get("team")

	if filters.get("from_date"):
		conditions += " AND wl.date >= %(from_date)s"
		values["from_date"] = filters.get("from_date")
	else:
		# Default: last 30 days
		conditions += " AND wl.date >= %(from_date)s"
		values["from_date"] = add_days(today(), -30)

	if filters.get("to_date"):
		conditions += " AND wl.date <= %(to_date)s"
		values["to_date"] = filters.get("to_date")
	else:
		conditions += " AND wl.date <= %(to_date)s"
		values["to_date"] = today()

	if filters.get("member"):
		conditions += " AND wl.member = %(member)s"
		values["member"] = filters.get("member")

	return frappe.db.sql("""
		SELECT
			u.full_name AS member_name,
			wl.team AS team,
			wl.date AS date,
			SUM(wl.hours_spent) AS total_hours,
			SUM(CASE WHEN wa.name IS NOT NULL THEN wl.hours_spent ELSE 0 END) AS billable_hours,
			COUNT(wl.name) AS log_count,
			ROUND(SUM(wl.hours_spent) / GREATEST(COUNT(DISTINCT wl.date), 1), 1) AS avg_hours_per_day
		FROM `tabWork Log` wl
		JOIN `tabUser` u ON u.name = wl.member
		LEFT JOIN `tabWork Assignment` wa ON wa.name = wl.work_assignment
		WHERE 1=1 {conditions}
		GROUP BY wl.member, wl.team, wl.date
		ORDER BY wl.date DESC, total_hours DESC
	""".format(conditions=conditions), values, as_dict=1)


def get_own_time_data(filters, user):
	values = {"user": user}
	conditions = " AND wl.member = %(user)s"

	if filters.get("from_date"):
		conditions += " AND wl.date >= %(from_date)s"
		values["from_date"] = filters.get("from_date")
	else:
		conditions += " AND wl.date >= %(from_date)s"
		values["from_date"] = add_days(today(), -30)

	if filters.get("to_date"):
		conditions += " AND wl.date <= %(to_date)s"
		values["to_date"] = filters.get("to_date")
	else:
		conditions += " AND wl.date <= %(to_date)s"
		values["to_date"] = today()

	if filters.get("team"):
		conditions += " AND wl.team = %(team)s"
		values["team"] = filters.get("team")

	return frappe.db.sql("""
		SELECT
			u.full_name AS member_name,
			wl.team AS team,
			wl.date AS date,
			SUM(wl.hours_spent) AS total_hours,
			SUM(CASE WHEN wa.name IS NOT NULL THEN wl.hours_spent ELSE 0 END) AS billable_hours,
			COUNT(wl.name) AS log_count,
			ROUND(SUM(wl.hours_spent) / GREATEST(COUNT(DISTINCT wl.date), 1), 1) AS avg_hours_per_day
		FROM `tabWork Log` wl
		JOIN `tabUser` u ON u.name = wl.member
		LEFT JOIN `tabWork Assignment` wa ON wa.name = wl.work_assignment
		WHERE 1=1 {conditions}
		GROUP BY wl.member, wl.team, wl.date
		ORDER BY wl.date DESC, total_hours DESC
	""".format(conditions=conditions), values, as_dict=1)
