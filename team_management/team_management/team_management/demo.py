"""Sample data generator for Team Management demo."""
import frappe
from frappe.utils import today, add_days, now_datetime
from random import choice, randint, sample
import os


def generate_demo_data():
	"""Generate comprehensive demo data for the Team Management app."""
	if frappe.flags.in_install:
		return

	if frappe.db.get_single_value("System Settings", "setup_complete"):
		_create_demo_data()
	else:
		pass


def _create_demo_data():
	"""Create demo teams, members, projects, leaves, and work logs."""
	if frappe.db.exists("Team", "Engineering Team"):
		print("✅ Demo data already exists. Skipping...")
		return

	print("🔄 Generating Team Management demo data...")

	# ===== TEAMS =====
	teams_data = [
		{"name": "Engineering Team", "team_name": "Engineering Team", "team_head": "Administrator"},
		{"name": "Design Team", "team_name": "Design Team", "team_head": "Administrator"},
		{"name": "Marketing Team", "team_name": "Marketing Team", "team_head": "Administrator"},
	]

	team_names = []
	for t_data in teams_data:
		team = frappe.get_doc({
			"doctype": "Team",
			**t_data,
			"team_description": f"The {t_data['team_name']} responsible for all related activities."
		})
		team.insert(ignore_permissions=True)
		team_names.append(team.name)
		print(f"  ✅ Created Team: {team.name}")

	# ===== TEAM MEMBERS =====
	member_emails = [
		"john.doe@example.com", "jane.smith@example.com",
		"bob.wilson@example.com", "alice.johnson@example.com",
		"charlie.brown@example.com", "diana.ross@example.com"
	]

	member_names = [
		"John Doe", "Jane Smith",
		"Bob Wilson", "Alice Johnson",
		"Charlie Brown", "Diana Ross"
	]

	created_members = []
	for i, email in enumerate(member_emails):
		if not frappe.db.exists("User", email):
			user = frappe.get_doc({
				"doctype": "User",
				"email": email,
				"first_name": member_names[i].split()[0],
				"last_name": member_names[i].split()[-1],
				"full_name": member_names[i],
				"send_welcome_email": 0,
				"user_type": "System User",
			})
			user.insert(ignore_permissions=True)
			user.add_roles("Team Member")
			print(f"  ✅ Created User: {member_names[i]}")

		created_members.append(email)

	for i, email in enumerate(created_members):
		team = team_names[i % len(team_names)]
		if not frappe.db.exists("Team Member", {"member": email, "team": team}):
			tm = frappe.get_doc({
				"doctype": "Team Member",
				"member": email,
				"team": team,
				"role": choice(["Developer", "Designer", "Tester", "Manager", "Lead"])
			})
			tm.insert(ignore_permissions=True)
			print(f"  ✅ Added {member_names[i]} to {team}")

	# ===== PROJECTS =====
	projects_data = [
		{"project_name": "Mobile App Redesign", "status": "In Progress", "priority": "High",
		 "team": "Design Team", "start_date": add_days(today(), -30), "end_date": add_days(today(), 30)},
		{"project_name": "Customer Portal v2", "status": "In Progress", "priority": "High",
		 "team": "Engineering Team", "start_date": add_days(today(), -20), "end_date": add_days(today(), 40)},
		{"project_name": "Marketing Campaign Q3", "status": "Planning", "priority": "Medium",
		 "team": "Marketing Team", "start_date": today(), "end_date": add_days(today(), 60)},
		{"project_name": "API Integration Module", "status": "Completed", "priority": "High",
		 "team": "Engineering Team", "start_date": add_days(today(), -60), "end_date": add_days(today(), -5)},
		{"project_name": "Brand Guidelines Update", "status": "Planning", "priority": "Low",
		 "team": "Design Team", "start_date": add_days(today(), 5), "end_date": add_days(today(), 35)},
	]

	project_names = []
	for p_data in projects_data:
		project = frappe.get_doc({
			"doctype": "Project",
			"naming_series": "PROJ-.YYYY.-",
			**p_data,
		})
		project.insert(ignore_permissions=True)
		project_names.append(project.name)
		print(f"  ✅ Created Project: {p_data['project_name']}")

	# ===== WORK REQUIREMENTS =====
	req_titles = [
		"Implement user authentication", "Design landing page mockup",
		"Setup CI/CD pipeline", "Write API documentation",
		"Create email templates", "Database optimization",
		"UI component library", "Performance testing",
		"Security audit", "Content strategy plan"
	]

	req_names = []
	for i, title in enumerate(req_titles):
		req = frappe.get_doc({
			"doctype": "Work Requirement",
			"naming_series": "WR-.YYYY.-",
			"title": title,
			"description": f"Requirement: {title}. This needs to be completed as part of the ongoing project.",
			"status": choice(["Open", "Open", "Open", "Assigned", "Completed"]),
			"priority": choice(["High", "Medium", "Low"]),
			"team": choice(team_names),
			"project": choice(project_names) if choice([True, False]) else "",
			"required_by": add_days(today(), randint(5, 45)),
		})
		req.insert(ignore_permissions=True)
		req_names.append(req.name)

	# ===== WORK ASSIGNMENTS =====
	statuses = ["Open", "Assigned", "In Progress", "Completed"]
	for i in range(15):
		member = choice(created_members)
		status = choice(statuses)
		due = add_days(today(), randint(-5, 30))

		assg = frappe.get_doc({
			"doctype": "Work Assignment",
			"naming_series": "WA-.YYYY.-",
			"title": f"Task {i+1}: {choice(req_titles)}",
			"description": f"This assignment is related to ongoing work. Please complete by {due}.",
			"assigned_to": member,
			"assigned_by": "Administrator",
			"team": choice(team_names),
			"status": status,
			"priority": choice(["High", "Medium", "Low"]),
			"due_date": due,
			"project": choice(project_names) if choice([True, False]) else "",
		})
		assg.insert(ignore_permissions=True)

		if status == "Completed":
			feedback = assg.append("feedback", {
				"rating": randint(3, 5),
				"feedback": choice([
					"Great work! Very thorough.",
					"Good job, completed on time.",
					"Excellent quality work.",
					"Needs some improvement in documentation.",
					"Well done! Keep it up."
				]),
				"given_by": "Administrator",
			})
		assg.save(ignore_permissions=True)

	# ===== WORK LOGS =====
	log_descriptions = [
		"Worked on API integration",
		"Completed UI mockups",
		"Fixed database queries",
		"Code review and testing",
		"Documentation updates",
		"Team meeting and planning",
		"Bug fixes and improvements",
		"Client communication",
		"Research and prototyping",
		"Deployment preparation"
	]

	for i in range(30):
		log_date = add_days(today(), -randint(0, 14))
		member = choice(created_members)

		log = frappe.get_doc({
			"doctype": "Work Log",
			"naming_series": "WL-.YYYY.-",
			"member": member,
			"team": choice(team_names),
			"date": log_date,
			"task_description": choice(log_descriptions),
			"hours_spent": randint(2, 9),
			"status": "Completed",
		})
		log.insert(ignore_permissions=True)

	# ===== LEAVE APPLICATIONS =====
	leave_types = ["Sick Leave", "Personal Leave", "Casual Leave", "Annual Leave"]
	for i in range(10):
		member = choice(created_members)
		lt = choice(leave_types)
		from_d = add_days(today(), -randint(0, 30))
		to_d = add_days(from_d, randint(0, 3))
		status = choice(["Pending Approval", "Approved", "Approved", "Approved", "Rejected"])

		leave = frappe.get_doc({
			"doctype": "Leave Application",
			"naming_series": "LA-.YYYY.-",
			"member": member,
			"team": choice(team_names),
			"leave_type": lt,
			"from_date": from_d,
			"to_date": to_d,
			"reason": f"Requesting {lt.lower()} due to personal reasons.",
			"total_days": randint(1, 3),
			"status": status,
		})
		leave.insert(ignore_permissions=True)
		if status != "Pending Approval":
			leave.status = status
			if status == "Approved":
				leave.approved_by = "Administrator"
				leave.approval_date = today()
			leave.db_update()

	# ===== TEAM UPDATES =====
	update_types = ["Late Arrival", "Work From Home", "General Info", "Health Update", "Traffic Delay"]
	update_msgs = [
		"Running 30 minutes late due to traffic",
		"Working from home today",
		"Completed the project milestone!",
		"Not feeling well, taking rest",
		"Will join by 10 AM today",
		"Client meeting pushed to afternoon",
		"Sprint planning completed",
		"Need help with database migration"
	]

	for i in range(15):
		update = frappe.get_doc({
			"doctype": "Team Update",
			"member": choice(created_members),
			"team": choice(team_names),
			"date": add_days(today(), -randint(0, 7)),
			"update_type": choice(update_types),
			"description": choice(update_msgs),
		})
		update.insert(ignore_permissions=True)

	# ===== HOLIDAYS =====
	holidays_data = [
		{"holiday_name": "Independence Day", "date": add_days(today(), randint(5, 30)), "color": "#27AE60"},
		{"holiday_name": "Company Foundation Day", "date": add_days(today(), randint(15, 45)), "color": "#2E86C1"},
		{"holiday_name": "Year-end Holiday", "date": add_days(today(), randint(60, 90)), "color": "#E74C3C"},
		{"holiday_name": "Team Offsite", "date": add_days(today(), randint(20, 50)), "color": "#8E44AD"},
	]

	for h_data in holidays_data:
		if not frappe.db.exists("Holiday", {"holiday_name": h_data["holiday_name"]}):
			holiday = frappe.get_doc({
				"doctype": "Holiday",
				**h_data,
				"is_company_wide": 1,
			})
			holiday.insert(ignore_permissions=True)

	print("\n" + "=" * 50)
	print("✅🎉 DEMO DATA GENERATED SUCCESSFULLY!")
	print("=" * 50)
	print(f"\n  Teams: {len(team_names)}")
	print(f"  Members: {len(created_members)}")
	print(f"  Projects: {len(project_names)}")
	print(f"  Work Requirements: {len(req_names)}")
	print(f"  Work Assignments: 15")
	print(f"  Work Logs: 30")
	print(f"  Leave Applications: 10")
	print(f"  Team Updates: 15")
	print(f"  Holidays: {len(holidays_data)}")
	print("\nLogin with any demo user to explore the features!")
	print("Demo users: john.doe@example.com, jane.smith@example.com, etc.")
	print("=" * 50)
