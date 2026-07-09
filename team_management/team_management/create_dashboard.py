"""
Create the "Team Work Dashboard" Dashboard record along with all its
Number Cards and Charts for the Team Management app.

Run this via bench console:
    bench --site team.details.local console
    exec(open("apps/team_management/team_management/create_dashboard.py").read())
"""

import frappe

# ─── Number Cards ─────────────────────────────────────────────────────────

NUMBER_CARDS = [
    {
        "name": "Total Tasks Assigned",
        "label": "Total Tasks Assigned",
        "document_type": "Work Assignment",
        "function": "Count",
        "filters_json": "[]",
        "color": "#2E86DE",
        "show_percentage_stats": 1,
        "stats_time_interval": "Weekly",
    },
    {
        "name": "Tasks In Progress",
        "label": "Tasks In Progress",
        "document_type": "Work Assignment",
        "function": "Count",
        "filters_json": '[["Work Assignment","status","=","In Progress"]]',
        "color": "#F39C12",
        "show_percentage_stats": 1,
        "stats_time_interval": "Weekly",
    },
    {
        "name": "Tasks Completed This Month",
        "label": "Tasks Completed (This Month)",
        "document_type": "Work Log",
        "function": "Count",
        "filters_json": '[["Work Log","status","=","Completed"]]',
        "color": "#27AE60",
        "show_percentage_stats": 0,
    },
    {
        "name": "Pending Requirements",
        "label": "Pending Requirements",
        "document_type": "Work Requirement",
        "function": "Count",
        "filters_json": '[["Work Requirement","status","=","Open"]]',
        "color": "#E67E22",
        "show_percentage_stats": 1,
        "stats_time_interval": "Weekly",
    },
    {
        "name": "Overdue Tasks",
        "label": "Overdue Tasks",
        "document_type": "Work Assignment",
        "function": "Count",
        "filters_json": '[["Work Assignment","status","!=","Completed"],["Work Assignment","due_date","<","Today"]]',
        "color": "#C0392B",
        "show_percentage_stats": 0,
    },
    {
        "name": "Leave Applications Pending",
        "label": "Leave Applications Pending",
        "document_type": "Leave Application",
        "function": "Count",
        "filters_json": '[["Leave Application","status","=","Pending Approval"]]',
        "color": "#8E44AD",
        "show_percentage_stats": 0,
    },
    {
        "name": "Leaves Approved This Month",
        "label": "Leaves Approved (This Month)",
        "document_type": "Leave Application",
        "function": "Count",
        "filters_json": '[["Leave Application","status","=","Approved"]]',
        "color": "#1ABC9C",
        "show_percentage_stats": 1,
        "stats_time_interval": "Monthly",
    },
    {
        "name": "Team Updates Today",
        "label": "Team Updates Today",
        "document_type": "Team Update",
        "function": "Count",
        "filters_json": '[["Team Update","date","=","Today"]]',
        "color": "#3498DB",
        "show_percentage_stats": 0,
    },
    {
        "name": "Active Projects",
        "label": "Active Projects",
        "document_type": "Project",
        "function": "Count",
        "filters_json": '[["Project","status","=","Active"]]',
        "color": "#2C3E50",
        "show_percentage_stats": 1,
        "stats_time_interval": "Weekly",
    },
    {
        "name": "Upcoming Holidays",
        "label": "Upcoming Holidays (30 Days)",
        "document_type": "Holiday",
        "function": "Count",
        "filters_json": '[["Holiday","holiday_date",">=","Today"]]',
        "color": "#27AE60",
        "show_percentage_stats": 0,
    },
    {
        "name": "Members Present Today",
        "label": "Members Present Today",
        "document_type": "Work Log",
        "function": "Count",
        "filters_json": '[["Work Log","date","=","Today"]]',
        "color": "#2980B9",
        "show_percentage_stats": 0,
    },
]

# ─── Dashboard Charts ─────────────────────────────────────────────────────

DASHBOARD_CHARTS = [
    {
        "name": "Work Status Breakdown",
        "chart_name": "Work Status Breakdown",
        "chart_type": "Group By",
        "document_type": "Work Assignment",
        "group_by_type": "Count",
        "group_by_based_on": "status",
        "type": "Donut",
        "is_public": 1,
        "timeseries": 0,
        "filters_json": "[]",
    },
    {
        "name": "Member-wise Task Load",
        "chart_name": "Member-wise Task Load",
        "chart_type": "Group By",
        "document_type": "Work Assignment",
        "group_by_type": "Count",
        "group_by_based_on": "assigned_to",
        "type": "Bar",
        "is_public": 1,
        "timeseries": 0,
        "filters_json": "[]",
    },
    {
        "name": "Requirements Trend",
        "chart_name": "Requirements Trend",
        "chart_type": "Count",
        "document_type": "Work Requirement",
        "type": "Line",
        "is_public": 1,
        "timeseries": 1,
        "time_interval": "Monthly",
        "based_on": "creation",
        "timespan": "Last Year",
        "filters_json": "[]",
    },
    {
        "name": "Work Log Completion Rate",
        "chart_name": "Work Log Completion Rate",
        "chart_type": "Group By",
        "document_type": "Work Log",
        "group_by_type": "Count",
        "group_by_based_on": "status",
        "type": "Percentage",
        "is_public": 1,
        "timeseries": 0,
        "filters_json": "[]",
    },
    {
        "name": "Leave Status Breakdown",
        "chart_name": "Leave Status Breakdown",
        "chart_type": "Group By",
        "document_type": "Leave Application",
        "group_by_type": "Count",
        "group_by_based_on": "status",
        "type": "Donut",
        "is_public": 1,
        "timeseries": 0,
        "filters_json": "[]",
    },
    {
        "name": "Leave Trend",
        "chart_name": "Leave Trend",
        "chart_type": "Count",
        "document_type": "Leave Application",
        "type": "Line",
        "is_public": 1,
        "timeseries": 1,
        "time_interval": "Monthly",
        "based_on": "creation",
        "timespan": "Last Year",
        "filters_json": "[]",
    },
    {
        "name": "Team Update Type Breakdown",
        "chart_name": "Team Update Type Breakdown",
        "chart_type": "Group By",
        "document_type": "Team Update",
        "group_by_type": "Count",
        "group_by_based_on": "update_type",
        "type": "Bar",
        "is_public": 1,
        "timeseries": 0,
        "filters_json": "[]",
    },
    {
        "name": "Project Status Overview",
        "chart_name": "Project Status Overview",
        "chart_type": "Group By",
        "document_type": "Project",
        "group_by_type": "Count",
        "group_by_based_on": "status",
        "type": "Donut",
        "is_public": 1,
        "timeseries": 0,
        "filters_json": "[]",
    },
    {
        "name": "Hours Logged Per Member",
        "chart_name": "Hours Logged Per Member",
        "chart_type": "Group By",
        "document_type": "Work Log",
        "group_by_type": "Sum",
        "group_by_based_on": "member",
        "aggregate_function_based_on": "hours_spent",
        "type": "Bar",
        "is_public": 1,
        "timeseries": 0,
        "filters_json": '[["Work Log","date",">=","Last 30 days"]]',
    },
]


def create_number_card(data):
    """Create a Number Card if it doesn't exist."""
    if frappe.db.exists("Number Card", data["name"]):
        print(f"  - Number Card '{data['name']}' already exists, skipping")
        return

    doc = frappe.get_doc({
        "doctype": "Number Card",
        "name": data["name"],
        "label": data["label"],
        "document_type": data["document_type"],
        "function": data["function"],
        "is_public": 1,
        "module": "Team Management",
        "filters_json": data["filters_json"],
        "color": data["color"],
        "show_percentage_stats": data.get("show_percentage_stats", 0),
        "stats_time_interval": data.get("stats_time_interval"),
    })
    doc.insert(ignore_permissions=True)
    print(f"  Created Number Card: {data['name']}")


def create_dashboard_chart(data):
    """Create a Dashboard Chart if it doesn't exist."""
    if frappe.db.exists("Dashboard Chart", data["name"]):
        print(f"  - Dashboard Chart '{data['name']}' already exists, skipping")
        return

    doc_data = {
        "doctype": "Dashboard Chart",
        "name": data["name"],
        "chart_name": data["chart_name"],
        "chart_type": data["chart_type"],
        "document_type": data["document_type"],
        "type": data["type"],
        "is_public": 1,
        "module": "Team Management",
        "timeseries": data["timeseries"],
        "filters_json": data["filters_json"],
    }

    if data["chart_type"] == "Group By":
        doc_data["group_by_type"] = data["group_by_type"]
        doc_data["group_by_based_on"] = data["group_by_based_on"]
        if data.get("aggregate_function_based_on"):
            doc_data["aggregate_function_based_on"] = data["aggregate_function_based_on"]

    if data["timeseries"]:
        doc_data["time_interval"] = data["time_interval"]
        doc_data["based_on"] = data["based_on"]
        doc_data["timespan"] = data["timespan"]

    doc = frappe.get_doc(doc_data)
    doc.insert(ignore_permissions=True)
    print(f"  Created Dashboard Chart: {data['chart_name']}")


def create_dashboard():
    """Create the Team Work Dashboard with linked charts and cards."""
    if frappe.db.exists("Dashboard", "Team Work Dashboard"):
        print("  - Dashboard 'Team Work Dashboard' already exists, skipping")
        return

    cards = []
    for card_data in NUMBER_CARDS:
        cards.append({
            "doctype": "Dashboard Card",
            "card": card_data["name"],
        })

    chart_links = []
    for chart_data in DASHBOARD_CHARTS:
        chart_links.append({
            "doctype": "Dashboard Chart Link",
            "chart": chart_data["name"],
        })

    doc = frappe.get_doc({
        "doctype": "Dashboard",
        "name": "Team Work Dashboard",
        "dashboard_name": "Team Work Dashboard",
        "module": "Team Management",
        "is_default": 0,
        "cards": cards,
        "charts": chart_links,
    })
    doc.insert(ignore_permissions=True)
    print("  Created Dashboard: Team Work Dashboard")


def update_workspace_with_dashboard():
    """Update the Team Management workspace to add the dashboard block."""
    if not frappe.db.exists("Workspace", "Team Management"):
        print("  - Workspace 'Team Management' doesn't exist, skipping")
        return

    ws = frappe.get_doc("Workspace", "Team Management")
    content = frappe.parse_json(ws.content)

    if not isinstance(content, list):
        print("  - Workspace content is not a list, skipping")
        return

    # Check if dashboard block already exists
    has_dash = any(b.get("id") == "dash_9.0" for b in content)
    if has_dash:
        print("  - Dashboard block already in workspace, skipping")
        return

    # Insert after the paragraph (index 1)
    content.insert(2, {
        "id": "dash_9.0",
        "type": "dashboard",
        "data": {
            "dashboard_name": "Team Work Dashboard",
            "col": 12
        }
    })
    ws.content = frappe.as_json(content)
    ws.save(ignore_permissions=True)
    frappe.db.commit()
    print("  Workspace updated with dashboard block")


def run():
    """Main function to create all dashboard records and update workspace."""
    print("=" * 60)
    print("  CREATING TEAM WORK DASHBOARD")
    print("=" * 60)
    print()

    print("Step 1: Creating Number Cards...")
    for card in NUMBER_CARDS:
        create_number_card(card)
    frappe.db.commit()

    print()
    print("Step 2: Creating Dashboard Charts...")
    for chart in DASHBOARD_CHARTS:
        create_dashboard_chart(chart)
    frappe.db.commit()

    print()
    print("Step 3: Creating Dashboard...")
    create_dashboard()
    frappe.db.commit()

    print()
    print("Step 4: Updating workspace with dashboard block...")
    update_workspace_with_dashboard()

    print()
    print("=" * 60)
    print("  DASHBOARD CREATION COMPLETE!")
    print("=" * 60)
    print()
    print("Run: bench clear-cache")
    print("Then refresh your browser.")
    print()


# Auto-run
try:
    run()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
