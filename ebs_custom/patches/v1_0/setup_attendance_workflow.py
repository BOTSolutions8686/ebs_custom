import frappe

WORKFLOW_NAME = "Branch Attendance Approval Workflow"
DOCUMENT_TYPE = "Branch Attendance Approval"

WORKFLOW_STATES = [
	"Draft",
	"Pending Approval",
	"Approved",
	"Rejected",
]

WORKFLOW_ACTIONS = [
	"Submit for Approval",
	"Approve",
	"Reject",
	"Reset to Draft",
]


def ensure_workflow_state(state_name):
	if frappe.db.exists("Workflow State", state_name):
		return

	frappe.get_doc(
		{
			"doctype": "Workflow State",
			"workflow_state_name": state_name,
		}
	).insert(ignore_permissions=True)


def ensure_workflow_action(action_name):
	"""Workflow Transition.action links to Workflow Action Master in Frappe v16."""
	if frappe.db.exists("Workflow Action Master", action_name):
		return

	frappe.get_doc(
		{
			"doctype": "Workflow Action Master",
			"workflow_action_name": action_name,
		}
	).insert(ignore_permissions=True)


def ensure_branch_manager_role():
	if frappe.db.exists("Role", "Branch Manager"):
		return

	frappe.get_doc({"doctype": "Role", "role_name": "Branch Manager"}).insert(
		ignore_permissions=True
	)


def execute():
	if not frappe.db.exists("DocType", DOCUMENT_TYPE):
		return

	if frappe.db.exists("Workflow", WORKFLOW_NAME):
		return

	ensure_branch_manager_role()

	for state in WORKFLOW_STATES:
		ensure_workflow_state(state)

	for action in WORKFLOW_ACTIONS:
		ensure_workflow_action(action)

	workflow = frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": WORKFLOW_NAME,
			"document_type": DOCUMENT_TYPE,
			"is_active": 1,
			"override_status": 0,
			"send_email_alert": 1,
			"workflow_state_field": "workflow_state",
			"states": [
				{
					"state": "Draft",
					"doc_status": "0",
					"allow_edit": "Branch Manager",
				},
				{
					"state": "Pending Approval",
					"doc_status": "0",
					"allow_edit": "Branch Manager",
				},
				{
					"state": "Approved",
					"doc_status": "0",
					"allow_edit": "All",
				},
				{
					"state": "Rejected",
					"doc_status": "0",
					"allow_edit": "Branch Manager",
				},
			],
			"transitions": [
				{
					"state": "Draft",
					"action": "Submit for Approval",
					"next_state": "Pending Approval",
					"allowed": "Branch Manager",
					"allow_self_approval": 1,
				},
				{
					"state": "Pending Approval",
					"action": "Approve",
					"next_state": "Approved",
					"allowed": "Branch Manager",
					"allow_self_approval": 1,
				},
				{
					"state": "Pending Approval",
					"action": "Reject",
					"next_state": "Rejected",
					"allowed": "Branch Manager",
					"allow_self_approval": 1,
				},
				{
					"state": "Rejected",
					"action": "Reset to Draft",
					"next_state": "Draft",
					"allowed": "Branch Manager",
					"allow_self_approval": 1,
				},
			],
		}
	)
	workflow.insert(ignore_permissions=True)
	frappe.db.commit()
