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


# ─── Work Requirement Notifications ──────────────────────────────────────

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


# ─── Work Assignment Notifications ───────────────────────────────────────

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


# ─── Leave Application Notifications ─────────────────────────────────────

def notify_team_head_new_leave(doc, method=None):
	"""Fired after_insert on Leave Application -> email the Team Head."""
	recipients = _team_head_emails(doc.team)
	if not recipients:
		return
	frappe.sendmail(
		recipients=recipients,
		subject=_("New Leave Application: {0}").format(doc.name),
		message=_(
			"A new leave application has been submitted by <b>{0}</b>.<br><br>"
			"Leave Type: {1}<br>"
			"From: {2} To: {3}<br>"
			"Total Days: {4}<br>"
			"Reason: {5}<br><br>"
			"<a href='{6}'>Open Leave Application</a>"
		).format(
			frappe.db.get_value("User", doc.member, "full_name") or doc.member,
			doc.leave_type,
			doc.from_date,
			doc.to_date,
			doc.total_days,
			doc.reason,
			get_url_to_form(doc.doctype, doc.name),
		),
	)


def notify_leave_status_change(doc, method=None):
	"""Fired on_update on Leave Application -> notify member when status changes."""
	if doc.is_new():
		return

	old_doc = doc.get_doc_before_save()
	if not old_doc:
		return

	if old_doc.status != doc.status and doc.status in ("Approved", "Rejected"):
		status_text = _("Approved") if doc.status == "Approved" else _("Rejected")
		frappe.sendmail(
			recipients=[doc.member],
			subject=_("Leave Application {0}: {1}").format(status_text, doc.name),
			message=_(
				"Your leave application <b>{0}</b> has been <b>{1}</b>.<br><br>"
				"Leave Type: {2}<br>"
				"From: {3} To: {4}<br>"
				"Days: {5}<br>"
				"Reason: {6}<br><br>"
				"Approved/Rejected By: {7}<br>"
				"Remarks: {8}<br><br>"
				"<a href='{9}'>Open Leave Application</a>"
			).format(
				doc.name,
				status_text,
				doc.leave_type,
				doc.from_date,
				doc.to_date,
				doc.total_days,
				doc.reason,
				frappe.db.get_value("User", doc.approved_by, "full_name") or doc.approved_by,
				doc.approval_remarks or _("N/A"),
				get_url_to_form(doc.doctype, doc.name),
			),
		)


# ─── Team Update Notifications ───────────────────────────────────────────

def notify_team_of_update(doc, method=None):
	"""Fired after_insert on Team Update -> notify all team members and head."""
	member_name = frappe.db.get_value("User", doc.member, "full_name") or doc.member

	recipients = list(set(
		_team_head_emails(doc.team) + _team_member_emails(doc.team)
	))
	# Don't notify the person who posted the update
	recipients = [r for r in recipients if r != doc.member]

	if not recipients:
		return

	frappe.sendmail(
		recipients=recipients,
		subject=_("Team Update from {0}: {1}").format(member_name, doc.update_type),
		message=_(
			"<b>{0}</b> posted a team update.<br><br>"
			"Type: {1}<br>"
			"Date: {2}<br>"
			"{3}<br><br>"
			"Message: {4}<br><br>"
			"<a href='{5}'>View Update</a>"
		).format(
			member_name,
			doc.update_type,
			doc.date,
			_("Expected Time: {0}").format(doc.update_time) if doc.update_time else "",
			doc.description,
			get_url_to_form(doc.doctype, doc.name),
		),
	)


# ─── Project Notifications ──────────────────────────────────────────────

def notify_team_new_project(doc, method=None):
	"""Fired after_insert on Project -> notify all team members."""
	recipients = list(set(
		_team_head_emails(doc.team) + _team_member_emails(doc.team)
	))
	if not recipients:
		return

	frappe.sendmail(
		recipients=recipients,
		subject=_("New Project Started: {0}").format(doc.project_name),
		message=_(
			"A new project <b>{0}</b> has been started in your team.<br><br>"
			"Priority: {1}<br>"
			"Start Date: {2}<br>"
			"Target End Date: {3}<br><br>"
			"<a href='{4}'>Open Project</a>"
		).format(
			doc.project_name,
			doc.priority,
			doc.start_date or "-",
			doc.end_date or "-",
			get_url_to_form(doc.doctype, doc.name),
		),
	)


# ─── Scheduled Jobs ──────────────────────────────────────────────────────

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
