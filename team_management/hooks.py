app_name = "team_management"
app_title = "Team Management"
app_publisher = "Your Organization"
app_description = "Internal Team Work Tracking, Requirement & Assignment Management"
app_email = "admin@yourorg.com"
app_license = "MIT"
app_version = "1.0.0"

# Includes in <head>
# ------------------
app_include_css = "/assets/team_management/css/team_management.bundle.css"
app_include_js = "/assets/team_management/js/team_management.bundle.js"

# Doctype-specific JavaScript
# ----------------------------
doctype_js = {
	"Leave Application": "public/js/team_management.js",
	"Work Log": "public/js/team_management.js",
	"Team Update": "public/js/team_management.js",
	"Work Assignment": "public/js/team_management.js",
	"Team": "public/js/team_management.js",
	"Project": "public/js/team_management.js",
}

# Fixtures - exports Notifications, Workflow, Custom Roles, Print Format with the app
# -------------------------------------------------------------------------------------
fixtures = [
	{"dt": "Role", "filters": [["name", "in", ["Team Head", "Team Member", "Functional Team"]]]},
	{"dt": "Notification", "filters": [["name", "like", "%Team Management%"]]},
	{"dt": "Workflow", "filters": [["document_type", "in", ["Work Requirement", "Leave Application"]]]},
	{"dt": "Workflow State", "filters": [["name", "in", ["Open", "Assigned", "In Progress", "Completed", "Pending Approval", "Approved", "Rejected"]]]},
	{"dt": "Workflow Action Master", "filters": [["name", "in", ["Assign", "Start", "Complete", "Approve", "Reject"]]]},
	{"dt": "Number Card", "filters": [["module", "=", "Team Management"]]},
	{"dt": "Dashboard Chart", "filters": [["module", "=", "Team Management"]]},
	{"dt": "Dashboard", "filters": [["module", "=", "Team Management"]]},
	{"dt": "Workspace", "filters": [["module", "=", "Team Management"]]},
	{"dt": "Print Format", "filters": [["doc_type", "=", "Work Assignment"]]},
	{"dt": "Web Form", "filters": [["doc_type", "=", "Work Requirement"]]},
]

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Work Requirement": {
		"after_insert": "team_management.team_management.utils.notify_team_head_new_requirement",
	},
	"Work Assignment": {
		"after_insert": "team_management.team_management.utils.notify_member_new_assignment",
		"on_update": "team_management.team_management.utils.notify_member_assignment_update",
	},
	"Leave Application": {
		"after_insert": "team_management.team_management.utils.notify_team_head_new_leave",
		"on_update": "team_management.team_management.utils.notify_leave_status_change",
	},
	"Team Update": {
		"after_insert": "team_management.team_management.utils.notify_team_of_update",
	},
	"Project": {
		"after_insert": "team_management.team_management.utils.notify_team_new_project",
	},
}

# Scheduled Tasks
# ---------------
scheduler_events = {
	"daily": [
		"team_management.team_management.utils.send_overdue_task_reminders"
	],
	"weekly": [
		"team_management.team_management.utils.send_weekly_team_summary"
	]
}

# Permission Query Conditions
# ---------------------------
# Restrict list views at the query level based on role (defense in depth,
# in addition to standard Role Permissions + User Permissions set up in Desk)

permission_query_conditions = {
	"Work Log": "team_management.team_management.permissions.work_log_query",
	"Work Assignment": "team_management.team_management.permissions.work_assignment_query",
	"Leave Application": "team_management.team_management.permissions.leave_application_query",
	"Team Update": "team_management.team_management.permissions.team_update_query",
	"Project": "team_management.team_management.permissions.project_query",
	"Holiday": "team_management.team_management.permissions.holiday_query",
}

has_permission = {
	"Work Log": "team_management.team_management.permissions.has_work_log_permission",
	"Work Assignment": "team_management.team_management.permissions.has_work_assignment_permission",
	"Leave Application": "team_management.team_management.permissions.has_leave_application_permission",
	"Team Update": "team_management.team_management.permissions.has_team_update_permission",
	"Project": "team_management.team_management.permissions.has_project_permission",
	"Holiday": "team_management.team_management.permissions.has_holiday_permission",
}
