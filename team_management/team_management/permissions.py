# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

"""
Central permission logic for the Team Management app.

Design summary:
- System Manager / HR Manager: unrestricted access to all records.
- Team Head: full access to their team's records.
- Team Member: read access within their team; write/delete only on own records.
"""

import frappe


def _is_system_manager(user):
	"""Check if user is System Manager."""
	roles = frappe.get_roles(user)
	return "System Manager" in roles


def _is_hr_manager(user):
	"""Check if user is HR Manager."""
	roles = frappe.get_roles(user)
	return "HR Manager" in roles


def _is_team_head(user):
	"""Check if user is a Team Head."""
	roles = frappe.get_roles(user)
	return "Team Head" in roles


def _is_privileged(user):
	"""Check if user has elevated privileges."""
	return _is_system_manager(user) or _is_hr_manager(user) or _is_team_head(user)


def _get_user_teams(user):
	"""Get all teams a user belongs to (as member or head)."""
	member_teams = frappe.db.sql_list("""
		SELECT DISTINCT parent
		FROM `tabTeam Member`
		WHERE user = %(user)s AND is_active = 1
	""", {"user": user})

	head_teams = frappe.db.sql_list("""
		SELECT DISTINCT name
		FROM `tabTeam`
		WHERE team_head = %(user)s AND is_active = 1
	""", {"user": user})

	return list(set(member_teams + head_teams))


def _get_user_team_list(user):
	"""Get SQL-safe team list for queries."""
	teams = _get_user_teams(user)
	if not teams:
		return "NULL"
	return ", ".join(frappe.db.escape(t) for t in teams)


# ─── Work Log ────────────────────────────────────────────────────────────

def work_log_query(user):
	"""Permission Query Condition for Work Log list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	if _is_team_head(user):
		teams = _get_user_team_list(user)
		return """(`tabWork Log`.team IN ({teams}))""".format(teams=teams)
	
	# Regular team members can only see their own logs
	return """(`tabWork Log`.member = '{user}')""".format(user=frappe.db.escape(user))


def has_work_log_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		if doc.team in teams:
			return True
	
	# Read access for own logs
	if ptype == "read":
		return doc.member == user or doc.owner == user
	
	# Write/delete only on own logs
	return doc.member == user


# ─── Work Assignment ─────────────────────────────────────────────────────

def work_assignment_query(user):
	"""Permission Query Condition for Work Assignment list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	if _is_team_head(user):
		teams = _get_user_team_list(user)
		return """(`tabWork Assignment`.team IN ({teams}))""".format(teams=teams)
	
	# Regular members see assignments to them
	return """(`tabWork Assignment`.assigned_to = '{user}')""".format(user=frappe.db.escape(user))


def has_work_assignment_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		if doc.team in teams:
			return True
	
	# Read access for assigned work
	if ptype == "read":
		return True
	
	# Team members can update status on their assignments
	if ptype in ("write", "submit"):
		return doc.assigned_to == user
	
	return False


# ─── Leave Application ───────────────────────────────────────────────────

def leave_application_query(user):
	"""Permission Query Condition for Leave Application list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	if _is_team_head(user):
		teams = _get_user_team_list(user)
		return """(`tabLeave Application`.team IN ({teams}))""".format(teams=teams)
	
	# Team members can only see their own leave applications
	return """(`tabLeave Application`.member = '{user}')""".format(user=frappe.db.escape(user))


def has_leave_application_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		if doc.team in teams:
			return True
	
	# Read/Write on own leave applications
	if ptype == "read":
		return doc.member == user
	
	if ptype in ("write", "submit"):
		return doc.member == user
	
	return False


# ─── Team Update ─────────────────────────────────────────────────────────

def team_update_query(user):
	"""Permission Query Condition for Team Update list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	teams = _get_user_team_list(user)
	return """(`tabTeam Update`.team IN ({teams}))""".format(teams=teams)


def has_team_update_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		if doc.team in teams:
			return True
	
	# Read all within team
	if ptype == "read":
		teams = _get_user_teams(user)
		return doc.team in teams
	
	# Write/delete only own posts
	return doc.owner == user


# ─── Project ────────────────────────────────────────────────────────────

def project_query(user):
	"""Permission Query Condition for Project list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	teams = _get_user_team_list(user)
	return """(`tabProject`.team IN ({teams}))""".format(teams=teams)


def has_project_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		return doc.team in teams
	
	# Read access for all team members
	if ptype == "read":
		teams = _get_user_teams(user)
		return doc.team in teams
	
	return False


# ─── Holiday ─────────────────────────────────────────────────────────────

def holiday_query(user):
	"""Permission Query Condition for Holiday list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	teams = _get_user_team_list(user)
	return """(`tabHoliday`.is_company_wide = 1 OR `tabHoliday`.team IN ({teams}))""".format(teams=teams)


def has_holiday_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		if doc.is_company_wide or doc.team in teams:
			return True
	
	# All can read
	if ptype == "read":
		return True
	
	return False


# ─── Work Requirement ────────────────────────────────────────────────────

def work_requirement_query(user):
	"""Permission Query Condition for Work Requirement list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	if _is_team_head(user):
		teams = _get_user_team_list(user)
		return """(`tabWork Requirement`.team IN ({teams}))""".format(teams=teams)
	
	return """(`tabWork Requirement`.requested_by = '{user}')""".format(user=frappe.db.escape(user))


def has_work_requirement_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		if doc.team in teams:
			return True
	
	# Read for team members
	if ptype == "read":
		teams = _get_user_teams(user)
		return doc.team in teams
	
	# Only creator can update
	return doc.requested_by == user


# ─── Employee Skill ──────────────────────────────────────────────────────

def employee_skill_query(user):
	"""Permission Query Condition for Employee Skill list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	if _is_team_head(user):
		teams = _get_user_team_list(user)
		return """EXISTS (
			SELECT 1 FROM `tabTeam Member` tm
			WHERE tm.user = `tabEmployee Skill`.user
			AND tm.parent IN ({teams})
		)""".format(teams=teams)
	
	return """(`tabEmployee Skill`.user = '{user}')""".format(user=frappe.db.escape(user))


def has_employee_skill_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		member = frappe.get_all(
			"Team Member",
			filters={"user": doc.user, "parent": ["in", teams]},
			pluck="name"
		)
		if member:
			return True
	
	# Read/Write own skills
	if ptype == "read":
		return True
	return doc.user == user


# ─── Performance Review ─────────────────────────────────────────────────

def performance_review_query(user):
	"""Permission Query Condition for Performance Review list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	if _is_team_head(user):
		teams = _get_user_team_list(user)
		return """(`tabPerformance Review`.team IN ({teams}))""".format(teams=teams)
	
	return """(`tabPerformance Review`.user = '{user}')""".format(user=frappe.db.escape(user))


def has_performance_review_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		if doc.team in teams:
			return True
	
	# Read own reviews
	if ptype == "read":
		return doc.user == user
	
	return False


# ─── Announcement ────────────────────────────────────────────────────────

def announcement_query(user):
	"""Permission Query Condition for Announcement list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	teams = _get_user_team_list(user)
	return """(`tabAnnouncement`.team IN ({teams}) OR `tabAnnouncement`.team IS NULL)""".format(teams=teams)


def has_announcement_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		if doc.team in teams or not doc.team:
			return True
	
	# All can read announcements
	if ptype == "read":
		return True
	
	return False


# ─── KPI ────────────────────────────────────────────────────────────────

def kpi_query(user):
	"""Permission Query Condition for KPI list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	if _is_team_head(user):
		teams = _get_user_team_list(user)
		return """(`tabKPI`.team IN ({teams}) OR `tabKPI`.team IS NULL)""".format(teams=teams)
	
	return "1=0"


def has_kpi_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		return not doc.team or doc.team in teams
	
	return False


# ─── Resource Allocation ─────────────────────────────────────────────────

def resource_allocation_query(user):
	"""Permission Query Condition for Resource Allocation list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	if _is_team_head(user):
		teams = _get_user_team_list(user)
		return """(`tabResource Allocation`.team IN ({teams}))""".format(teams=teams)
	
	return """(`tabResource Allocation`.user = '{user}')""".format(user=frappe.db.escape(user))


def has_resource_allocation_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		if doc.team in teams:
			return True
	
	if ptype == "read":
		return doc.user == user
	
	return False


# ─── Goal Setting ────────────────────────────────────────────────────────

def goal_setting_query(user):
	"""Permission Query Condition for Goal Setting list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	if _is_team_head(user):
		teams = _get_user_team_list(user)
		return """(`tabGoal Setting`.team IN ({teams}))""".format(teams=teams)
	
	return """(`tabGoal Setting`.user = '{user}')""".format(user=frappe.db.escape(user))


def has_goal_setting_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		if doc.team in teams:
			return True
	
	if ptype == "read":
		return doc.user == user
	
	return False


# ─── Discussion Thread ───────────────────────────────────────────────────

def discussion_thread_query(user):
	"""Permission Query Condition for Discussion Thread list views."""
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return ""
	
	teams = _get_user_team_list(user)
	return """(`tabDiscussion Thread`.team IN ({teams}))""".format(teams=teams)


def has_discussion_thread_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	
	if _is_system_manager(user) or _is_hr_manager(user):
		return True
	
	if _is_team_head(user):
		teams = _get_user_teams(user)
		if doc.team in teams:
			return True
	
	if ptype == "read":
		teams = _get_user_teams(user)
		return doc.team in teams
	
	return doc.created_by == user
