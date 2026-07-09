# Copyright (c) 2026, Your Organization
# For license information, please see license.txt

"""
Comprehensive cleanup script for Team Management app.

Run this via bench console on your site:
    bench --site team.details.local console
    exec(open("apps/team_management/team_management/team_management/cleanup_site.py").read())
    run()

This will DELETE all doctypes, records, Module Def, Workspace, and fixtures
related to the Team Management app from the site database.

WARNING: This action cannot be undone. All data will be permanently deleted.
"""

import frappe

# ─── All DocTypes to delete (in reverse dependency order) ────────────────

CHILD_DOCTYPES = [
    "Project Milestone",
    "Team Member",
    "Team Capacity",
    "Team Member Item",
    "Assignment Feedback",
    "Resource Allocation",
]

PARENT_DOCTYPES = [
    "Work Log",
    "Work Assignment",
    "Work Requirement",
    "Leave Application",
    "Team Update",
    "Project",
    "Holiday",
    "Team",
    "Employee Skill",
    "Performance Review",
    "Goal Setting",
    "Announcement",
    "Discussion Thread",
    "KPI",
]

ALL_DOCTYPES = CHILD_DOCTYPES + PARENT_DOCTYPES


def delete_table_data(doctype):
    """Delete all records from a doctype table."""
    table = f"tab{doctype}"
    if frappe.db.table_exists(table):
        count = frappe.db.count(doctype)
        frappe.db.sql(f"DELETE FROM `{table}`")
        frappe.db.commit()
        print(f"  ✔ Deleted {count} records from {doctype}")
    else:
        print(f"  - Table {table} does not exist, skipping")


def delete_doctype_definition(doctype):
    """Delete the DocType definition and its table."""
    try:
        if frappe.db.exists("DocType", doctype):
            frappe.delete_doc("DocType", doctype, force=True, ignore_permissions=True)
            frappe.db.commit()
            print(f"  ✔ Deleted DocType: {doctype}")
        else:
            print(f"  - DocType {doctype} not found, skipping")
    except Exception as e:
        print(f"  ✗ Failed to delete DocType {doctype}: {e}")
        # Fallback: drop the table directly
        table = f"tab{doctype}"
        try:
            if frappe.db.table_exists(table):
                frappe.db.sql(f"DROP TABLE IF EXISTS `{table}`")
                frappe.db.commit()
                print(f"  ✔ Dropped table: {table}")
        except Exception as e2:
            print(f"  ✗ Failed to drop table {table}: {e2}")


def cleanup_fixtures():
    """Delete workspace, module def, reports, and other fixtures."""
    # Delete Workspace
    if frappe.db.exists("Workspace", "Team Management"):
        frappe.delete_doc("Workspace", "Team Management", force=True, ignore_permissions=True)
        print("  ✔ Deleted Workspace: Team Management")

    # Delete Module Def
    if frappe.db.exists("Module Def", {"module_name": "Team Management"}):
        module_name = frappe.db.get_value("Module Def", {"module_name": "Team Management"})
        if module_name:
            frappe.delete_doc("Module Def", module_name, force=True, ignore_permissions=True)
            print("  ✔ Deleted Module Def: Team Management")

    # Delete Reports
    for report in ["Attendance Dashboard", "Time Tracking Summary", "Team Performance Summary"]:
        if frappe.db.exists("Report", report):
            frappe.delete_doc("Report", report, force=True, ignore_permissions=True)
            print(f"  ✔ Deleted Report: {report}")

    # Delete custom roles (these are app-specific, safe to remove)
    for role in ["Team Head", "Team Lead", "Team Member", "Functional Team", "Project Manager"]:
        if frappe.db.exists("Role", role):
            frappe.delete_doc("Role", role, force=True, ignore_permissions=True)
            print(f"  ✔ Deleted Role: {role}")

    # Delete Notifications
    notifications = frappe.get_all(
        "Notification", filters={"name": ["like", "%Team Management%"]}, pluck="name"
    )
    for n in notifications:
        frappe.delete_doc("Notification", n, force=True, ignore_permissions=True)
        print(f"  ✔ Deleted Notification: {n}")

    # Delete Workflows
    for wf in [
        "Work Requirement Workflow",
        "Leave Application Workflow",
        "Work Assignment Workflow",
        "Project Workflow",
    ]:
        if frappe.db.exists("Workflow", wf):
            frappe.delete_doc("Workflow", wf, force=True, ignore_permissions=True)
            print(f"  ✔ Deleted Workflow: {wf}")

    # Delete Print Formats
    for pf in ["Work Assignment Print", "Leave Application Print", "Performance Review Print"]:
        if frappe.db.exists("Print Format", pf):
            frappe.delete_doc("Print Format", pf, force=True, ignore_permissions=True)
            print(f"  ✔ Deleted Print Format: {pf}")

    # Delete Web Forms
    web_forms = frappe.get_all("Web Form", filters={"doc_type": "Work Requirement"}, pluck="name")
    for wf in web_forms:
        frappe.delete_doc("Web Form", wf, force=True, ignore_permissions=True)
        print(f"  ✔ Deleted Web Form: {wf}")

    # Delete Dashboard
    if frappe.db.exists("Dashboard", "Team Work Dashboard"):
        frappe.delete_doc("Dashboard", "Team Work Dashboard", force=True, ignore_permissions=True)
        print("  ✔ Deleted Dashboard: Team Work Dashboard")

    # Delete Dashboard Charts
    charts = frappe.get_all("Dashboard Chart", filters={"module": "Team Management"}, pluck="name")
    for c in charts:
        frappe.delete_doc("Dashboard Chart", c, force=True, ignore_permissions=True)
        print(f"  ✔ Deleted Dashboard Chart: {c}")

    # Delete Number Cards
    cards = frappe.get_all("Number Card", filters={"module": "Team Management"}, pluck="name")
    for card in cards:
        frappe.delete_doc("Number Card", card, force=True, ignore_permissions=True)
        print(f"  ✔ Deleted Number Card: {card}")


def run():
    """Main cleanup function. Call this from bench console."""
    print("=" * 60)
    print("  TEAM MANAGEMENT APP - SITE CLEANUP")
    print("=" * 60)
    print()
    print("  This will permanently DELETE all Team Management data")
    print("  from the current site.")
    print()

    print("Step 1: Deleting child table data...")
    for dt in CHILD_DOCTYPES:
        delete_table_data(dt)

    print()
    print("Step 2: Deleting parent table data...")
    for dt in PARENT_DOCTYPES:
        delete_table_data(dt)

    print()
    print("Step 3: Deleting DocType definitions...")
    for dt in ALL_DOCTYPES:
        delete_doctype_definition(dt)

    print()
    print("Step 4: Cleaning up fixtures...")
    cleanup_fixtures()

    print()
    print("Step 5: Deleting team_dashboard page...")
    if frappe.db.exists("Page", "team-dashboard"):
        frappe.delete_doc("Page", "team-dashboard", force=True, ignore_permissions=True)
        print("  ✔ Deleted Page: team-dashboard")

    frappe.db.commit()

    print()
    print("=" * 60)
    print("  CLEANUP COMPLETE")
    print("=" * 60)
    print()
    print("Now run these commands on your server:")
    print("  bench --site team.details.local migrate")
    print("  bench clear-cache")
    print()

# Auto-run when executed
run()
