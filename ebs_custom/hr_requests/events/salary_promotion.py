import frappe
from frappe.utils import getdate, today

from ebs_custom.hr_requests.utils.notifications import notify_users, notify_users_by_email
from ebs_custom.hr_requests.utils.workflow_helpers import STATE_APPROVER_ROLE

FINAL_NOTIFY_ROLES = ["HR Officer", "Accounts Officer"]

SALARY_DOCTYPE = "Salary Adjustment Request"
PROMOTION_DOCTYPE = "Promotion Request"


def on_hr_request_update(doc, method=None):
	_handle_workflow_notifications(doc)
	_handle_final_approval(doc)


def _handle_workflow_notifications(doc):
	if doc.is_new():
		return

	previous_state = doc.get_doc_before_save().get("workflow_state") if doc.get_doc_before_save() else None
	current_state = doc.get("workflow_state")

	if not current_state or previous_state == current_state:
		return

	employee_label = doc.get("employee_name") or doc.get("employee")

	if current_state == "Rejected":
		notify_users(
			doc,
			["Branch Manager", "Division Manager"],
			subject=f"{doc.doctype} Rejected - {doc.name}",
			message=f"Request for {employee_label} was rejected at {previous_state}.",
		)
		return

	if current_state in STATE_APPROVER_ROLE:
		role = STATE_APPROVER_ROLE[current_state]
		notify_users(
			doc,
			[role],
			subject=f"Action Required: {doc.doctype} - {doc.name}",
			message=(
				f"A {doc.doctype} for {employee_label} requires your approval. "
				f"Current stage: {current_state}."
			),
		)
		notify_users_by_email(
			doc,
			[role],
			subject=f"Action Required: {doc.doctype} - {doc.name}",
			message=f"Please review {doc.doctype} <b>{doc.name}</b> for {employee_label}.",
		)


def _handle_final_approval(doc):
	if doc.get("workflow_state") != "Approved":
		return

	if doc.get("employee_update_applied"):
		return

	effective_date = getdate(doc.get("effective_date") or today())
	if effective_date > getdate(today()):
		doc.db_set("update_scheduled", 1, update_modified=False)
		_notify_final_roles(doc, scheduled=True)
		return

	_apply_employee_update(doc)
	doc.db_set("employee_update_applied", 1, update_modified=False)
	doc.db_set("update_scheduled", 0, update_modified=False)
	_notify_final_roles(doc, scheduled=False)


def _notify_final_roles(doc, scheduled=False):
	employee_label = doc.get("employee_name") or doc.get("employee")
	status = "scheduled" if scheduled else "applied"
	subject = f"{doc.doctype} Approved - {doc.name}"
	message = (
		f"{doc.doctype} for {employee_label} has been fully approved. "
		f"Employee update has been {status}."
	)
	notify_users(doc, FINAL_NOTIFY_ROLES, subject, message)
	notify_users_by_email(doc, FINAL_NOTIFY_ROLES, subject, message)


def _apply_employee_update(doc):
	if doc.doctype == SALARY_DOCTYPE:
		_apply_salary_adjustment(doc)
	elif doc.doctype == PROMOTION_DOCTYPE:
		_apply_promotion(doc)


def _apply_salary_adjustment(doc):
	updates = {}
	if frappe.get_meta("Employee").has_field("custom_current_salary"):
		updates["custom_current_salary"] = doc.proposed_salary

	if updates:
		frappe.db.set_value("Employee", doc.employee, updates, update_modified=True)


def _apply_promotion(doc):
	updates = {}
	if doc.proposed_designation:
		updates["designation"] = doc.proposed_designation
	if doc.proposed_grade and frappe.get_meta("Employee").has_field("grade"):
		updates["grade"] = doc.proposed_grade
	if doc.proposed_salary_change and frappe.get_meta("Employee").has_field(
		"custom_current_salary"
	):
		updates["custom_current_salary"] = doc.proposed_salary_change

	if updates:
		frappe.db.set_value("Employee", doc.employee, updates, update_modified=True)


def apply_scheduled_hr_updates():
	"""Daily job: apply approved requests with future effective dates."""
	for doctype in (SALARY_DOCTYPE, PROMOTION_DOCTYPE):
		if not frappe.db.exists("DocType", doctype):
			continue

		pending = frappe.get_all(
			doctype,
			filters={
				"workflow_state": "Approved",
				"employee_update_applied": 0,
				"update_scheduled": 1,
				"effective_date": ["<=", today()],
			},
			pluck="name",
		)

		for name in pending:
			doc = frappe.get_doc(doctype, name)
			_apply_employee_update(doc)
			doc.db_set("employee_update_applied", 1, update_modified=False)
			doc.db_set("update_scheduled", 0, update_modified=False)
