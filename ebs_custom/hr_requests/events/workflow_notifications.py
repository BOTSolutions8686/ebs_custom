"""In-app and mobile push notifications for HR workflow requests.

Any active Workflow whose DocType belongs to HR, Payroll, or an EBS HR module
notifies the next approver role when the state changes, and notifies the
employee when the request is approved or rejected.

PWA Notification.after_insert sends the phone push through Frappe's relay.
Notification Log is the desk bell.
"""

import frappe
from frappe import _

from ebs_custom.hr_requests.utils.notifications import notify_user_list, notify_users

HR_MODULES = {
	"HR",
	"Payroll",
	"Lending",
	"Ebs Custom",
	"Transfer Requests",
	"Employee Requests",
	"Hr Complaints",
	"Employee Exit",
}

# HRMS already pushes when these status fields change to Approved or Rejected.
PWA_MIXIN_STATUS = {
	"Leave Application": "status",
	"Expense Claim": "approval_status",
	"Shift Request": "status",
}

# Broadcasting to every Employee user is too wide. Notify the requester instead.
DIRECT_ROLES = {"Employee", "All"}

# Status-driven requests that are not always on a Workflow.
STATUS_REQUESTS = {
	"Employee Complaint": {
		"field": "status",
		"roles": {
			"Submitted": ["HR Officer"],
			"Under Review": ["HR Officer"],
		},
		"terminal": {"Resolved"},
	},
	"Employee Data Adjustment Request": {
		"field": "status",
		"roles": {
			"Pending": ["HR Officer", "HR Manager"],
			"In Progress": ["HR Officer", "HR Manager"],
		},
		"terminal": {"Completed"},
	},
}

SKIP_DOCTYPES = {
	"Notification Log",
	"PWA Notification",
	"Error Log",
	"Comment",
	"Version",
	"Activity Log",
	"Access Log",
	"View Log",
	"Route History",
	"Communication",
	"Email Queue",
	"File",
	"ToDo",
	"DocShare",
	"GL Entry",
	"Stock Ledger Entry",
	"Workflow",
	"Workflow Action",
}


def on_update(doc, method=None):
	if _should_skip(doc):
		return

	workflow = _get_workflow(doc.doctype)
	if workflow:
		_handle_workflow(doc, workflow, method)
		return

	_handle_status_request(doc, method)


def clear_workflow_cache(doc=None, method=None):
	doctype = getattr(doc, "document_type", None)
	if not doctype:
		return
	frappe.cache.delete_value(_workflow_cache_key(doctype))
	frappe.cache.delete_value(_module_cache_key(doctype))


def _should_skip(doc):
	if not getattr(doc, "doctype", None) or not getattr(doc, "name", None):
		return True
	if doc.doctype in SKIP_DOCTYPES:
		return True
	if frappe.flags.in_migrate or frappe.flags.in_install or frappe.flags.in_patch:
		return True
	if frappe.flags.in_import:
		return True
	return False


def _handle_workflow(doc, workflow, method):
	state_field = workflow.get("state_field") or "workflow_state"
	current = doc.get(state_field)
	if not current or _is_draft(current):
		return

	previous = _previous_value(doc, state_field, method)
	if previous == current:
		return

	employee_label = doc.get("employee_name") or doc.get("employee") or doc.name
	kind = _classify_state(current)

	if kind in ("approved", "rejected"):
		if _mixin_already_notifies(doc):
			return

		verb = "approved" if kind == "approved" else "rejected"
		subject = _("{0} {1}: {2}").format(doc.doctype, verb.title(), doc.name)
		message = _("{0} for {1} has been {2}.").format(doc.doctype, employee_label, verb)
		notify_user_list(doc, _requester_users(doc), subject, message)

		allow_edit = (workflow.get("states") or {}).get(current)
		if allow_edit and allow_edit not in DIRECT_ROLES:
			notify_users(
				doc,
				[allow_edit],
				subject,
				_("{0} {1} is now {2}.").format(doc.doctype, doc.name, current),
			)
		return

	_notify_actors(
		doc,
		(workflow.get("actors") or {}).get(current) or [],
		employee_label,
		current,
	)


def _handle_status_request(doc, method):
	config = STATUS_REQUESTS.get(doc.doctype)
	if not config:
		return

	# Complaint creation already sends its own detailed notice.
	if method == "after_insert" and doc.doctype == "Employee Complaint":
		return

	fieldname = config["field"]
	current = doc.get(fieldname)
	if not current:
		return

	previous = _previous_value(doc, fieldname, method)
	if previous == current:
		return

	employee_label = doc.get("employee_name") or doc.get("employee") or doc.name

	if current in config.get("terminal", set()):
		subject = _("{0} updated: {1}").format(doc.doctype, doc.name)
		message = _("{0} for {1} is now {2}.").format(doc.doctype, employee_label, current)
		notify_user_list(doc, _requester_users(doc), subject, message)
		return

	_notify_actors(
		doc,
		(config.get("roles") or {}).get(current) or [],
		employee_label,
		current,
	)


def _previous_value(doc, fieldname, method):
	if method == "after_insert":
		return None
	before = doc.get_doc_before_save()
	if not before:
		return None
	return before.get(fieldname)


def _requester_users(doc):
	users = []
	employee = doc.get("employee")
	if employee:
		user_id = frappe.db.get_value("Employee", employee, "user_id")
		if user_id:
			users.append(user_id)

	owner = doc.get("owner")
	if owner and owner not in users:
		users.append(owner)
	return users


def _notify_actors(doc, roles, employee_label, stage):
	broadcast = [role for role in roles if role not in DIRECT_ROLES]
	direct = _requester_users(doc) if any(role in DIRECT_ROLES for role in roles) else []
	if not broadcast and not direct:
		return

	subject = _("Action required: {0} {1}").format(doc.doctype, doc.name)
	message = _("{0} for {1} is waiting for approval. Stage: {2}.").format(
		doc.doctype, employee_label, stage
	)
	if broadcast:
		notify_users(doc, broadcast, subject, message)
	if direct:
		notify_user_list(doc, direct, subject, message)


def _mixin_already_notifies(doc):
	"""Skip a second push when HRMS itself notifies this approval."""
	fieldname = PWA_MIXIN_STATUS.get(doc.doctype)
	if not fieldname:
		return False

	current = doc.get(fieldname)
	if current not in ("Approved", "Rejected"):
		return False

	before = doc.get_doc_before_save()
	previous = before.get(fieldname) if before else None
	return previous != current


def _is_draft(state):
	return (state or "").strip().lower() == "draft"


def _classify_state(state):
	text = (state or "").strip().lower()
	if "reject" in text or "cancel" in text:
		return "rejected"
	if text.startswith("approv") or "approved" in text:
		return "approved"
	return "pending"


def _get_workflow(doctype):
	if not _is_hr_doctype(doctype):
		return None

	key = _workflow_cache_key(doctype)
	cached = frappe.cache.get_value(key)
	if cached is None:
		cached = _load_workflow(doctype)
		frappe.cache.set_value(key, cached, expires_in_sec=300)
	return cached or None


def _load_workflow(doctype):
	name = frappe.db.get_value("Workflow", {"document_type": doctype, "is_active": 1}, "name")
	if not name:
		return {}

	workflow = frappe.get_doc("Workflow", name)
	actors = {}
	for row in workflow.transitions:
		if not row.allowed or row.allowed == "All":
			continue
		roles = actors.setdefault(row.state, [])
		if row.allowed not in roles:
			roles.append(row.allowed)

	return {
		"state_field": workflow.workflow_state_field or "workflow_state",
		"states": {row.state: row.allow_edit for row in workflow.states},
		"actors": actors,
	}


def _is_hr_doctype(doctype):
	if doctype in STATUS_REQUESTS:
		return True

	key = _module_cache_key(doctype)
	module = frappe.cache.get_value(key)
	if module is None:
		module = frappe.db.get_value("DocType", doctype, "module") or ""
		frappe.cache.set_value(key, module, expires_in_sec=300)
	return module in HR_MODULES


def _workflow_cache_key(doctype):
	return f"ebs_hr_wf:{doctype}"


def _module_cache_key(doctype):
	return f"ebs_hr_mod:{doctype}"
