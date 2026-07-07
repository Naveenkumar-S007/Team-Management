# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

"""
Central permission logic for the Team Management app.

Design summary:
- System Manager / Team Head: unrestricted access to all Work Log and
  Work Assignment records.
- Team Member: can READ every Work Log (transparency across the team),
  but can only WRITE/DELETE their own. Work Assignment rows are visible
  in list views to everyone on the team, but a member may only ever
  change the record where they are the assignee.
"""

import frappe


def _is_privileged(user):
	roles = frappe.get_roles(user)
	return "Team Head" in roles or "System Manager" in roles


def work_log_query(user):
	"""Permission Query Condition for Work Log list views."""
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return ""  # no restriction - see everything
	# Team Members see all logs (read-only transparency), so no filter needed for read;
	# write protection is enforced in has_work_log_permission / controller validate().
	return ""


def has_work_log_permission(doc, ptype, user):
	if not user:
		user = frappe.session.user
	if _is_privileged(user):
		return True

	if ptype == "read":
		return True  # everyone on the team can view all work logs

	# write / delete / submit - only the owner (creator) may modify their own entry
	return doc.owner == user


def work_assignment_query(user):
	"""Permission Query Condition for Work Assignment list views.
	Everyone can see all assignments in their team for transparency,
	so no extra SQL filter is applied here; write access is locked down
	in has_work_assignment_permission below."""
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
		return False  # only Team Head can create assignments

	# write - member may only update the status of their own assignment
	return doc.assigned_to == user
