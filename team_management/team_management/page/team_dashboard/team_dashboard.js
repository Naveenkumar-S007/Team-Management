frappe.pages['team-dashboard'].on_page_load = function(wrapper) {
	frappe.team_management.dashboard = new frappe.team_management.TeamDashboard(wrapper);
};

frappe.pages['team-dashboard'].on_page_show = function(wrapper) {
	if (frappe.team_management.dashboard) {
		frappe.team_management.dashboard.load_stats();
		frappe.team_management.dashboard.load_activity();
	}
};
