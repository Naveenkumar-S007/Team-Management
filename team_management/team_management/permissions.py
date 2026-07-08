# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

"""
Central permission logic for the Team Management app.

Design summary:
- System Manager / Team Head: unrestricted access to all records.
- Team Member: transparent read access across the team; write/delete only
  on own records. For Leave Applications: can only see own. For Team Updates:
  can see all within the team.
"""

import frappe


def _is_privileged(user):
	roles = frappe.get_roles(user)
	return "Team Head" in roles or "System Manager" in roles


# ─── Work Log ────────────────────────────────────────────────────────────

def work_log_query(user):
	"""Permission Query Condition for Work Log list views."""
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return ""
	return ""


def has_work_log_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return True

	if ptype == "read":
		return True

	return doc.owner == user


# ─── Work Assignment ─────────────────────────────────────────────────────

def work_assignment_query(user):
	"""Permission Query Condition for Work Assignment list views."""
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return ""
	return ""


def has_work_assignment_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return True

	if ptype == "read":
		return True

	if ptype == "create":
		return False

	return doc.assigned_to == user


# ─── Leave Application ───────────────────────────────────────────────────

def leave_application_query(user):
	"""Permission Query Condition for Leave Application list views.
	- System Manager / Team Head: see all leave applications.
	- Team Member: see only their own leave applications."""
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return ""
	return """(`tabLeave Application`.member = '{user}')""".format(user=frappe.db.escape(user))


def has_leave_application_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return True

	if ptype == "read":
		# Team Members can only read their own leave applications
		return doc.member == user

	# write / delete / submit - only the owner and head
	if doc.member == user:
		return True

	return False


# ─── Team Update ─────────────────────────────────────────────────────────

def team_update_query(user):
	"""Permission Query Condition for Team Update list views.
	- System Manager / Team Head: see all updates.
	- Team Member: see updates within their team only."""
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return ""

	# Get teams this member belongs to
	member_teams = frappe.db.sql_list("""
		SELECT DISTINCT parent
		FROM `tabTeam Member`
		WHERE user = %(user)s
	""", {"user": user})

	# Also get teams where user is the Team Head
	head_teams = frappe.db.sql_list("""
		SELECT DISTINCT name
		FROM `tabTeam`
		WHERE team_head = %(user)s
	""", {"user": user})

	all_teams = list(set(member_teams + head_teams))
	if not all_teams:
		return "1=0"  # No teams - no results

	team_list = ", ".join(frappe.db.escape(t) for t in all_teams)
	return """(`tabTeam Update`.team IN ({teams}))""".format(teams=team_list)


# ─── Project ────────────────────────────────────────────────────────────

def project_query(user):
	"""Permission Query Condition for Project list views."""
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return ""
	# Team Members see projects within their team
	member_teams = frappe.db.sql_list("""
		SELECT DISTINCT parent
		FROM `tabTeam Member`
		WHERE user = %(user)s
	""", {"user": user})

	head_teams = frappe.db.sql_list("""
		SELECT DISTINCT name
		FROM `tabTeam`
		WHERE team_head = %(user)s
	""", {"user": user})

	all_teams = list(set(member_teams + head_teams))
	if not all_teams:
		return "1=0"

	team_list = ", ".join(frappe.db.escape(t) for t in all_teams)
	return """(`tabProject`.team IN ({teams}))""".format(teams=team_list)


def has_project_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return True

	if ptype == "read":
		return True  # Team Members can read projects in their team

	# write/delete - only Team Head / System Manager
	return False


# ─── Holiday ─────────────────────────────────────────────────────────────

def holiday_query(user):
	"""Permission Query Condition for Holiday list views."""
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return ""
	# Team Members see company-wide holidays and holidays for their teams
	member_teams = frappe.db.sql_list("""
		SELECT DISTINCT parent
		FROM `tabTeam Member`
		WHERE user = %(user)s
	""", {"user": user})

	head_teams = frappe.db.sql_list("""
		SELECT DISTINCT name
		FROM `tabTeam`
		WHERE team_head = %(user)s
	""", {"user": user})

	all_teams = list(set(member_teams + head_teams))
	if not all_teams:
		team_condition = ""
	else:
		team_list = ", ".join(frappe.db.escape(t) for t in all_teams)
		team_condition = " OR team IN ({teams})".format(teams=team_list)

	return """(`tabHoliday`.is_company_wide = 1{team_condition})""".format(team_condition=team_condition)


def has_holiday_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return True

	if ptype == "read":
		return True  # All can read holidays

	# write/delete - only Team Head / System Manager
	return False


# ─── Team Update ─────────────────────────────────────────────────────────

def has_team_update_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return True

	if ptype == "read":
		# Team Members can see all updates within their team
		return True

	# write / delete - only the owner can edit their own update
	return doc.owner == user
