app_name = "team_management"
app_title = "Team Management"
app_publisher = "Your Organization"
app_description = "Internal Team Work Tracking, Requirement & Assignment Management"
app_email = "admin@yourorg.com"
app_license = "MIT"
app_version = "2.0.0"

# Includes in <head>
app_include_css = "/assets/team_management/css/team_management.bundle.css"
app_include_js = "/assets/team_management/js/team_management.bundle.js"

# Doctype-specific JavaScript
doctype_js = {
	"Leave Application": "public/js/team_management.js",
	"Work Log": "public/js/team_management.js",
	"Team Update": "public/js/team_management.js",
	"Work Assignment": "public/js/team_management.js",
	"Team": "public/js/team_management.js",
	"Project": "public/js/team_management.js",
	"Employee Skill": "public/js/team_management.js",
	"Performance Review": "public/js/team_management.js",
	"Goal Setting": "public/js/team_management.js",
	"Announcement": "public/js/team_management.js",
	"Discussion Thread": "public/js/team_management.js",
	"Resource Allocation": "public/js/team_management.js",
	"KPI": "public/js/team_management.js",
}

# Fixtures
fixtures = [
	{"dt": "Role", "filters": [["name", "in", ["Team Head", "Team Lead", "Team Member", "Functional Team", "Project Manager"]]]},
	{"dt": "Notification", "filters": [["name", "like", "%Team Management%"]]},
	{"dt": "Workflow", "filters": [["document_type", "in", ["Work Requirement", "Leave Application", "Work Assignment", "Project"]]]},
	{"dt": "Workflow State", "filters": [["name", "in", ["Open", "Assigned", "In Progress", "Completed", "Pending Approval", "Approved", "Rejected", "Active", "Planning", "On Hold", "Cancelled"]]]},
	{"dt": "Workflow Action Master", "filters": [["name", "in", ["Assign", "Start", "Complete", "Approve", "Reject", "Submit", "Cancel"]]]},
	{"dt": "Number Card", "filters": [["module", "=", "Team Management"]]},
	{"dt": "Dashboard Chart", "filters": [["module", "=", "Team Management"]]},
	{"dt": "Dashboard", "filters": [["module", "=", "Team Management"]]},
	{"dt": "Workspace", "filters": [["module", "=", "Team Management"]]},
	{"dt": "Print Format", "filters": [["doc_type", "in", ["Work Assignment", "Leave Application", "Performance Review"]]]},
	{"dt": "Web Form", "filters": [["doc_type", "=", "Work Requirement"]]},
]

# Document Events
doc_events = {
	"Work Requirement": {
		"after_insert": "team_management.team_management.utils.notify_team_head_new_requirement",
		"on_update": "team_management.team_management.utils.notify_requirement_update",
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
		"on_update": "team_management.team_management.utils.notify_project_update",
	},
	"Announcement": {
		"after_insert": "team_management.team_management.utils.notify_announcement",
	},
	"Performance Review": {
		"after_insert": "team_management.team_management.utils.notify_review_created",
	},
}

# Scheduled Tasks
scheduler_events = {
	"daily": [
		"team_management.team_management.utils.send_overdue_task_reminders",
		"team_management.team_management.utils.check_leave_expiring",
		"team_management.team_management.utils.update_project_progress",
	],
	"weekly": [
		"team_management.team_management.utils.send_weekly_team_summary",
		"team_management.team_management.utils.send_pending_review_reminders",
	],
	"monthly": [
		"team_management.team_management.utils.generate_monthly_reports",
	],
}

# After Install
after_install = "team_management.team_management.install.after_install"
after_app_install = "team_management.team_management.install.after_app_installed"

# Website / Web View
website_context = {
	"team_management": {
		"title": "Team Management",
		"icon": "task",
		"color": "blue"
	}
}

# Permission Query Conditions
permission_query_conditions = {
	"Work Log": "team_management.team_management.permissions.work_log_query",
	"Work Assignment": "team_management.team_management.permissions.work_assignment_query",
	"Leave Application": "team_management.team_management.permissions.leave_application_query",
	"Team Update": "team_management.team_management.permissions.team_update_query",
	"Project": "team_management.team_management.permissions.project_query",
	"Holiday": "team_management.team_management.permissions.holiday_query",
	"Work Requirement": "team_management.team_management.permissions.work_requirement_query",
	"Employee Skill": "team_management.team_management.permissions.employee_skill_query",
	"Performance Review": "team_management.team_management.permissions.performance_review_query",
	"Announcement": "team_management.team_management.permissions.announcement_query",
	"KPI": "team_management.team_management.permissions.kpi_query",
	"Resource Allocation": "team_management.team_management.permissions.resource_allocation_query",
	"Goal Setting": "team_management.team_management.permissions.goal_setting_query",
	"Discussion Thread": "team_management.team_management.permissions.discussion_thread_query",
}

has_permission = {
	"Work Log": "team_management.team_management.permissions.has_work_log_permission",
	"Work Assignment": "team_management.team_management.permissions.has_work_assignment_permission",
	"Leave Application": "team_management.team_management.permissions.has_leave_application_permission",
	"Team Update": "team_management.team_management.permissions.has_team_update_permission",
	"Project": "team_management.team_management.permissions.has_project_permission",
	"Holiday": "team_management.team_management.permissions.has_holiday_permission",
	"Work Requirement": "team_management.team_management.permissions.has_work_requirement_permission",
	"Employee Skill": "team_management.team_management.permissions.has_employee_skill_permission",
	"Performance Review": "team_management.team_management.permissions.has_performance_review_permission",
	"Announcement": "team_management.team_management.permissions.has_announcement_permission",
	"KPI": "team_management.team_management.permissions.has_kpi_permission",
	"Resource Allocation": "team_management.team_management.permissions.has_resource_allocation_permission",
	"Goal Setting": "team_management.team_management.permissions.has_goal_setting_permission",
	"Discussion Thread": "team_management.team_management.permissions.has_discussion_thread_permission",
}
