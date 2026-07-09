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


# ─── Additional Scheduled Jobs ────────────────────────────────────────────────

def check_leave_expiring():
	"""Daily job: Check for leaves expiring soon and send reminders."""
	from frappe.utils import date_diff
	
	expiry_date = add_days(today(), 3)
	
	expiring_leaves = frappe.get_all(
		"Leave Application",
		filters={
			"status": "Approved",
			"to_date": ["<=", expiry_date],
			"to_date": [">=", today()],
		},
		fields=["name", "member", "leave_type", "to_date"],
	)
	
	for leave in expiring_leaves:
		frappe.sendmail(
			recipients=[leave.member],
			subject=_("Leave Expiring Soon: {0}").format(leave.name),
			message=_("""
				<p>Your approved leave is expiring soon.</p>
				<p><strong>Leave Type:</strong> {leave_type}</p>
				<p><strong>End Date:</strong> {to_date}</p>
				<p><strong>Days Remaining:</strong> {days_remaining}</p>
			""").format(
				leave_type=leave.leave_type,
				to_date=leave.to_date,
				days_remaining=date_diff(leave.to_date, today()),
			),
		)


def update_project_progress():
	"""Daily job: Auto-update project progress from milestones."""
	projects = frappe.get_all(
		"Project",
		filters={"is_active": 1, "status": ["in", ["Active", "Planning"]]},
		pluck="name"
	)
	
	for project_name in projects:
		project = frappe.get_doc("Project", project_name)
		if project.milestones:
			completed = len([m for m in project.milestones if m.status == "Completed"])
			total = len(project.milestones)
			progress = (completed / total) * 100 if total > 0 else 0
			
			if abs(progress - (project.progress or 0)) > 0.5:
				frappe.db.set_value("Project", project_name, "progress", progress)


def send_pending_review_reminders():
	"""Weekly job: Send reminders for pending performance reviews."""
	reviews = frappe.get_all(
		"Performance Review",
		filters={"status": "Draft"},
		fields=["name", "employee", "reviewer", "review_date"],
	)
	
	for review in reviews:
		if review.review_date and review.review_date < today():
			frappe.sendmail(
				recipients=[review.reviewer],
				subject=_("Overdue Performance Review: {0}").format(review.name),
				message=_("""
					<p>You have an overdue performance review to complete.</p>
					<p><strong>Review:</strong> {name}</p>
					<p><strong>Employee:</strong> {employee}</p>
					<p><strong>Due Date:</strong> {review_date}</p>
				""").format(
					name=review.name,
					employee=review.employee,
					review_date=review.review_date,
				),
			)


def generate_monthly_reports():
	"""Monthly job: Generate and send monthly team reports."""
	from frappe.utils import get_first_day, get_last_day
	
	teams = frappe.get_all("Team", filters={"is_active": 1}, pluck="name")
	month_start = get_first_day(add_days(today(), -30))
	month_end = get_last_day(month_start)
	
	for team in teams:
		team_head = _team_head_emails(team)
		if not team_head:
			continue
		
		# Get monthly stats
		members_count = frappe.db.count("Team Member", {"parent": team, "is_active": 1})
		completed_assignments = frappe.db.count(
			"Work Assignment",
			{"team": team, "status": "Completed", "assigned_date": ["between", [month_start, month_end]]}
		)
		hours_logged = frappe.db.sql("""
			SELECT COALESCE(SUM(wl.hours_spent), 0)
			FROM `tabWork Log` wl
			WHERE wl.team = %s
			AND wl.date BETWEEN %s AND %s
		""", [team, month_start, month_end])[0][0] or 0
		
		frappe.sendmail(
			recipients=team_head,
			subject=_("Monthly Team Report: {0} - {month}").format(team, month=month_start.strftime("%B %Y")),
			message=_("""
				<p>Here is your monthly team performance report for <strong>{team}</strong>.</p>
				<h3>{month}</h3>
				<ul>
					<li><strong>Active Members:</strong> {members}</li>
					<li><strong>Completed Assignments:</strong> {completed}</li>
					<li><strong>Hours Logged:</strong> {hours}</li>
				</ul>
			""").format(
				team=team,
				month=month_start.strftime("%B %Y"),
				members=members_count,
				completed=completed_assignments,
				hours=hours_logged,
			),
		)


# ─── Additional Notification Functions ─────────────────────────────────────────

def notify_announcement(doc, method=None):
	"""Notify team members of new announcements."""
	if not doc.is_active:
		return
	
	recipients = []
	if doc.team:
		recipients = _team_member_emails(doc.team)
	else:
		# Company-wide announcement
		recipients = frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name")
	
	if recipients:
		frappe.sendmail(
			recipients=recipients,
			subject=_("New Announcement: {0}").format(doc.title),
			message=_("""
				<p><strong>{title}</strong></p>
				<p>{content}</p>
				<p><strong>Type:</strong> {announcement_type}</p>
				<p><strong>Priority:</strong> {priority}</p>
			""").format(
				title=doc.title,
				content=doc.content or "",
				announcement_type=doc.announcement_type,
				priority=doc.priority,
			),
		)


def notify_review_created(doc, method=None):
	"""Notify employee when a performance review is created."""
	if doc.user and doc.user != frappe.session.user:
		frappe.sendmail(
			recipients=[doc.user],
			subject=_("New Performance Review Created: {0}").format(doc.name),
			message=_("""
				<p>A new performance review has been created for you.</p>
				<p><strong>Review Type:</strong> {review_type}</p>
				<p><strong>Review Period:</strong> {review_period}</p>
				<p><strong>Review Date:</strong> {review_date}</p>
			""").format(
				review_type=doc.review_type,
				review_period=doc.review_period or "N/A",
				review_date=doc.review_date or "N/A",
			),
		)


def notify_project_update(doc, method=None):
	"""Notify team members when project status changes."""
	if not doc.has_value_changed("status"):
		return
	
	members = _team_member_emails(doc.team)
	if doc.owner in members:
		members.remove(doc.owner)
	
	if members:
		old_status = doc.get_doc_before_save().status if doc.get_doc_before_save() else "Unknown"
		frappe.sendmail(
			recipients=members,
			subject=_("Project Status Update: {0}").format(doc.project_name or doc.name),
			message=_("""
				<p>Project status has been updated.</p>
				<p><strong>Project Name:</strong> {project_name}</p>
				<p><strong>Old Status:</strong> {old_status}</p>
				<p><strong>New Status:</strong> {new_status}</p>
			""").format(
				project_name=doc.project_name or doc.name,
				old_status=old_status,
				new_status=doc.status,
			),
		)


def notify_requirement_update(doc, method=None):
	"""Notify relevant parties when a requirement is updated."""
	if not doc.has_value_changed("status"):
		return
	
	old_doc = doc.get_doc_before_save()
	if old_doc and old_doc.status != doc.status:
		team_head = _team_head_emails(doc.team)
		if team_head and frappe.session.user:
			frappe.sendmail(
				recipients=team_head,
				subject=_("Requirement Status Update: {0}").format(doc.title or doc.name),
				message=_("""
					<p>A work requirement status has been updated.</p>
					<p><strong>Title:</strong> {title}</p>
					<p><strong>Old Status:</strong> {old_status}</p>
					<p><strong>New Status:</strong> {new_status}</p>
				""").format(
					title=doc.title or doc.name,
					old_status=old_doc.status,
					new_status=doc.status,
				),
			)
