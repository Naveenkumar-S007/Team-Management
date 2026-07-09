import frappe
from frappe import _
from frappe.utils import today, fmt_money, add_days

no_cache = 1

def get_context(context):
    """Provide context for the Team Portal web page."""
    context.title = "Team Portal"
    context.show_sidebar = False
    context.no_breadcrumbs = True

    if frappe.session.user == "Guest":
        context.message = "Please login to access the Team Portal."
        return context

    user = frappe.session.user
    context.user_fullname = frappe.db.get_value("User", user, "full_name") or user
    context.user_email = user
    context.user_initials = (context.user_fullname[:2]).upper()
    context.roles = frappe.get_roles(user)
    context.is_team_head = "Team Head" in context.roles or "System Manager" in context.roles

    # Get user's teams
    member_teams = frappe.get_all("Team Member",
        filters={"user": user, "is_active": 1}, pluck="parent", distinct=True)
    head_teams = frappe.get_all("Team",
        filters={"team_head": user, "is_active": 1}, pluck="name")
    all_teams = list(set(list(member_teams or []) + list(head_teams or [])))

    context.teams_json = frappe.as_json(all_teams)
    context.primary_team = all_teams[0] if all_teams else ""

    # Get dashboard stats
    stats = {}
    if context.primary_team:
        stats["pending_leaves"] = frappe.db.count("Leave Application",
            {"team": context.primary_team, "status": "Pending Approval"})
        stats["active_projects"] = frappe.db.count("Project",
            {"team": context.primary_team, "status": ["in", ["Planning", "In Progress"]]})
        stats["open_assignments"] = frappe.db.count("Work Assignment",
            {"team": context.primary_team, "status": ["in", ["Open", "Assigned", "In Progress"]]})
        stats["team_updates_today"] = frappe.db.count("Team Update",
            {"team": context.primary_team, "date": today()})
        stats["overdue_tasks"] = frappe.db.count("Work Assignment",
            {"team": context.primary_team,
             "status": ["not in", ["Completed", "Cancelled"]],
             "due_date": ["<", today()]})
        stats["team_members"] = frappe.db.count("Team Member",
            {"parent": context.primary_team, "is_active": 1})
    else:
        stats = {"pending_leaves": 0, "active_projects": 0, "open_assignments": 0,
                 "team_updates_today": 0, "overdue_tasks": 0, "team_members": 0}

    stats["my_logs_today"] = frappe.db.count("Work Log",
        {"member": user, "date": today()})
    stats["my_pending"] = frappe.db.count("Work Assignment",
        {"assigned_to": user, "status": ["in", ["Open", "Assigned", "In Progress"]]})
    stats["upcoming_holidays"] = frappe.db.count("Holiday",
        {"holiday_date": [">=", today()]})

    context.stats_json = frappe.as_json(stats)

    context.leave_types = [
        "Sick Leave", "Personal Leave", "Casual Leave", "Annual Leave",
        "Maternity Leave", "Paternity Leave", "Bereavement Leave",
        "Work From Home", "Compensatory Off", "Other"
    ]
    context.update_types = [
        "Late Arrival", "Early Departure", "Work From Home",
        "Traffic Delay", "Personal Errand", "General Info",
        "Health Update", "Other"
    ]

    return context
