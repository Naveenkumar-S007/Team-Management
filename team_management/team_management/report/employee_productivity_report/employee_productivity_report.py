# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, today, add_to_date


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	
	return columns, data


def get_columns():
	return [
		{"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150},
		{"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
		{"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 120},
		{"label": "Team", "fieldname": "team", "fieldtype": "Link", "options": "Team", "width": 120},
		{"label": "Assignments", "fieldname": "total_assignments", "fieldtype": "Int", "width": 100},
		{"label": "Completed", "fieldname": "completed_assignments", "fieldtype": "Int", "width": 100},
		{"label": "Completion Rate (%)", "fieldname": "completion_rate", "fieldtype": "Percent", "width": 120},
		{"label": "Hours Logged", "fieldname": "hours_logged", "fieldtype": "Float", "width": 100},
		{"label": "Avg Hours/Day", "fieldname": "avg_hours_per_day", "fieldtype": "Float", "width": 100},
	]


def get_data(filters):
	data = []
	
	# Default to last 30 days
	end_date = getdate(today())
	start_date = add_to_date(end_date, days=-30)
	
	# Get all active team members
	member_filter = {"is_active": 1}
	if filters.get("team"):
		member_filter["parent"] = filters["team"]
	
	members = frappe.get_all(
		"Team Member",
		filters=member_filter,
		fields=["parent", "user", "designation"]
	)
	
	for member in members:
		# Get employee details
		employee = frappe.get_all(
			"Employee",
			filters={"user_id": member.user},
			fields=["name", "employee_name", "department"]
		)
		
		if not employee:
			continue
		
		emp = employee[0]
		
		# Get assignment counts
		assignments = frappe.get_all(
			"Work Assignment",
			filters={
				"assigned_to": member.user,
				"assigned_date": ["between", [start_date, end_date]]
			},
			fields=["name", "status"]
		)
		
		total_assignments = len(assignments)
		completed_assignments = len([a for a in assignments if a.status == "Completed"])
		completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
		
		# Get hours logged
		hours_logged = frappe.db.sql("""
			SELECT COALESCE(SUM(wl.hours_spent), 0)
			FROM `tabWork Log` wl
			WHERE wl.member = %s
			AND wl.date BETWEEN %s AND %s
		""", [member.user, start_date, end_date])[0][0] or 0
		
		# Calculate avg hours per day (working days)
		working_days = 22  # Approximate working days in 30 days
		avg_hours_per_day = hours_logged / working_days if working_days > 0 else 0
		
		data.append({
			"employee": emp.name,
			"employee_name": emp.employee_name,
			"department": emp.department or "",
			"team": member.parent,
			"total_assignments": total_assignments,
			"completed_assignments": completed_assignments,
			"completion_rate": completion_rate,
			"hours_logged": hours_logged,
			"avg_hours_per_day": round(avg_hours_per_day, 2),
		})
	
	return data
