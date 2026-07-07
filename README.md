# Team Management (ERPNext v15 Custom App)

Internal team work-tracking app: requirements, assignments, work logs,
role-based visibility, dashboards, reports, and automatic email notifications.

## What's Included

| Component | Purpose |
|---|---|
| **Team** (doctype) | Master: team name, Team Head, member list. Auto-syncs roles + User Permissions. |
| **Work Requirement** (doctype) | Functional Team raises requirements. Workflow: Open → Assigned → In Progress → Completed. |
| **Work Assignment** (doctype) | Only Team Head can create. Assigns work to a member. |
| **Work Log** (doctype) | Daily work entries. Everyone reads all; each member edits only their own. |
| **Team Performance Summary** (Script Report) | Team Head/Admin see everyone; a Team Member automatically sees only their own row. |
| **Team Work Dashboard** | Number Cards + Charts: task status, workload, trends, completion rate. |
| **Team Management Workspace** | App home screen with shortcuts + embedded dashboard. |
| **Task Sheet** (Print Format) | Clean printable PDF for a Work Assignment. |
| **Raise a Requirement** (Web Form) | Optional no-desk-login form for the Functional Team at `/raise-a-requirement`. |
| **Notifications** | Emails on new requirement, new assignment, and task completion. |
| Scheduled jobs | Daily overdue reminders + weekly digest to each Team Head. |

## Roles

- **Team Head** — full access to their team's requirements, assignments, work logs; the only role that can create a Work Assignment.
- **Team Member** — reads everyone's work logs/assignments (transparency), but can only create/edit their **own** entries.
- **Functional Team** — can raise/view their own requirements only; no visibility into internal work logs.
- **System Manager** — unrestricted (standard Frappe admin role).

## Installation

```bash
# from your frappe-bench directory
bench get-app team_management /path/to/team_management   # or from a git remote
bench --site your-site.local install-app team_management
bench --site your-site.local migrate
bench restart
```

If you unzip this folder directly into `apps/team_management` on your bench server:

```bash
cd ~/frappe-bench
bench get-app team_management apps/team_management --skip-assets
bench --site your-site.local install-app team_management
bench --site your-site.local migrate
bench build --app team_management
bench restart
```

## Post-Install Setup Checklist

1. **Create Teams** — go to *Team* list, add a Team, set the Team Head, add Members.
   This automatically grants the `Team Head` / `Team Member` roles and creates
   the User Permission that scopes each Head to their own team's data.
2. **Create Users** — each member needs a standard Frappe User (unique login/password
   is native to Frappe — no extra doctype needed).
3. **Check Notifications** — *Setup > Notification* — enabled by default, edit
   wording/recipients as needed.
4. **Check Workflow** — *Setup > Workflow > Work Requirement Workflow* — adjust
   transitions/roles if your approval flow differs.
5. **Enable Web Form (optional)** — if the Functional Team doesn't need full Desk
   access, share the link `https://your-site/raise-a-requirement` instead of
   giving them a Desk login.
6. **Scheduler** — ensure `bench` scheduler is enabled (`bench doctor`) so the
   daily overdue reminders and weekly digest emails actually fire.

## Folder Structure

```
team_management/
├── setup.py, requirements.txt, license.txt, MANIFEST.in
└── team_management/
    ├── hooks.py                # app config: doc_events, scheduler, permissions, fixtures
    ├── modules.txt
    └── team_management/        # the "Team Management" module
        ├── doctype/
        │   ├── team/
        │   ├── team_member/          (child table)
        │   ├── work_requirement/
        │   ├── work_assignment/
        │   └── work_log/
        ├── report/
        │   └── team_performance_summary/
        ├── fixtures/            # Roles, Notifications, Workflow, Dashboard, Workspace,
        │                         # Number Cards, Charts, Print Format, Web Form
        ├── permissions.py       # query + doc-level permission hooks
        └── utils.py             # email notification + scheduled job logic
```

## Notes

- All permission logic is layered: standard **Role Permissions** (Desk UI) +
  **User Permissions** (per-Team scoping for Team Heads) + custom Python hooks
  in `permissions.py` and each doctype's `validate()` (defense in depth, so a
  member can never edit someone else's record even via API).
- Everything here is standard Frappe/ERPNext v15 constructs — no external
  dependencies — so it upgrades cleanly with future ERPNext versions.
