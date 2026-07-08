import frappe
from frappe import _
from datetime import date, datetime

@frappe.whitelist()
def get_dashboard_stats():
	"""Get dashboard statistics for the current user."""
	user = frappe.session.user
	roles = frappe.get_roles(user)
	is_team_head = "Team Head" in roles or "System Manager" in roles
	team = get_user_team(user)

	filters = {}
	if not is_team_head and team:
		filters["team"] = team

	today = date.today()
	today_str = today.isoformat()

	stats = {}

	# Pending leaves
	pending_leaves_filters = {"status": "Pending Approval", "docstatus": 1}
	if not is_team_head and team:
		pending_leaves_filters["team"] = team
	stats["pending_leaves"] = frappe.db.count("Leave Application", pending_leaves_filters)

	# Active projects
	active_filters = {"status": ["in", ["Planning", "In Progress"]]}
	if not is_team_head and team:
		active_filters["team"] = team
	stats["active_projects"] = frappe.db.count("Project", active_filters)

	# Open assignments
	open_filters = {"status": ["in", ["Open", "Assigned", "In Progress"]]}
	if not is_team_head and team:
		open_filters["team"] = team
	stats["open_assignments"] = frappe.db.count("Work Assignment", open_filters)

	# Work logs today
	log_today_filters = {"date": today_str}
	if not is_team_head:
		log_today_filters["member"] = user
	stats["logged_today"] = frappe.db.count("Work Log", log_today_filters)

	# Team updates today
	updates_filters = {"date": today_str}
	if not is_team_head and team:
		updates_filters["team"] = team
	stats["today_updates"] = frappe.db.count("Team Update", updates_filters)

	# Overdue tasks (past due_date and not completed)
	overdue_filters = {
		"status": ["not in", ["Completed", "Cancelled"]],
		"due_date": ["<", today_str]
	}
	if not is_team_head and team:
		overdue_filters["team"] = team
	stats["overdue_tasks"] = frappe.db.count("Work Assignment", overdue_filters)

	return stats


@frappe.whitelist()
def get_recent_activity(limit=15):
	"""Get recent activity across all Team Management doctypes."""
	user = frappe.session.user
	roles = frappe.get_roles(user)
	is_team_head = "Team Head" in roles or "System Manager" in roles
	team = get_user_team(user)

	activities = []

	# Recent Work Logs
	log_fields = ["name", "member", "date", "hours_spent", "task_description", "creation"]
	log_filters = {}
	if not is_team_head and team:
		log_filters["team"] = team
	if not is_team_head:
		log_filters["member"] = user

	logs = frappe.db.get_list("Work Log",
		filters=log_filters,
		fields=log_fields,
		order_by="creation desc",
		limit=limit
	)
	for log in logs:
		user_name = frappe.db.get_value("User", log.member, "full_name") or log.member
		desc = log.task_description[:80] + "..." if log.task_description and len(log.task_description) > 80 else (log.task_description or "")
		hours = f" ({log.hours_spent}h)" if log.hours_spent else ""
		activities.append({
			"doctype": log.doctype,
			"name": log.name,
			"title": f"{user_name} logged work{hours}",
			"description": desc,
			"icon": "📝",
			"icon_color": "blue",
			"creation": log.creation
		})

	# Recent Leave Applications
	leave_fields = ["name", "member", "leave_type", "status", "from_date", "to_date", "creation"]
	leave_filters = {}
	if not is_team_head and team:
		leave_filters["team"] = team
	if not is_team_head:
		leave_filters["member"] = user

	leaves = frappe.db.get_list("Leave Application",
		filters=leave_filters,
		fields=leave_fields,
		order_by="creation desc",
		limit=limit
	)
	for leave in leaves:
		user_name = frappe.db.get_value("User", leave.member, "full_name") or leave.member
		activities.append({
			"doctype": leave.doctype,
			"name": leave.name,
			"title": f"{user_name} - {leave.leave_type}",
			"description": f"{leave.status} ({frappe.utils.format_date(leave.from_date)} to {frappe.utils.format_date(leave.to_date)})",
			"icon": "📋",
			"icon_color": "orange",
			"creation": leave.creation
		})

	# Recent Team Updates
	update_fields = ["name", "member", "update_type", "description", "date", "creation"]
	update_filters = {}
	if not is_team_head and team:
		update_filters["team"] = team
	if not is_team_head:
		update_filters["member"] = user

	updates = frappe.db.get_list("Team Update",
		filters=update_filters,
		fields=update_fields,
		order_by="creation desc",
		limit=limit
	)
	for update in updates:
		user_name = frappe.db.get_value("User", update.member, "full_name") or update.member
		activities.append({
			"doctype": update.doctype,
			"name": update.name,
			"title": f"{user_name} shared an update",
			"description": f"{update.update_type}: {update.description[:80]}..." if update.description and len(update.description) > 80 else f"{update.update_type}: {update.description}",
			"icon": "💬",
			"icon_color": "cyan",
			"creation": update.creation
		})

	# Recent Work Assignments
	assignment_fields = ["name", "assigned_to", "title", "status", "creation"]
	assignment_filters = {}
	if not is_team_head and team:
		assignment_filters["team"] = team
	if not is_team_head:
		assignment_filters["assigned_to"] = user

	assignments = frappe.db.get_list("Work Assignment",
		filters=assignment_filters,
		fields=assignment_fields,
		order_by="creation desc",
		limit=limit
	)
	for assg in assignments:
		user_name = frappe.db.get_value("User", assg.assigned_to, "full_name") or assg.assigned_to
		activities.append({
			"doctype": assg.doctype,
			"name": assg.name,
			"title": f"{user_name} - {assg.title[:50]}..." if assg.title and len(assg.title) > 50 else f"{user_name} - {assg.title}",
			"description": f"Status: {assg.status}",
			"icon": "🎯",
			"icon_color": "purple",
			"creation": assg.creation
		})

	# Sort by creation time (most recent first)
	activities.sort(key=lambda x: x["creation"], reverse=True)

	return activities[:limit]


def get_user_team(user):
	"""Get the team(s) the user belongs to."""
	teams = frappe.db.get_all("Team Member",
		filters={"member": user},
		pluck="team",
		distinct=True
	)
	return teams[0] if teams else None
