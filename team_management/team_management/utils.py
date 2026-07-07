# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, add_days, get_url_to_form


def _team_head_emails(team):
	if not team:
		return []
	head = frappe.db.get_value("Team", team, "team_head")
	return [head] if head else []


def _team_member_emails(team):
	if not team:
		return []
	members = frappe.get_all(
		"Team Member",
		filters={"parenttype": "Team", "parent": team},
		pluck="user",
	)
	return members


def notify_team_head_new_requirement(doc, method=None):
	"""Fired after_insert on Work Requirement -> email the Team Head."""
	recipients = _team_head_emails(doc.team)
	if not recipients:
		return
	frappe.sendmail(
		recipients=recipients,
		subject=_("New Requirement Raised: {0}").format(doc.requirement_title),
		message=_(
			"A new requirement <b>{0}</b> has been raised by {1} for your team.<br><br>"
			"Priority: {2}<br>Due Date: {3}<br><br>"
			"<a href='{4}'>Open Requirement</a>"
		).format(
			doc.requirement_title,
			frappe.db.get_value("User", doc.requested_by, "full_name") or doc.requested_by,
			doc.priority,
			doc.due_date or "-",
			get_url_to_form(doc.doctype, doc.name),
		),
	)


def notify_member_new_assignment(doc, method=None):
	"""Fired after_insert on Work Assignment -> email the assigned member."""
	if not doc.assigned_to:
		return
	frappe.sendmail(
		recipients=[doc.assigned_to],
		subject=_("New Work Assigned: {0}").format(doc.name),
		message=_(
			"You have been assigned new work by {0}.<br><br>"
			"Priority: {1}<br>Due Date: {2}<br>Instructions: {3}<br><br>"
			"<a href='{4}'>Open Assignment</a>"
		).format(
			frappe.db.get_value("User", doc.assigned_by, "full_name") or doc.assigned_by,
			doc.priority,
			doc.due_date or "-",
			frappe.utils.strip_html(doc.instructions or ""),
			get_url_to_form(doc.doctype, doc.name),
		),
	)

	# Also notify the rest of the team, so everyone stays aware of what's assigned
	team_members = _team_member_emails(doc.team)
	other_members = [m for m in team_members if m != doc.assigned_to]
	if other_members:
		frappe.sendmail(
			recipients=other_members,
			subject=_("Team Update: New Work Assigned to {0}").format(
				frappe.db.get_value("User", doc.assigned_to, "full_name") or doc.assigned_to
			),
			message=_("A new task '{0}' has been assigned within the team.").format(doc.name),
		)


def notify_member_assignment_update(doc, method=None):
	if doc.has_value_changed("status") and doc.status == "Completed":
		head_emails = _team_head_emails(doc.team)
		if head_emails:
			frappe.sendmail(
				recipients=head_emails,
				subject=_("Task Completed: {0}").format(doc.name),
				message=_("{0} has marked the assignment '{1}' as Completed.").format(
					frappe.db.get_value("User", doc.assigned_to, "full_name") or doc.assigned_to,
					doc.name,
				),
			)


def send_overdue_task_reminders():
	"""Daily scheduled job: nudge members (and cc the Team Head) about overdue work."""
	overdue = frappe.get_all(
		"Work Assignment",
		filters={"due_date": ["<", today()], "status": ["not in", ["Completed"]]},
		fields=["name", "assigned_to", "team", "due_date"],
	)
	for row in overdue:
		head_emails = _team_head_emails(row.team)
		recipients = [row.assigned_to] + head_emails
		frappe.sendmail(
			recipients=list(set(recipients)),
			subject=_("Overdue Task Reminder: {0}").format(row.name),
			message=_("The task {0} was due on {1} and is still not marked Completed.").format(
				row.name, row.due_date
			),
		)


def send_weekly_team_summary():
	"""Weekly scheduled job: send each Team Head a digest of their team's progress."""
	teams = frappe.get_all("Team", fields=["name", "team_head"])
	for team in teams:
		if not team.team_head:
			continue
		completed = frappe.db.count(
			"Work Log", {"team": team.name, "status": "Completed", "date": [">=", add_days(today(), -7)]}
		)
		pending = frappe.db.count("Work Log", {"team": team.name, "status": ["!=", "Completed"]})
		frappe.sendmail(
			recipients=[team.team_head],
			subject=_("Weekly Team Summary: {0}").format(team.name),
			message=_(
				"Weekly summary for <b>{0}</b>:<br>Completed this week: {1}<br>Currently Pending: {2}"
			).format(team.name, completed, pending),
		)
