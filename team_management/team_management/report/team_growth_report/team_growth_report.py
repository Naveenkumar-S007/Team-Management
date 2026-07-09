# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, today, add_to_date, get_first_day, get_last_day


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	
	return columns, data


def get_columns():
	return [
		{"label": "Team", "fieldname": "team", "fieldtype": "Link", "options": "Team", "width": 150},
		{"label": "Team Head", "fieldname": "team_head", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": "Current Members", "fieldname": "current_members", "fieldtype": "Int", "width": 120},
		{"label": "New Members (Month)", "fieldname": "new_members", "fieldtype": "Int", "width": 130},
		{"label": "Left Members (Month)", "fieldname": "left_members", "fieldtype": "Int", "width": 140},
		{"label": "Active Projects", "fieldname": "active_projects", "fieldtype": "Int", "width": 120},
		{"label": "Completed Projects", "fieldname": "completed_projects", "fieldtype": "Int", "width": 130},
		{"label": "Growth Rate (%)", "fieldname": "growth_rate", "fieldtype": "Percent", "width": 100},
	]


def get_data(filters):
	data = []
	
	# Get current month date range
	month_start = get_first_day(today())
	month_end = get_last_day(today())
	
	# Get all teams
	team_filter = {"is_active": 1}
	if filters.get("team"):
		team_filter["name"] = filters["team"]
	
	teams = frappe.get_all(
		"Team",
		filters=team_filter,
		fields=["name", "team_head", "creation"]
	)
	
	for team in teams:
		# Get current active members
		current_members = frappe.db.count(
			"Team Member",
			{"parent": team.name, "is_active": 1}
		)
		
		# Get new members this month
		new_members = frappe.db.count(
			"Team Member",
			{
				"parent": team.name,
				"joined_on": ["between", [month_start, month_end]]
			}
		)
		
		# Get members who left this month (deactivated)
		# For simplicity, we'll check if there are inactive members with recent deactivation
		# This would need a deactivation_date field, but for now we'll skip
		left_members = 0
		
		# Get active projects
		active_projects = frappe.db.count(
			"Project",
			{"team": team.name, "status": "Active"}
		)
		
		# Get completed projects this month
		completed_projects = frappe.db.count(
			"Project",
			{
				"team": team.name,
				"status": "Completed",
				"completion_date": ["between", [month_start, month_end]]
			}
		)
		
		# Calculate growth rate
		# (new_members - left_members) / current_members * 100
		if current_members > 0:
			growth_rate = ((new_members - left_members) / current_members) * 100
		else:
			growth_rate = 0
		
		data.append({
			"team": team.name,
			"team_head": team.team_head,
			"current_members": current_members,
			"new_members": new_members,
			"left_members": left_members,
			"active_projects": active_projects,
			"completed_projects": completed_projects,
			"growth_rate": round(growth_rate, 2),
		})
	
	return data
