import frappe

HR_ROLES = [
	"Branch Manager",
	"Division Manager",
	"Operations Manager",
	"COO",
	"HR Manager",
	"CFO",
	"CEO",
	"HR Officer",
	"Accounts Officer",
]

WORKFLOW_STATES = [
	"Draft",
	"Pending Operations Manager",
	"Pending COO",
	"Pending HR Manager",
	"Pending CFO",
	"Pending CEO",
	"Approved",
	"Rejected",
]

WORKFLOW_ACTIONS = [
	"Submit",
	"Approve",
	"Reject",
]

# Role that must act when document is IN this workflow state
STATE_APPROVER_ROLE = {
	"Pending Operations Manager": "Operations Manager",
	"Pending COO": "COO",
	"Pending HR Manager": "HR Manager",
	"Pending CFO": "CFO",
	"Pending CEO": "CEO",
}


def ensure_role(role_name):
	if frappe.db.exists("Role", role_name):
		return
	frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)


def ensure_hr_roles():
	for role in HR_ROLES:
		ensure_role(role)


def ensure_workflow_state(state_name):
	if frappe.db.exists("Workflow State", state_name):
		return
	frappe.get_doc(
		{"doctype": "Workflow State", "workflow_state_name": state_name}
	).insert(ignore_permissions=True)


def ensure_workflow_action(action_name):
	if frappe.db.exists("Workflow Action Master", action_name):
		return
	frappe.get_doc(
		{"doctype": "Workflow Action Master", "workflow_action_name": action_name}
	).insert(ignore_permissions=True)


def ensure_workflow_prerequisites():
	ensure_hr_roles()
	for state in WORKFLOW_STATES:
		ensure_workflow_state(state)
	for action in WORKFLOW_ACTIONS:
		ensure_workflow_action(action)


def get_hr_approval_workflow_definition(document_type, workflow_name):
	return {
		"doctype": "Workflow",
		"workflow_name": workflow_name,
		"document_type": document_type,
		"is_active": 1,
		"override_status": 0,
		"send_email_alert": 1,
		"workflow_state_field": "workflow_state",
		"states": [
			{"state": "Draft", "doc_status": "0", "allow_edit": "All"},
			{
				"state": "Pending Operations Manager",
				"doc_status": "0",
				"allow_edit": "Operations Manager",
			},
			{"state": "Pending COO", "doc_status": "0", "allow_edit": "COO"},
			{"state": "Pending HR Manager", "doc_status": "0", "allow_edit": "HR Manager"},
			{"state": "Pending CFO", "doc_status": "0", "allow_edit": "CFO"},
			{"state": "Pending CEO", "doc_status": "0", "allow_edit": "CEO"},
			{"state": "Approved", "doc_status": "1", "allow_edit": "All"},
			{"state": "Rejected", "doc_status": "0", "allow_edit": "Branch Manager"},
		],
		"transitions": [
			{
				"state": "Draft",
				"action": "Submit",
				"next_state": "Pending Operations Manager",
				"allowed": "Branch Manager",
				"allow_self_approval": 1,
			},
			{
				"state": "Draft",
				"action": "Submit",
				"next_state": "Pending Operations Manager",
				"allowed": "Division Manager",
				"allow_self_approval": 1,
			},
			{
				"state": "Pending Operations Manager",
				"action": "Approve",
				"next_state": "Pending COO",
				"allowed": "Operations Manager",
				"allow_self_approval": 0,
			},
			{
				"state": "Pending COO",
				"action": "Approve",
				"next_state": "Pending HR Manager",
				"allowed": "COO",
				"allow_self_approval": 0,
			},
			{
				"state": "Pending HR Manager",
				"action": "Approve",
				"next_state": "Pending CFO",
				"allowed": "HR Manager",
				"allow_self_approval": 0,
			},
			{
				"state": "Pending CFO",
				"action": "Approve",
				"next_state": "Pending CEO",
				"allowed": "CFO",
				"allow_self_approval": 0,
			},
			{
				"state": "Pending CEO",
				"action": "Approve",
				"next_state": "Approved",
				"allowed": "CEO",
				"allow_self_approval": 0,
			},
			{
				"state": "Pending Operations Manager",
				"action": "Reject",
				"next_state": "Rejected",
				"allowed": "Operations Manager",
				"allow_self_approval": 0,
			},
			{
				"state": "Pending COO",
				"action": "Reject",
				"next_state": "Rejected",
				"allowed": "COO",
				"allow_self_approval": 0,
			},
			{
				"state": "Pending HR Manager",
				"action": "Reject",
				"next_state": "Rejected",
				"allowed": "HR Manager",
				"allow_self_approval": 0,
			},
			{
				"state": "Pending CFO",
				"action": "Reject",
				"next_state": "Rejected",
				"allowed": "CFO",
				"allow_self_approval": 0,
			},
			{
				"state": "Pending CEO",
				"action": "Reject",
				"next_state": "Rejected",
				"allowed": "CEO",
				"allow_self_approval": 0,
			},
		],
	}


def create_workflow_if_missing(document_type, workflow_name):
	if frappe.db.exists("Workflow", workflow_name):
		return
	if not frappe.db.exists("DocType", document_type):
		return

	ensure_workflow_prerequisites()
	workflow = frappe.get_doc(get_hr_approval_workflow_definition(document_type, workflow_name))
	workflow.insert(ignore_permissions=True)
