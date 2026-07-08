// Team Management - Doctype-specific Client Scripts
// These are auto-loaded via doctype_js in hooks.py

// Wait for frappe to be ready
frappe.ready(function() {
	"use strict";
});

// ═══════════════════════════════════════════
//  LEAVE APPLICATION CLIENT SCRIPT
// ═══════════════════════════════════════════
frappe.ui.form.on('Leave Application', {
	refresh: function(frm) {
		// Show leave balance info
		if (frm.doc.member && !frm.is_new()) {
			frappe.team_management.leave_app.show_leave_balance(frm);
		}

		// Show holiday warnings
		if (frm.doc.from_date && frm.doc.to_date) {
			frappe.team_management.leave_app.check_holiday_overlap(frm);
		}

		// Update total days on load
		frappe.team_management.leave_app.calculate_total_days(frm);

		// Add custom approve/reject buttons for Team Head
		if (frm.doc.status === 'Pending Approval' && !frm.is_new()) {
			if (frappe.user_roles.includes('Team Head') || frappe.user_roles.includes('System Manager')) {
				frm.add_custom_button(__('Approve'), function() {
					frappe.team_management.leave_app.approve_leave(frm);
				}, 'actions');
				frm.add_custom_button(__('Reject'), function() {
					frappe.team_management.leave_app.reject_leave(frm);
				}, 'actions');
			}
		}
	},

	before_save: function(frm) {
		frappe.team_management.leave_app.calculate_total_days(frm);
	},

	from_date: function(frm) {
		frappe.team_management.leave_app.calculate_total_days(frm);
		if (frm.doc.to_date) {
			frappe.team_management.leave_app.check_holiday_overlap(frm);
		}
	},

	to_date: function(frm) {
		frappe.team_management.leave_app.calculate_total_days(frm);
		if (frm.doc.from_date) {
			frappe.team_management.leave_app.check_holiday_overlap(frm);
		}
	},

	member: function(frm) {
		if (frm.doc.member) {
			frappe.team_management.leave_app.show_leave_balance(frm);
		}
	},

	team: function(frm) {
		if (frm.doc.team && frm.doc.from_date && frm.doc.to_date) {
			frappe.team_management.leave_app.check_holiday_overlap(frm);
		}
	}
});

frappe.team_management.leave_app = {
	calculate_total_days: function(frm) {
		let from_date = frm.doc.from_date;
		let to_date = frm.doc.to_date;
		if (from_date && to_date) {
			let diff = frappe.datetime.get_diff(to_date, from_date);
			frm.set_value('total_days', diff + 1);
		}
	},

	show_leave_balance: function(frm) {
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Leave Application',
				filters: {
					member: frm.doc.member,
					status: 'Approved',
					docstatus: 1
				},
				fields: ['leave_type', 'total_days'],
				limit_page_length: 100
			},
			callback: function(r) {
				if (r.message) {
					let balance = {};
					r.message.forEach(function(l) {
						if (!balance[l.leave_type]) balance[l.leave_type] = 0;
						balance[l.leave_type] += l.total_days || 1;
					});
					// Render balance in a section
					let html = '<div class="leave-balance-card">';
					html += '<div class="balance-title">' + __('Leaves Taken This Year') + '</div>';
					html += '<div class="balance-grid">';
					Object.keys(balance).forEach(function(type) {
						html += '<div class="balance-item">';
						html += '<div class="count">' + balance[type] + '</div>';
						html += '<div class="label">' + __(type) + '</div>';
						html += '</div>';
					});
					html += '</div></div>';
					if (!frm.fields_dict.leave_balance_html) {
						frm.add_custom_html(html, 'after_form', 'leave_balance_html');
					}
				}
			}
		});
	},

	check_holiday_overlap: function(frm) {
		if (!frm.doc.from_date || !frm.doc.to_date) return;
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Holiday',
				filters: {
					date: ['between', [frm.doc.from_date, frm.doc.to_date]]
				},
				fields: ['name', 'holiday_name', 'date'],
				limit_page_length: 10
			},
			callback: function(r) {
				if (r.message && r.message.length) {
					let msg = __('Note: Your leave overlaps with the following holidays:') + '<br>';
					r.message.forEach(function(h) {
						msg += '• ' + h.holiday_name + ' (' + h.date + ')<br>';
					});
					frappe.show_alert({
						message: msg,
						indicator: 'blue'
					}, 6);
				}
			}
		});
	},

	approve_leave: function(frm) {
		frappe.confirm(
			__('Are you sure you want to approve this leave application?'),
			function() {
				frm.set_value('status', 'Approved');
				frm.set_value('approved_by', frappe.session.user);
				frm.set_value('approval_date', frappe.datetime.get_today());
				frm.save();
				frappe.show_alert({
					message: __('✅ Leave approved successfully'),
					indicator: 'green'
				}, 4);
			}
		);
	},

	reject_leave: function(frm) {
		let d = new frappe.ui.Dialog({
			title: __('Reject Leave'),
			fields: [
				{
					label: __('Rejection Reason'),
					fieldname: 'approval_remarks',
					fieldtype: 'Small Text',
					reqd: 1
				}
			],
			primary_action: function() {
				let data = d.get_values();
				frm.set_value('status', 'Rejected');
				frm.set_value('approved_by', frappe.session.user);
				frm.set_value('approval_date', frappe.datetime.get_today());
				frm.set_value('approval_remarks', data.approval_remarks);
				frm.save();
				d.hide();
				frappe.show_alert({
					message: __('Leave request has been rejected'),
					indicator: 'red'
				}, 4);
			},
			primary_action_label: __('Reject')
		});
		d.show();
	}
};

// ═══════════════════════════════════════════
//  WORK LOG CLIENT SCRIPT
// ═══════════════════════════════════════════
frappe.ui.form.on('Work Log', {
	refresh: function(frm) {
		// Auto-set date to today
		if (frm.is_new() && !frm.doc.date) {
			frm.set_value('date', frappe.datetime.get_today());
		}
		// Auto-set member to current user
		if (frm.is_new() && !frm.doc.member) {
			frm.set_value('member', frappe.session.user);
		}
	},

	work_assignment: function(frm) {
		if (frm.doc.work_assignment) {
			// Auto-fill task description from assignment
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Work Assignment',
					name: frm.doc.work_assignment
				},
				callback: function(r) {
					if (r.message && !frm.doc.task_description) {
						frm.set_value('task_description', r.message.title || r.message.description);
					}
				}
			});
		}
	}
});

// ═══════════════════════════════════════════
//  TEAM UPDATE CLIENT SCRIPT
// ═══════════════════════════════════════════
frappe.ui.form.on('Team Update', {
	refresh: function(frm) {
		if (frm.is_new()) {
			frm.set_value('member', frappe.session.user);
			frm.set_value('date', frappe.datetime.get_today());
		}
	},
	
	validate: function(frm) {
		if (frm.doc.description && frm.doc.description.length > 500) {
			frappe.msgprint(__('Description should be less than 500 characters.'));
			frappe.validated = false;
		}
	}
});

// ═══════════════════════════════════════════
//  WORK ASSIGNMENT CLIENT SCRIPT
// ═══════════════════════════════════════════
frappe.ui.form.on('Work Assignment', {
	refresh: function(frm) {
		// Add a "Mark as Complete" button if In Progress
		if (frm.doc.status === 'In Progress' && !frm.is_new()) {
			frm.add_custom_button(__('Mark Complete'), function() {
				frappe.team_management.work_assignment.complete_assignment(frm);
			}, 'actions');
		}

		// Show progress indicator based on status
		if (frm.doc.status) {
			let pct = 0;
			if (frm.doc.status === 'Assigned') pct = 25;
			else if (frm.doc.status === 'In Progress') pct = 50;
			else if (frm.doc.status === 'Completed') pct = 100;
			if (pct > 0 && !frm.is_new()) {
				let html = '<div class="progress-bar-wrapper">' +
					'<div class="progress-header"><span>' + __('Progress') + '</span><span>' + pct + '%</span></div>' +
					'<div class="progress-track"><div class="progress-fill" style="width:' + pct + '%"></div></div>' +
					'</div>';
				if (!frm.fields_dict.progress_html) {
					frm.add_custom_html(html, 'after_form', 'progress_html');
				}
			}
		}

		// Auto-set default due date if not set
		if (frm.is_new() && !frm.doc.due_date) {
			let default_due = frappe.datetime.add_days(frappe.datetime.get_today(), 7);
			frm.set_value('due_date', default_due);
		}
	},

	status: function(frm) {
		// Refresh to update progress bar
		if (!frm.is_new()) {
			frm.refresh_field('status');
		}
	}
});

frappe.team_management.work_assignment = {
	complete_assignment: function(frm) {
		let d = new frappe.ui.Dialog({
			title: __('Complete Assignment'),
			fields: [
				{
					label: __('Completion Notes'),
					fieldname: 'notes',
					fieldtype: 'Small Text'
				}
			],
			primary_action: function() {
				let data = d.get_values();
				frm.set_value('status', 'Completed');
				if (data.notes) {
					frm.set_value('description', (frm.doc.description || '') + '\n\nCompletion Notes: ' + data.notes);
				}
				frm.save();
				d.hide();
				frappe.show_alert({
					message: __('✅ Assignment marked as completed!'),
					indicator: 'green'
				}, 4);
			},
			primary_action_label: __('Complete')
		});
		d.show();
	}
};

// ═══════════════════════════════════════════
//  TEAM CLIENT SCRIPT
// ═══════════════════════════════════════════
frappe.ui.form.on('Team', {
	refresh: function(frm) {
		// Add button to view team members
		frm.add_custom_button(__('Team Members'), function() {
			frappe.set_route('List', 'Team Member', { 'team': frm.doc.name });
		}, 'view');

		frm.add_custom_button(__('Assignments'), function() {
			frappe.set_route('List', 'Work Assignment', { 'team': frm.doc.name });
		}, 'view');
	}
});

// ═══════════════════════════════════════════
//  PROJECT CLIENT SCRIPT
// ═══════════════════════════════════════════
frappe.ui.form.on('Project', {
	refresh: function(frm) {
		// Add links to requirements and assignments
		if (!frm.is_new()) {
			frm.add_custom_button(__('Requirements'), function() {
				frappe.set_route('List', 'Work Requirement', { 'project': frm.doc.name });
			}, 'view');

			frm.add_custom_button(__('Assignments'), function() {
				frappe.set_route('List', 'Work Assignment', { 'project': frm.doc.name });
			}, 'view');
		}

		// Show progress from milestones
		frappe.team_management.project.update_progress(frm);
	},

	start_date: function(frm) {
		if (!frm.doc.end_date && frm.doc.start_date) {
			// Default: project duration 30 days
			frm.set_value('end_date', frappe.datetime.add_days(frm.doc.start_date, 30));
		}
	}
});

frappe.ui.form.on('Project Milestone', {
	milestones_remove: function(frm, cdt, cdn) {
		frappe.team_management.project.update_progress(frm);
	},

	status: function(frm, cdt, cdn) {
		frappe.team_management.project.update_progress(frm);
	}
});

frappe.team_management.project = {
	update_progress: function(frm) {
		if (!frm.doc.milestones || !frm.doc.milestones.length) return;
		let total = frm.doc.milestones.length;
		let completed = frm.doc.milestones.filter(function(m) {
			return m.status === 'Completed';
		}).length;
		let pct = Math.round((completed / total) * 100);

		// Set project progress
		if (frm.fields_dict.progress) {
			frm.set_value('progress', pct);
		}

		// Auto-update project status based on milestone completion
		if (pct === 100 && frm.doc.status !== 'Completed') {
			frm.set_value('status', 'Completed');
		} else if (pct > 0 && pct < 100 && frm.doc.status === 'Planning') {
			frm.set_value('status', 'In Progress');
		}
	}
};
