import json

import frappe
from frappe import _
from frappe.utils import getdate

from ebs_custom.hr_requests.events.workflow_notifications import _classify_state, _get_workflow, _is_draft

LANGUAGES = {"en", "ar", "tr"}

MANAGER_ROLES = {"System Manager", "HR Manager", "HR Officer", "Branch Manager"}

ROUTE_NAMES = {
	"Leave Application": "LeaveApplicationDetailView",
	"Expense Claim": "ExpenseClaimDetailView",
	"Employee Advance": "EmployeeAdvanceDetailView",
	"Attendance Request": "AttendanceRequestDetailView",
	"Shift Request": "ShiftRequestDetailView",
	"Salary Adjustment Request": "SalaryAdjustmentRequestDetailView",
	"Promotion Request": "PromotionRequestDetailView",
	"Branch Transfer Request": "BranchTransferRequestDetailView",
	"Shift Transfer Request": "ShiftTransferRequestDetailView",
	"Salary Statement Request": "SalaryStatementRequestDetailView",
	"Resignation Request": "ResignationRequestDetailView",
	"Offboarding Interview": "OffboardingInterviewDetailView",
	"Employee Complaint": "EmployeeComplaintDetailView",
	"Employee Data Adjustment Request": "EmployeeDataAdjustmentRequestDetailView",
}

WORKFLOW_DOCTYPES = [
	"Salary Adjustment Request",
	"Promotion Request",
	"Branch Transfer Request",
	"Shift Transfer Request",
	"Salary Statement Request",
	"Resignation Request",
	"Offboarding Interview",
]

INFO_FIELDS = {
	"Cell Number": "cell_number",
	"Personal Email": "personal_email",
	"Current Address": "current_address",
	"Permanent Address": "permanent_address",
	"Emergency Phone": "emergency_phone_number",
	"Contact Person": "person_to_be_contacted",
	"Bank Account": "bank_ac_no",
	"IBAN": "iban",
}


def _employee_for_user(user=None):
	user = user or frappe.session.user
	return frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")


def _roles():
	return set(frappe.get_roles())


@frappe.whitelist()
def set_my_language(language):
	language = (language or "").strip()
	if language not in LANGUAGES:
		frappe.throw(_("Choose English, Arabic, or Turkish."))

	frappe.db.set_value("User", frappe.session.user, "language", language)
	frappe.db.commit()
	return {"language": language}


@frappe.whitelist()
def get_pending_requests():
	user = frappe.session.user
	employee = _employee_for_user(user)
	seen = set()
	rows = []

	def add(doctype, name, title, status, when, mine):
		key = (doctype, name)
		if not name or key in seen:
			return
		seen.add(key)
		rows.append(
			{
				"doctype": doctype,
				"name": name,
				"title": title or name,
				"status": status or "",
				"date": str(when or ""),
				"route": ROUTE_NAMES.get(doctype),
				"mine": bool(mine),
			}
		)

	if employee:
		_add_own_standard(employee, add)
		_add_own_workflow(employee, add)
		_add_own_status(employee, add)

	_add_approver_standard(user, employee, add)
	_add_role_workflow(employee, add)

	rows.sort(key=lambda row: row["date"], reverse=True)
	return rows[:200]


def _add_own_standard(employee, add):
	for doctype, status_field, pending, title_field, date_field in (
		("Leave Application", "status", ["Open"], "employee_name", "from_date"),
		("Expense Claim", "approval_status", ["Draft"], "employee_name", "posting_date"),
		("Shift Request", "status", ["Draft"], "employee_name", "from_date"),
		("Employee Advance", "status", ["Draft", "Unpaid"], "employee_name", "posting_date"),
	):
		if not frappe.db.exists("DocType", doctype):
			continue
		for row in frappe.get_all(
			doctype,
			filters={"employee": employee, status_field: ["in", pending], "docstatus": ["<", 2]},
			fields=["name", title_field, status_field, date_field],
			limit=100,
			order_by="modified desc",
		):
			add(doctype, row.name, row.get(title_field), row.get(status_field), row.get(date_field), True)

	if frappe.db.exists("DocType", "Attendance Request"):
		for row in frappe.get_all(
			"Attendance Request",
			filters={"employee": employee, "docstatus": 0},
			fields=["name", "employee_name", "from_date"],
			limit=100,
			order_by="modified desc",
		):
			add("Attendance Request", row.name, row.employee_name, "Draft", row.from_date, True)


def _add_own_workflow(employee, add):
	for doctype in WORKFLOW_DOCTYPES:
		for row in _workflow_rows(doctype, {"employee": employee}):
			add(doctype, row.name, row.employee_name, row.workflow_state, row.modified, True)


def _add_own_status(employee, add):
	if frappe.db.exists("DocType", "Employee Complaint"):
		for row in frappe.get_all(
			"Employee Complaint",
			filters={"employee": employee, "status": ["in", ["Submitted", "Under Review"]]},
			fields=["name", "employee_name", "status", "modified"],
			limit=100,
		):
			add("Employee Complaint", row.name, row.employee_name, row.status, row.modified, True)

	if frappe.db.exists("DocType", "Employee Data Adjustment Request"):
		for row in frappe.get_all(
			"Employee Data Adjustment Request",
			filters={"employee": employee, "status": ["in", ["Pending", "In Progress"]], "docstatus": ["<", 2]},
			fields=["name", "employee_name", "status", "modified"],
			limit=100,
		):
			add("Employee Data Adjustment Request", row.name, row.employee_name, row.status, row.modified, True)


def _add_approver_standard(user, employee, add):
	checks = (
		("Leave Application", "leave_approver", "status", ["Open"], "from_date"),
		("Expense Claim", "expense_approver", "approval_status", ["Draft"], "posting_date"),
		("Shift Request", "approver", "status", ["Draft"], "from_date"),
	)
	for doctype, approver_field, status_field, pending, date_field in checks:
		if not frappe.db.exists("DocType", doctype):
			continue
		if not frappe.get_meta(doctype).has_field(approver_field):
			continue
		for row in frappe.get_all(
			doctype,
			filters={approver_field: user, status_field: ["in", pending], "docstatus": ["<", 2]},
			fields=["name", "employee", "employee_name", status_field, date_field],
			limit=100,
			order_by="modified desc",
		):
			add(doctype, row.name, row.employee_name, row.get(status_field), row.get(date_field), row.employee == employee)


def _add_role_workflow(employee, add):
	roles = _roles()
	for doctype in WORKFLOW_DOCTYPES:
		workflow = _get_workflow(doctype)
		if not workflow:
			continue
		actor_states = [state for state, allowed in (workflow.get("actors") or {}).items() if roles.intersection(allowed)]
		if not actor_states:
			continue
		state_field = workflow.get("state_field") or "workflow_state"
		for row in _workflow_rows(doctype, {state_field: ["in", actor_states]}):
			add(doctype, row.name, row.employee_name, row.workflow_state, row.modified, row.employee == employee)


def _workflow_rows(doctype, filters):
	if not frappe.db.exists("DocType", doctype):
		return []
	if not frappe.get_meta(doctype).has_field("workflow_state"):
		return []
	rows = frappe.get_all(
		doctype,
		filters=filters,
		fields=["name", "employee", "employee_name", "workflow_state", "modified"],
		limit=100,
		order_by="modified desc",
	)
	return [row for row in rows if row.workflow_state and not _is_draft(row.workflow_state) and _classify_state(row.workflow_state) == "pending"]


@frappe.whitelist()
def get_information_fields():
	employee = _employee_for_user()
	if not employee:
		frappe.throw(_("No active employee is linked to your user."))

	doc = frappe.get_doc("Employee", employee)
	return [
		{"label": label, "fieldname": fieldname, "current_value": doc.get(fieldname) or ""}
		for label, fieldname in INFO_FIELDS.items()
		if doc.meta.has_field(fieldname)
	]


@frappe.whitelist()
def submit_information_change(field_label, new_value, reason=None):
	if field_label not in INFO_FIELDS:
		frappe.throw(_("Choose a valid field."))

	employee = _employee_for_user()
	if not employee:
		frappe.throw(_("No active employee is linked to your user."))

	new_value = (new_value or "").strip()
	if not new_value:
		frappe.throw(_("Enter the new value."))

	doc = frappe.get_doc("Employee", employee)
	request = frappe.new_doc("Employee Data Adjustment Request")
	request.employee = employee
	request.employee_name = doc.employee_name
	request.request_date = getdate()
	request.status = "Pending"
	request.append(
		"items",
		{
			"field_to_be_updated": field_label,
			"current_value": doc.get(INFO_FIELDS[field_label]) or "",
			"new_value": new_value,
			"reason_for_change": reason or "",
		},
	)
	request.insert(ignore_permissions=True)
	return {"name": request.name}


@frappe.whitelist()
def get_shift_form_data(branch=None):
	_require_shift_manager()
	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active", **({"branch": branch} if branch else {})},
		fields=["name", "employee_name", "branch", "company", "default_shift"],
		order_by="employee_name asc",
		limit=500,
	)
	return {
		"branches": frappe.get_all("Branch", pluck="name", order_by="name asc"),
		"shift_types": frappe.get_all("Shift Type", pluck="name", order_by="name asc"),
		"employees": employees,
	}


@frappe.whitelist()
def assign_shifts(employees, shift_type, start_date, end_date=None):
	_require_shift_manager()
	if isinstance(employees, str):
		employees = json.loads(employees)

	employees = [name for name in (employees or []) if name]
	if not employees:
		frappe.throw(_("Select at least one employee."))
	if not shift_type or not frappe.db.exists("Shift Type", shift_type):
		frappe.throw(_("Select a shift type."))
	if not start_date:
		frappe.throw(_("Select the start date."))

	from hrms.hr.doctype.shift_assignment_tool.shift_assignment_tool import create_shift_assignment

	success = []
	failure = []
	for name in employees:
		company = frappe.db.get_value("Employee", name, "company")
		try:
			assignment = create_shift_assignment(
				name,
				company,
				shift_type,
				start_date,
				end_date or None,
				"Active",
			)
			success.append({"employee": name, "assignment": assignment.name})
			frappe.db.commit()
		except Exception as exc:
			frappe.db.rollback()
			failure.append({"employee": name, "error": str(exc)})

	return {"success": success, "failure": failure}


def _require_shift_manager():
	if not _roles().intersection(MANAGER_ROLES):
		frappe.throw(_("Only a manager can assign shifts for employees."), frappe.PermissionError)


def ensure_information_request_access():
	if not frappe.db.exists("DocType", "Employee Data Adjustment Request"):
		return

	from frappe.permissions import add_permission, update_permission_property

	if frappe.db.exists("Role", "Employee"):
		add_permission("Employee Data Adjustment Request", "Employee", 0)
		for perm in ("read", "write", "create"):
			update_permission_property("Employee Data Adjustment Request", "Employee", 0, perm, 1)
		update_permission_property("Employee Data Adjustment Request", "Employee", 0, "submit", 0)
		update_permission_property("Employee Data Adjustment Request", "Employee", 0, "if_owner", 1)

	for role in ("HR Officer", "HR Manager", "HR User"):
		if not frappe.db.exists("Role", role):
			continue
		add_permission("Employee Data Adjustment Request", role, 0)
		for perm in ("read", "write", "create", "submit", "report"):
			update_permission_property("Employee Data Adjustment Request", role, 0, perm, 1)
