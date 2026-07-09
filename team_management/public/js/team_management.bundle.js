// Team Management - Core JS Bundle
// This bundle.js is auto-loaded via hooks.py

frappe.provide('frappe.team_management');

// ─── Team Management Core Utilities ───
frappe.team_management = {
	// API helper for server-side methods
	call: function(method, args, callback) {
		return frappe.call({
			method: 'team_management.team_management.' + method,
			args: args || {},
			callback: callback
		});
	},

	// Show a success alert
	show_success: function(msg) {
		frappe.show_alert({ message: __('✓ ' + msg), indicator: 'green' }, 4);
	},

	// Show an error alert
	show_error: function(msg) {
		frappe.show_alert({ message: __('✗ ' + msg), indicator: 'red' }, 6);
	},

	// Format date to readable string
	format_date: function(date_str) {
		if (!date_str) return '';
		let d = new Date(date_str);
		return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
	},

	// Calculate working days between two dates
	calculate_working_days: function(from_date, to_date) {
		if (!from_date || !to_date) return 0;
		let start = frappe.datetime.str_to_obj(from_date);
		let end = frappe.datetime.str_to_obj(to_date);
		let diff = frappe.datetime.get_diff(end, start);
		return diff + 1;
	},

	// Get time difference in hours
	time_diff_in_hours: function(start_time, end_time) {
		if (!start_time || !end_time) return 0;
		let start = frappe.datetime.str_to_obj(start_time);
		let end = frappe.datetime.str_to_obj(end_time);
		let diff = frappe.datetime.get_diff(end, start, true);
		return Math.round(diff / 3600 * 100) / 100;
	},

	// Open a doctype in new tab
	open_doctype: function(doctype, name) {
		if (name) {
			frappe.set_route('Form', doctype, name);
		} else {
			frappe.set_route('List', doctype);
		}
	},

	// Quick dialog for creating a new record
	quick_new: function(doctype, defaults, callback) {
		frappe.new_doc(doctype, defaults);
	},

	// Status color mapping
	status_colors: {
		'Open': 'orange',
		'Pending': 'orange',
		'Pending Approval': 'orange',
		'In Progress': 'blue',
		'Assigned': 'blue',
		'Completed': 'green',
		'Approved': 'green',
		'Rejected': 'red',
		'Cancelled': 'red',
		'Overdue': 'red'
	},

	// Get status indicator class
	get_status_html: function(status) {
		let color = this.status_colors[status] || 'gray';
		let badge_class = 'status-badge ' + (status || '').toLowerCase().replace(/\s+/g, '-');
		return `<span class="${badge_class}">${__(status)}</span>`;
	}
};

// ─── Custom App Page Setup ───
$(document).ready(function() {
	// Enhance all Team Management list views with custom styling
	setTimeout(function() {
		$('.listview-main-section [data-doctype="Team"], \
		   .listview-main-section [data-doctype="Project"], \
		   .listview-main-section [data-doctype="Work Requirement"], \
		   .listview-main-section [data-doctype="Work Assignment"], \
		   .listview-main-section [data-doctype="Work Log"], \
		   .listview-main-section [data-doctype="Leave Application"], \
		   .listview-main-section [data-doctype="Team Update"], \
		   .listview-main-section [data-doctype="Holiday"]')
			.closest('.page-container')
			.addClass('team-management-page');
	}, 500);
});

frappe.team_management.TeamDashboard = Class.extend({
	init: function(wrapper) {
		this.wrapper = $(wrapper);
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __('Team Dashboard'),
			single_column: true
		});
		this.page_container = this.page.main;
		this.setup();
	},

	setup: function() {
		let me = this;
		this.page_container.html(`
			<div class="team-dashboard-wrapper">
				<div class="greeting-header">
					<h2>${__('Welcome back, {0}!', [frappe.session.user_fullname || frappe.session.user])}</h2>
					<div class="subtitle">${__('Your team management overview at a glance')}</div>
				</div>
				<div id="dashboard-stats" class="stats-cards-row"></div>
				<div id="dashboard-quick-actions" class="quick-actions-section">
					<h3>${__('Quick Actions')}</h3>
					<div class="quick-actions-grid">
						<a class="action-card" onclick="frappe.new_doc('Leave Application')">
							<span class="action-icon">📋</span>
							<div class="action-label">${__('Apply Leave')}</div>
							<div class="action-desc">${__('Submit a leave request')}</div>
						</a>
						<a class="action-card" onclick="frappe.new_doc('Work Log')">
							<span class="action-icon">📝</span>
							<div class="action-label">${__('Log Work')}</div>
							<div class="action-desc">${__('Record today\'s work')}</div>
						</a>
						<a class="action-card" onclick="frappe.new_doc('Team Update')">
							<span class="action-icon">📢</span>
							<div class="action-label">${__('Team Update')}</div>
							<div class="action-desc">${__('Share info with team')}</div>
						</a>
						<a class="action-card" onclick="frappe.new_doc('Work Assignment')">
							<span class="action-icon">🎯</span>
							<div class="action-label">${__('New Assignment')}</div>
							<div class="action-desc">${__('Assign work to member')}</div>
						</a>
						<a class="action-card" onclick="frappe.set_route('List', 'Project')">
							<span class="action-icon">📊</span>
							<div class="action-label">${__('Projects')}</div>
							<div class="action-desc">${__('View all projects')}</div>
						</a>
						<a class="action-card" onclick="frappe.set_route('List', 'Team Update')">
							<span class="action-icon">💬</span>
							<div class="action-label">${__('Team Feed')}</div>
							<div class="action-desc">${__('See team updates')}</div>
						</a>
					</div>
				</div>
				<div id="dashboard-activity" class="recent-activity-section">
					<h3>${__('Recent Activity')}</h3>
					<div class="activity-feed" id="activity-feed">
						<div class="text-muted text-center" style="padding: 20px;">
							${__('Loading recent activity...')}
						</div>
					</div>
				</div>
			</div>
		`);
		this.load_stats();
		this.load_activity();
	},

	load_stats: function() {
		let me = this;
		// Load stats from the server
		frappe.call({
			method: 'team_management.team_management.page.team_dashboard.team_dashboard.get_dashboard_stats',
			args: {},
			callback: function(r) {
				if (r.message) {
					me.render_stats(r.message);
				}
			}
		});
	},

	render_stats: function(stats) {
		let cards = [
			{ label: __('Pending Leaves'), value: stats.pending_leaves || 0, icon: '📋', color: 'orange' },
			{ label: __('Active Projects'), value: stats.active_projects || 0, icon: '📊', color: 'blue' },
			{ label: __('Open Tasks'), value: stats.open_assignments || 0, icon: '🎯', color: 'purple' },
			{ label: __('Logged Today'), value: stats.logged_today || 0, icon: '⏱️', color: 'green' },
			{ label: __('Team Updates'), value: stats.today_updates || 0, icon: '💬', color: 'cyan' },
			{ label: __('Overdue Tasks'), value: stats.overdue_tasks || 0, icon: '⚠️', color: 'red' }
		];

		let html = '';
		cards.forEach(function(card) {
			html += `
				<div class="stat-card ${card.color}">
					<div class="stat-icon">${card.icon}</div>
					<div class="stat-value">${card.value}</div>
					<div class="stat-label">${__(card.label)}</div>
				</div>
			`;
		});
		$('#dashboard-stats').html(html);
	},

	load_activity: function() {
		let me = this;
		frappe.call({
			method: 'team_management.team_management.page.team_dashboard.team_dashboard.get_recent_activity',
			args: {},
			callback: function(r) {
				if (r.message && r.message.length) {
					me.render_activity(r.message);
				} else {
					$('#activity-feed').html(`
						<div class="text-muted text-center" style="padding: 20px;">
							${__('No recent activity to show.')}
						</div>
					`);
				}
			}
		});
	},

	render_activity: function(activities) {
		let me = this;
		let html = '';
		activities.forEach(function(item) {
			let icon_color = item.icon_color || 'gray';
			html += `
				<div class="activity-item" onclick="frappe.set_route('Form', '${item.doctype}', '${item.name}')" style="cursor:pointer;">
					<div class="activity-icon" style="background: var(--${icon_color}-100); color: var(--${icon_color}-600);">
						${item.icon || '📌'}
					</div>
					<div class="activity-content">
						<div class="activity-title">${__(item.title)}</div>
						<div class="activity-desc">${__(item.description)}</div>
					</div>
					<div class="activity-time">${frappe.datetime.pretty_date(item.creation)}</div>
				</div>
			`;
		});
		$('#activity-feed').html(html);
	}
});

// ─── List View Enhancements ───
frappe.listview_settings['Leave Application'] = {
	get_indicator: function(doc) {
		const status_colors = {
			'Pending Approval': 'orange',
			'Approved': 'green',
			'Rejected': 'red'
		};
		return [__(doc.status), status_colors[doc.status] || 'gray', 'status,=,' + doc.status];
	},
	button: {
		show: function(doc) {
			return doc.status === 'Pending Approval';
		},
		get_label: function() {
			return __('Approve / Reject');
		},
		get_description: function() {
			return __('Review this leave application');
		},
		action: function(doc) {
			frappe.set_route('Form', 'Leave Application', doc.name);
		}
	}
};

frappe.listview_settings['Work Assignment'] = {
	get_indicator: function(doc) {
		const status_colors = {
			'Open': 'orange',
			'Assigned': 'blue',
			'In Progress': 'blue',
			'Completed': 'green',
			'Overdue': 'red'
		};
		return [__(doc.status), status_colors[doc.status] || 'gray', 'status,=,' + doc.status];
	}
};

frappe.listview_settings['Team Update'] = {
	get_indicator: function(doc) {
		const type_colors = {
			'Late Arrival': 'red',
			'Early Departure': 'orange',
			'Work From Home': 'green',
			'Traffic Delay': 'purple',
			'Personal Errand': 'blue',
			'General Info': 'cyan',
			'Health Update': 'pink',
			'Other': 'gray'
		};
		return [__(doc.update_type), type_colors[doc.update_type] || 'gray', 'update_type,=,' + doc.update_type];
	}
};

frappe.listview_settings['Project'] = {
	get_indicator: function(doc) {
		const status_colors = {
			'Planning': 'orange',
			'In Progress': 'blue',
			'On Hold': 'gray',
			'Completed': 'green',
			'Cancelled': 'red'
		};
		return [__(doc.status), status_colors[doc.status] || 'gray', 'status,=,' + doc.status];
	}
};

frappe.listview_settings['Holiday'] = {
	get_indicator: function(doc) {
		return [__(doc.holiday_name), doc.color && doc.color.toLowerCase() || 'green', 'date,>,' + frappe.datetime.get_today()];
	}
};
