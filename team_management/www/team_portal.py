import frappe
from frappe import _
from frappe.utils import fmt_money, today, now_datetime

no_cache = 1

def get_context(context):
	"""Provide context for the Team Portal web page."""
	context.title = "Team Portal"
	context.show_sidebar = False
	context.no_breadcrumbs = True

	# Check if user is logged in
	if frappe.session.user == "Guest":
		context.message = "Please login to access the Team Portal."
		return context

	user = frappe.session.user
	context.user_fullname = frappe.db.get_value("User", user, "full_name") or user
	context.user_email = user
	context.roles = frappe.get_roles(user)
	context.is_team_head = "Team Head" in context.roles or "System Manager" in context.roles

	# Get user's team
	team_list = frappe.db.get_all("Team Member", filters={"member": user}, pluck="team", distinct=True)
	context.user_teams = team_list
	context.primary_team = team_list[0] if team_list else None

	# Dashboard stats
	stats = _get_dashboard_stats(user, context.is_team_head, context.primary_team)
	context.stats = stats

	# Recent activity
	context.recent_activity = _get_recent_activity(user, context.is_team_head, context.primary_team, limit=10)

	# Leave types
	context.leave_types = [
		"Sick Leave", "Personal Leave", "Casual Leave", "Annual Leave",
		"Maternity Leave", "Paternity Leave", "Bereavement Leave",
		"Work From Home", "Compensatory Off", "Other"
	]

	# Update types
	context.update_types = [
		"Late Arrival", "Early Departure", "Work From Home",
		"Traffic Delay", "Personal Errand", "General Info",
		"Health Update", "Other"
	]

	return context


def _get_dashboard_stats(user, is_team_head, team):
	"""Get dashboard stats."""
	stats = {}

	# Build filters for team-scoped queries
	base_filter = {}
	if not is_team_head and team:
		base_filter["team"] = team

	user_filter = {}
	if not is_team_head:
		user_filter["member"] = user

	today_str = today()

	# Pending leaves
	stats["pending_leaves"] = frappe.db.count("Leave Application", {
		**base_filter, "status": "Pending Approval", "docstatus": 1
	})

	# Approved leaves today
	stats["approved_leaves_today"] = frappe.db.count("Leave Application", {
		**base_filter, "status": "Approved", "from_date": ["<=", today_str], "to_date": [">=", today_str]
	})

	# Active projects
	stats["active_projects"] = frappe.db.count("Project", {
		**base_filter, "status": ["in", ["Planning", "In Progress"]]
	})

	# Open assignments
	stats["open_assignments"] = frappe.db.count("Work Assignment", {
		**base_filter, "status": ["in", ["Open", "Assigned", "In Progress"]]
	})

	# Completed today
	stats["completed_today"] = frappe.db.count("Work Assignment", {
		**base_filter, "status": "Completed", "modified": [">=", today_str]
	})

	# My work logs today
	stats["my_logs_today"] = frappe.db.count("Work Log", {
		"member": user, "date": today_str
	})

	# Team updates today
	stats["team_updates_today"] = frappe.db.count("Team Update", {
		**base_filter, "date": today_str
	})

	# Overdue assignments
	stats["overdue_tasks"] = frappe.db.count("Work Assignment", {
		**base_filter, "status": ["not in", ["Completed", "Cancelled"]],
		"due_date": ["<", today_str]
	})

	# My pending items (assignments assigned to me)
	stats["my_pending"] = frappe.db.count("Work Assignment", {
		"assigned_to": user, "status": ["in", ["Open", "Assigned", "In Progress"]]
	})

	# Team member count
	if team:
		stats["team_member_count"] = frappe.db.count("Team Member", {"team": team})
	else:
		stats["team_member_count"] = 0

	# Upcoming holidays
	stats["upcoming_holidays"] = frappe.db.count("Holiday", {
		"date": [">=", today_str]
	})

	stats["team_name"] = frappe.db.get_value("Team", team, "team_name") if team else "Not Assigned"
	stats["team_head"] = frappe.db.get_value("Team", team, "team_head") if team else None

	return stats


def _get_recent_activity(user, is_team_head, team, limit=10):
	"""Get combined recent activity."""
	activities = []
	base_filter = {}
	if not is_team_head and team:
		base_filter["team"] = team
	user_filter = {}
	if not is_team_head:
		user_filter["member"] = user

	# Work logs
	logs = frappe.db.get_list("Work Log",
		filters={**base_filter, **user_filter},
		fields=["name", "member", "task_description", "hours_spent", "creation"],
		order_by="creation desc", limit=limit
	)
	for log in logs:
		name = frappe.db.get_value("User", log.member, "full_name") or log.member
		activities.append({
			"type": "Work Log", "name": log.name,
			"title": f"{name} logged {log.hours_spent or 0}h",
			"subtitle": (log.task_description or "")[:60],
			"time": log.creation, "icon": "work", "color": "blue"
		})

	# Leave applications
	leaves = frappe.db.get_list("Leave Application",
		filters={**base_filter, **user_filter},
		fields=["name", "member", "leave_type", "status", "from_date", "creation"],
		order_by="creation desc", limit=limit
	)
	for l in leaves:
		name = frappe.db.get_value("User", l.member, "full_name") or l.member
		activities.append({
			"type": "Leave", "name": l.name,
			"title": f"{name} - {l.leave_type}",
			"subtitle": l.status,
			"time": l.creation, "icon": "leave", "color": "orange"
		})

	# Team updates
	updates = frappe.db.get_list("Team Update",
		filters={**base_filter, **user_filter},
		fields=["name", "member", "update_type", "description", "creation"],
		order_by="creation desc", limit=limit
	)
	for u in updates:
		name = frappe.db.get_value("User", u.member, "full_name") or u.member
		activities.append({
			"type": "Team Update", "name": u.name,
			"title": f"{name} - {u.update_type}",
			"subtitle": (u.description or "")[:60],
			"time": u.creation, "icon": "update", "color": "cyan"
		})

	# Work assignments
	assignments = frappe.db.get_list("Work Assignment",
		filters={**base_filter},
		fields=["name", "assigned_to", "title", "status", "creation"],
		order_by="creation desc", limit=limit
	)
	for a in assignments:
		name = frappe.db.get_value("User", a.assigned_to, "full_name") or a.assigned_to
		activities.append({
			"type": "Assignment", "name": a.name,
			"title": f"{name} - {a.title[:40]}",
			"subtitle": a.status,
			"time": a.creation, "icon": "assignment", "color": "purple"
		})

	activities.sort(key=lambda x: x["time"], reverse=True)
	return activities[:limit]
