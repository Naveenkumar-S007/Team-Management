"""API endpoints for the Team Management frontend."""
import frappe
from frappe import _
from frappe.utils import today, now_datetime

@frappe.whitelist()
def create_leave(leave_type, from_date, to_date, reason, team, member=None):
	"""Create a new leave application."""
	try:
		if not member:
			member = frappe.session.user

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
			"naming_series": "LA-.YYYY.-",
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
	leaves = frappe.db.get_list("Leave Application",
		filters={"member": user},
		fields=["name", "leave_type", "from_date", "to_date", "total_days", "reason", "status", "creation"],
		order_by="creation desc",
		limit=20
	)
	return leaves


@frappe.whitelist()
def create_work_log(task_description, hours_spent, team, member=None):
	"""Create a new work log entry."""
	try:
		if not member:
			member = frappe.session.user

		log = frappe.get_doc({
			"doctype": "Work Log",
			"member": member,
			"team": team,
			"date": today(),
			"task_description": task_description,
			"hours_spent": float(hours_spent),
			"status": "Completed",
			"naming_series": "WL-.YYYY.-",
		})
		log.insert(ignore_permissions=True)

		return {"success": True, "name": log.name}
	except Exception as e:
		frappe.log_error(f"Work log creation failed: {str(e)}", "Team Management API")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_recent_work_logs():
	"""Get recent work logs for the user's team."""
	user = frappe.session.user
	logs = frappe.db.get_list("Work Log",
		filters={},
		fields=["name", "member", "team", "date", "task_description", "hours_spent", "creation"],
		order_by="creation desc",
		limit=20
	)
	for log in logs:
		log["member_name"] = frappe.db.get_value("User", log.member, "full_name") or log.member
	return logs


@frappe.whitelist()
def create_team_update(update_type, description, team, member=None):
	"""Create a new team update."""
	try:
		if not member:
			member = frappe.session.user

		update = frappe.get_doc({
			"doctype": "Team Update",
			"member": member,
			"team": team,
			"date": today(),
			"update_type": update_type,
			"description": description,
		})
		update.insert(ignore_permissions=True)

		return {"success": True, "name": update.name}
	except Exception as e:
		frappe.log_error(f"Team update creation failed: {str(e)}", "Team Management API")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_team_updates():
	"""Get recent team updates."""
	user = frappe.session.user
	updates = frappe.db.get_list("Team Update",
		filters={},
		fields=["name", "member", "team", "update_type", "description", "date", "creation"],
		order_by="creation desc",
		limit=20
	)
	for u in updates:
		u["member_name"] = frappe.db.get_value("User", u.member, "full_name") or u.member
	return updates


@frappe.whitelist()
def get_projects():
	"""Get projects for the user's teams."""
	user = frappe.session.user
	projects = frappe.db.get_list("Project",
		filters={},
		fields=["name", "project_name", "status", "priority", "start_date", "end_date", "team"],
		order_by="creation desc",
		limit=20
	)
	return projects


@frappe.whitelist()
def get_team_members():
	"""Get members of the user's teams."""
	user = frappe.session.user
	members = frappe.db.get_list("Team Member",
		filters={},
		fields=["name", "member", "team", "role"],
		order_by="team",
		limit=50
	)
	for m in members:
		m["member_name"] = frappe.db.get_value("User", m.member, "full_name") or m.member
	return members


@frappe.whitelist()
def get_member_details(member):
	"""Get full details of a team member."""
	details = frappe.db.get_value("User", member,
		["full_name", "mobile_no", "designation", "department", "user_image"],
		as_dict=True
	) or {}
	team_member = frappe.db.get_value("Team Member",
		{"member": member},
		["team"],
		as_dict=True
	)
	if team_member:
		details["team"] = team_member.team
		details["team_name"] = frappe.db.get_value("Team", team_member.team, "team_name")
	return details
