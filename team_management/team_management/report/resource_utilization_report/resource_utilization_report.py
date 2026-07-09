# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, today, date_diff


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	
	return columns, data


def get_columns():
	return [
		{"label": "Team", "fieldname": "team", "fieldtype": "Link", "options": "Team", "width": 150},
		{"label": "Member", "fieldname": "member", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": "Designation", "fieldname": "designation", "fieldtype": "Data", "width": 120},
		{"label": "Capacity (hrs)", "fieldname": "capacity_hours", "fieldtype": "Float", "width": 100},
		{"label": "Allocated (hrs)", "fieldname": "allocated_hours", "fieldtype": "Float", "width": 100},
		{"label": "Logged (hrs)", "fieldname": "logged_hours", "fieldtype": "Float", "width": 100},
		{"label": "Utilization (%)", "fieldname": "utilization", "fieldtype": "Percent", "width": 100},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
	]


def get_data(filters):
	data = []
	
	# Get all active team members
	member_filter = {"is_active": 1}
	if filters.get("team"):
		member_filter["parent"] = filters["team"]
	
	members = frappe.get_all(
		"Team Member",
		filters=member_filter,
		fields=["parent", "user", "designation", "capacity_hours", "joined_on"]
	)
	
	for member in members:
		# Get logged hours for current month
		logged_hours = frappe.db.sql("""
			SELECT COALESCE(SUM(wl.hours_spent), 0)
			FROM `tabWork Log` wl
			WHERE wl.member = %s
			AND MONTH(wl.date) = MONTH(CURDATE())
			AND YEAR(wl.date) = YEAR(CURDATE())
		""", [member.user])[0][0] or 0
		
		# Get allocated hours
		allocated_hours = frappe.db.sql("""
			SELECT COALESCE(SUM(wa.estimated_hours), 0)
			FROM `tabWork Assignment` wa
			WHERE wa.assigned_to = %s
			AND wa.status IN ('Assigned', 'In Progress')
		""", [member.user])[0][0] or 0
		
		capacity = member.capacity_hours or 160
		utilization = (logged_hours / capacity * 100) if capacity > 0 else 0
		
		# Determine status
		if utilization >= 100:
			status = "Overloaded"
		elif utilization >= 80:
			status = "Optimal"
		elif utilization >= 50:
			status = "Moderate"
		else:
			status = "Underutilized"
		
		data.append({
			"team": member.parent,
			"member": member.user,
			"designation": member.designation or "",
			"capacity_hours": capacity,
			"allocated_hours": allocated_hours,
			"logged_hours": logged_hours,
			"utilization": utilization,
			"status": status,
		})
	
	return data
