import frappe
from frappe import _

def after_install():
	"""Run after the app is installed on a site."""
	create_team_dashboard_page()
	create_roles_if_not_exist()
	frappe.db.commit()

	print("✅ Team Management: Post-install setup complete!")

def after_app_installed(app_name):
	"""Run after any app is installed (checks if it's our app)."""
	if app_name == "team_management":
		after_install()


def create_team_dashboard_page():
	"""Create the Team Dashboard page in the database."""
	if frappe.db.exists("Page", "team-dashboard"):
		print("✅ Team Dashboard page already exists.")
		return

	try:
		page = frappe.get_doc({
			"doctype": "Page",
			"page_name": "team-dashboard",
			"title": "Team Dashboard",
			"module": "Team Management",
			"icon": "dashboard",
			"standard": "Yes",
			"system_page": 0,
		})
		page.insert(ignore_permissions=True, ignore_if_duplicate=True)
		print("✅ Team Dashboard page created successfully!")
	except Exception as e:
		print(f"⚠️ Could not create Team Dashboard page: {e}")


def create_roles_if_not_exist():
	"""Create required roles if they don't exist."""
	roles = ["Team Head", "Team Member", "Functional Team"]
	for role_name in roles:
		if not frappe.db.exists("Role", role_name):
			role = frappe.get_doc({
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
			})
			role.insert(ignore_permissions=True)
			print(f"✅ Created Role: {role_name}")
