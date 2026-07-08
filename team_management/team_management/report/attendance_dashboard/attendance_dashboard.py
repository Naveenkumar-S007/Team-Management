# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, getdate


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	date = filters.get("date") or today()
	user = frappe.session.user
	roles = frappe.get_roles(user)

	if "Team Head" in roles or "System Manager" in roles:
		data = get_team_attendance(filters, date, user, roles)
	else:
		data = get_own_attendance(filters, date, user)

	return columns, data


def get_columns():
	return [
		{"label": _("Member"), "fieldname": "member_name", "fieldtype": "Data", "width": 180},
		{"label": _("Team"), "fieldname": "team", "fieldtype": "Link", "options": "Team", "width": 150},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": _("Details"), "fieldname": "details", "fieldtype": "Data", "width": 300},
		{"label": _("In Time"), "fieldname": "in_time", "fieldtype": "Time", "width": 100},
	]


def get_team_attendance(filters, date, user, roles):
	"""Team Head sees their teams. System Manager sees all teams."""
	team_condition = ""
	values = {"date": date}

	if "System Manager" not in roles:
		team_names = frappe.get_all("Team", filters={"team_head": user}, pluck="name")
		if not team_names:
			return []
		team_condition = " AND t.name IN %(teams)s"
		values["teams"] = team_names

	if filters.get("team"):
		team_condition += " AND t.name = %(filter_team)s"
		values["filter_team"] = filters.get("team")

	# Get all team members
	members = frappe.db.sql("""
		SELECT DISTINCT
			tm.user AS member,
			t.name AS team,
			tm.parent AS team_name
		FROM `tabTeam Member` tm
		JOIN `tabTeam` t ON t.name = tm.parent
		WHERE t.is_active = 1 {team_condition}
		ORDER BY t.name, tm.user
	""".format(team_condition=team_condition), values, as_dict=1)

	if not members:
		return []

	# Get leaves for this date
	leaves = frappe.db.sql("""
		SELECT member, status, leave_type, reason
		FROM `tabLeave Application`
		WHERE %(date)s BETWEEN from_date AND to_date
		AND status = 'Approved'
	""", {"date": date}, as_dict=1)

	leave_map = {}
	for l in leaves:
		leave_map[l.member] = l

	# Get team updates for this date
	updates = frappe.db.sql("""
		SELECT member, update_type, update_time, description
		FROM `tabTeam Update`
		WHERE date = %(date)s
	""", {"date": date}, as_dict=1)

	update_map = {}
	for u in updates:
		if u.member not in update_map:
			update_map[u.member] = []
		update_map[u.member].append(u)

	data = []
	for member in members:
		member_name = frappe.db.get_value("User", member.member, "full_name") or member.member
		status = "Present"
		details = ""
		in_time = None

		# Check if on leave
		if member.member in leave_map:
			leave = leave_map[member.member]
			status = "On Leave"
			details = "{} - {}".format(leave.leave_type, leave.reason or "")

		# Check for team updates (override for more specific status)
		if member.member in update_map:
			for upd in update_map[member.member]:
				if upd.update_type == "Late Arrival":
					status = "Late"
					details = upd.description or "Late arrival"
					in_time = upd.update_time
				elif upd.update_type == "Work From Home":
					status = "WFH"
					details = upd.description or "Working from home"
				elif upd.update_type == "Early Departure":
					if status not in ("On Leave",):
						status = "Early Departure"
						details = upd.description or "Early departure"
				elif upd.update_type == "Sick Report":
					if status not in ("On Leave",):
						status = "Sick"
						details = upd.description or "Reported sick"
				else:
					# Other updates while Present
					if status == "Present":
						details = upd.description or upd.update_type

		data.append({
			"member_name": member_name,
			"team": member.team,
			"status": status,
			"details": details,
			"in_time": in_time,
		})

	return data


def get_own_attendance(filters, date, user):
	"""Team Member sees only their own attendance."""
	member_name = frappe.db.get_value("User", user, "full_name") or user

	# Get teams this member belongs to
	teams = frappe.db.sql_list("""
		SELECT DISTINCT parent
		FROM `tabTeam Member`
		WHERE user = %(user)s
	""", {"user": user})

	head_teams = frappe.db.sql_list("""
		SELECT name FROM `tabTeam`
		WHERE team_head = %(user)s
	""", {"user": user})

	all_teams = list(set(teams + head_teams))

	data = []
	for team in all_teams:
		# Check leave
		leave = frappe.db.sql("""
			SELECT leave_type, reason FROM `tabLeave Application`
			WHERE member = %(user)s
			AND %(date)s BETWEEN from_date AND to_date
			AND status = 'Approved'
		""", {"user": user, "date": date}, as_dict=1)

		status = "Present"
		details = ""
		in_time = None

		if leave:
			status = "On Leave"
			details = "{} - {}".format(leave[0].leave_type, leave[0].reason or "")

		# Check team updates
		updates = frappe.db.sql("""
			SELECT update_type, update_time, description
			FROM `tabTeam Update`
			WHERE member = %(user)s AND date = %(date)s
		""", {"user": user, "date": date}, as_dict=1)

		for upd in updates:
			if upd.update_type == "Late Arrival":
				status = "Late"
				details = upd.description or "Late arrival"
				in_time = upd.update_time
			elif upd.update_type == "Work From Home":
				status = "WFH"
				details = upd.description or "Working from home"
			elif upd.update_type == "Early Departure" and status not in ("On Leave",):
				status = "Early Departure"
				details = upd.description or "Early departure"
			elif upd.update_type == "Sick Report" and status not in ("On Leave",):
				status = "Sick"
				details = upd.description or "Reported sick"
			elif status == "Present":
				details = upd.description or upd.update_type

		data.append({
			"member_name": member_name,
			"team": team,
			"status": status,
			"details": details,
			"in_time": in_time,
		})

	return data
