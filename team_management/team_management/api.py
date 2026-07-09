"""API endpoints for the Team Management module."""
import frappe
from frappe import _
from frappe.utils import today, now_datetime, add_days


def validate_user_access(user=None, team=None):
	"""Validate user has access to the requested team."""
	if not user:
		user = frappe.session.user
	
	roles = frappe.get_roles(user)
	if "System Manager" in roles or "HR Manager" in roles:
		return True
	
	if team:
		is_head = frappe.db.get_value("Team", team, "team_head") == user
		is_member = frappe.db.exists(
			"Team Member",
			{"parent": team, "user": user, "is_active": 1}
		)
		if is_head or is_member:
			return True
	
	return False


@frappe.whitelist()
def get_teams_for_user(user=None):
	"""Return all teams a user belongs to."""
	if not user:
		user = frappe.session.user
	
	member_teams = frappe.get_all(
		"Team Member",
		filters={"user": user, "is_active": 1},
		pluck="parent"
	)
	
	head_teams = frappe.get_all(
		"Team",
		filters={"team_head": user, "is_active": 1},
		pluck="name"
	)
	
	return list(set(member_teams + head_teams))


@frappe.whitelist()
def get_team_info(team):
	"""Return basic information about a team."""
	if not validate_user_access(team=team):
		frappe.throw(_("You don't have access to this team."))
	
	team_doc = frappe.get_doc("Team", team)
	return {
		"name": team_doc.name,
		"team_name": team_doc.team_name,
		"team_head": team_doc.team_head,
		"department": team_doc.department,
		"is_active": team_doc.is_active,
		"creation": team_doc.creation,
		"members": [
			{"user": m.user, "designation": m.designation, "joined_on": m.joined_on, "is_active": m.is_active}
			for m in team_doc.members if m.is_active
		],
	}


@frappe.whitelist()
def get_team_members(team):
	"""Return active members of a team."""
	if not validate_user_access(team=team):
		frappe.throw(_("You don't have access to this team."))
	
	team_doc = frappe.get_doc("Team", team)
	active_members = [m for m in team_doc.members if m.is_active]
	
	member_details = []
	for member in active_members:
		user_doc = frappe.get_doc("User", member.user)
		member_details.append({
			"user": member.user,
			"full_name": user_doc.full_name,
			"email": user_doc.email,
			"designation": member.designation,
			"joined_on": member.joined_on,
		})
	return member_details


@frappe.whitelist()
def create_leave(leave_type, from_date, to_date, reason, team, member=None):
	"""Create a new leave application."""
	try:
		if not member:
			member = frappe.session.user
		
		if not validate_user_access(team=team) and "Team Head" not in frappe.get_roles():
			frappe.throw(_("You don't have access to this team."))
		
		from frappe.utils import date_diff
		days = date_diff(to_date, from_date) + 1
		
		leave = frappe.get_doc({
			"doctype": "Leave Application",
			"member": member,
			"team": team,
			"leave_type": leave_type,
			"from_date": from_date,
			"to_date": to_date,
			"reason": reason,
			"total_days": days,
			"status": "Pending Approval",
		})
		leave.insert(ignore_permissions=True)
		
		return {"success": True, "name": leave.name}
	except Exception as e:
		frappe.log_error(f"Leave creation failed: {str(e)}", "Team Management API")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_my_leaves():
	"""Get leave applications for the current user."""
	user = frappe.session.user
	return frappe.get_all(
		"Leave Application",
		filters={"member": user},
		fields=["name", "leave_type", "from_date", "to_date", "total_days", "reason", "status", "creation"],
		order_by="creation desc",
		limit=20
	)


@frappe.whitelist()
def create_work_log(task_description, hours_spent, team, member=None, work_assignment=None):
	"""Create a new work log entry."""
	try:
		if not member:
			member = frappe.session.user
		
		if not validate_user_access(team=team) and "Team Head" not in frappe.get_roles():
			frappe.throw(_("You don't have access to this team."))
		
		log = frappe.get_doc({
			"doctype": "Work Log",
			"member": member,
			"team": team,
			"date": today(),
			"task_description": task_description,
			"hours_spent": float(hours_spent),
			"status": "Completed",
			"work_assignment": work_assignment,
		})
		log.insert(ignore_permissions=True)
		
		return {"success": True, "name": log.name}
	except Exception as e:
		frappe.log_error(f"Work log creation failed: {str(e)}", "Team Management API")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_recent_work_logs(team=None, member=None):
	"""Get recent work logs for the user's team."""
	filters = {}
	if team:
		if not validate_user_access(team=team):
			frappe.throw(_("You don't have access to this team."))
		filters["team"] = team
	if member:
		filters["member"] = member
	
	logs = frappe.get_all(
		"Work Log",
		filters=filters,
		fields=["name", "member", "team", "date", "task_description", "hours_spent", "creation"],
		order_by="creation desc",
		limit=20
	)
	for log in logs:
		log["member_name"] = frappe.db.get_value("User", log.member, "full_name") or log.member
	return logs


@frappe.whitelist()
def get_work_assignments(team=None, status=None):
	"""Get work assignments."""
	filters = {}
	if team:
		if not validate_user_access(team=team):
			frappe.throw(_("You don't have access to this team."))
		filters["team"] = team
	if status:
		filters["status"] = status
	
	return frappe.get_all(
		"Work Assignment",
		filters=filters,
		fields=["name", "title", "assigned_to", "team", "status", "priority", "due_date", "assigned_date"],
		order_by="due_date asc",
		limit=50
	)


@frappe.whitelist()
def create_team_update(description, team, member=None, title=None):
	"""Create a new team update."""
	try:
		if not member:
			member = frappe.session.user
		
		if not validate_user_access(team=team):
			frappe.throw(_("You don't have access to this team."))
		
		update = frappe.get_doc({
			"doctype": "Team Update",
			"posted_by": member,
			"team": team,
			"title": title or f"Update - {today()}",
			"update_content": description,
		})
		update.insert(ignore_permissions=True)
		
		return {"success": True, "name": update.name}
	except Exception as e:
		frappe.log_error(f"Team update creation failed: {str(e)}", "Team Management API")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_team_updates(team):
	"""Get recent team updates."""
	if not validate_user_access(team=team):
		frappe.throw(_("You don't have access to this team."))
	
	updates = frappe.get_all(
		"Team Update",
		filters={"team": team},
		fields=["name", "title", "update_content", "posted_by", "creation"],
		order_by="creation desc",
		limit=20
	)
	for u in updates:
		u["posted_by_name"] = frappe.db.get_value("User", u.posted_by, "full_name") or u.posted_by
	return updates


@frappe.whitelist()
def get_projects(team=None):
	"""Get projects for teams."""
	filters = {"is_active": 1}
	if team:
		if not validate_user_access(team=team):
			frappe.throw(_("You don't have access to this team."))
		filters["team"] = team
	
	return frappe.get_all(
		"Project",
		filters=filters,
		fields=["name", "project_name", "status", "priority", "start_date", "end_date", "team", "progress"],
		order_by="creation desc",
		limit=20
	)


@frappe.whitelist()
def get_announcements(team=None):
	"""Get announcements."""
	filters = {"is_active": 1}
	if team:
		filters["team"] = ["in", [team, None]]
	else:
		filters["team"] = ["is", "not set"]
	
	return frappe.get_all(
		"Announcement",
		filters=filters,
		fields=["name", "title", "content", "announcement_type", "priority", "start_date", "end_date"],
		order_by="creation desc",
		limit=10
	)


@frappe.whitelist()
def get_team_stats(team):
	"""Return statistics for a team."""
	if not validate_user_access(team=team):
		frappe.throw(_("You don't have access to this team."))
	
	total_members = frappe.db.count("Team Member", {"parent": team, "is_active": 1})
	active_assignments = frappe.db.count("Work Assignment", {"team": team, "status": ["in", ["Assigned", "In Progress"]]})
	completed_assignments = frappe.db.count("Work Assignment", {"team": team, "status": "Completed"})
	total_projects = frappe.db.count("Project", {"team": team})
	pending_leaves = frappe.db.count("Leave Application", {"team": team, "status": "Pending Approval"})
	
	week_start = add_days(today(), -7)
	hours_this_week = frappe.db.sql(
		"SELECT COALESCE(SUM(wl.hours_spent), 0) FROM `tabWork Log` wl WHERE wl.team = %s AND wl.date >= %s",
		[team, week_start],
	)[0][0]
	
	return {
		"total_members": total_members,
		"active_assignments": active_assignments,
		"completed_assignments": completed_assignments,
		"total_projects": total_projects,
		"pending_leaves": pending_leaves,
		"hours_this_week": hours_this_week,
	}


@frappe.whitelist()
def get_member_stats(member=None):
	"""Return statistics for a team member."""
	if not member:
		member = frappe.session.user
	
	assigned_count = frappe.db.count("Work Assignment", {"assigned_to": member})
	completed_count = frappe.db.count("Work Assignment", {"assigned_to": member, "status": "Completed"})
	pending_count = frappe.db.count("Work Assignment", {"assigned_to": member, "status": ["!=", "Completed"]})
	
	week_start = add_days(today(), -7)
	hours_this_week = frappe.db.sql(
		"SELECT COALESCE(SUM(wl.hours_spent), 0) FROM `tabWork Log` wl WHERE wl.member = %s AND wl.date >= %s",
		[member, week_start],
	)[0][0]
	
	return {
		"assigned_count": assigned_count,
		"completed_count": completed_count,
		"pending_count": pending_count,
		"hours_this_week": hours_this_week,
	}


@frappe.whitelist()
def get_employee_skills(user=None):
	"""Return skills for an employee."""
	if not user:
		user = frappe.session.user
	
	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
	if not employee:
		return []
	
	return frappe.get_all(
		"Employee Skill",
		filters={"employee": employee},
		fields=["name", "skill_name", "skill_type", "proficiency_level", "years_of_experience"],
		order_by="skill_name asc",
	)


@frappe.whitelist()
def get_team_kpis(team=None):
	"""Return KPIs for a team."""
	if team and not validate_user_access(team=team):
		frappe.throw(_("You don't have access to these KPIs."))
	
	filters = {"is_active": 1}
	if team:
		filters["team"] = team
	
	return frappe.get_all(
		"KPI",
		filters=filters,
		fields=["name", "kpi_name", "kpi_type", "target_value", "current_value", "achievement_percentage"],
		order_by="kpi_name asc",
	)


@frappe.whitelist()
def get_discussion_threads(team):
	"""Return discussion threads for a team."""
	if not validate_user_access(team=team):
		frappe.throw(_("You don't have access to this team."))
	
	return frappe.get_all(
		"Discussion Thread",
		filters={"team": team},
		fields=["name", "title", "is_pinned", "is_resolved", "created_by", "creation", "last_post_on"],
		order_by="is_pinned desc, last_post_on desc",
		limit=20
	)


@frappe.whitelist()
def get_resource_allocations(team=None):
	"""Return resource allocations."""
	if team and not validate_user_access(team=team):
		frappe.throw(_("You don't have access to these allocations."))
	
	filters = {"status": ["!=", "Cancelled"]}
	if team:
		filters["team"] = team
	
	return frappe.get_all(
		"Resource Allocation",
		filters=filters,
		fields=["name", "employee", "user", "team", "project", "allocation_type", "start_date", "end_date", "allocated_hours", "status"],
		order_by="start_date desc",
	)


@frappe.whitelist()
def update_assignment_status(assignment, status):
	"""Update the status of a work assignment."""
	assignment_doc = frappe.get_doc("Work Assignment", assignment)
	
	if frappe.session.user != assignment_doc.assigned_to and "Team Head" not in frappe.get_roles():
		frappe.throw(_("Only the assigned member or Team Head can update the status."))
	
	assignment_doc.db_set("status", status)
	frappe.db.commit()
	return {"success": True}
