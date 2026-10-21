import frappe
from frappe import _
from frappe.utils import get_datetime, getdate

from ebs_custom.attendance.report.branch_attendance_excel import generate_branch_attendance_excel
from ebs_custom.attendance.utils.recipients import get_role_emails


def validate_checkin(doc, method=None):
	"""Hold check-in until branch manager approves attendance for the day."""
	if doc.is_new() and not doc.get("approval_status"):
		doc.approval_status = "Pending"

	if doc.approval_status != "Approved":
		doc.skip_auto_attendance = 1


def on_branch_approval_update(doc, method=None):
	"""On Branch Manager approval: save attendance, Excel report, email."""
	if doc.doctype != "Branch Attendance Approval":
		return

	if doc.get("excel_generated"):
		return

	if doc.workflow_state != "Approved":
		return

	if not doc.employees:
		frappe.throw(_("No employees to approve. Load check-ins first."))

	rows = []
	for row in doc.employees:
		create_or_update_attendance(row, doc.attendance_date, doc.company)
		approve_employee_checkins(row.employee, doc.attendance_date)

		rows.append(
			{
				"employee_name": row.employee_name,
				"employee_id": row.employee_id,
				"check_in_time": row.check_in_time,
				"check_out_time": row.check_out_time,
				"status": row.status,
			}
		)

	file_url = generate_branch_attendance_excel(
		doc.branch,
		doc.attendance_date,
		rows,
		approval_docname=doc.name,
	)

	doc.db_set("report_file", file_url, update_modified=False)
	doc.db_set("excel_generated", 1, update_modified=False)

	send_branch_attendance_report(doc, file_url)


@frappe.whitelist()
def get_branch_manager_defaults():
	"""Return branch/company defaults for the logged-in branch manager (PWA)."""
	return (
		frappe.db.get_value(
			"Employee",
			{"user_id": frappe.session.user, "status": "Active"},
			["custom_branch", "company"],
			as_dict=True,
		)
		or {}
	)


@frappe.whitelist()
def load_branch_checkins(branch, attendance_date):
	"""Load all branch employees with check-in/out and status for the day."""
	attendance_date = getdate(attendance_date)
	employees = frappe.get_all(
		"Employee",
		filters={"custom_branch": branch, "status": "Active"},
		fields=["name", "employee_name", "employee"],
		order_by="employee_name asc",
	)

	if not employees:
		return []

	rows = []
	for emp in employees:
		check_in_time, check_out_time = get_checkin_times(emp.name, attendance_date)
		status = get_attendance_status(emp.name, attendance_date, check_in_time)

		rows.append(
			{
				"employee": emp.name,
				"employee_name": emp.employee_name,
				"employee_id": emp.employee or emp.name,
				"check_in_time": check_in_time,
				"check_out_time": check_out_time,
				"status": status,
			}
		)

	return rows


def get_checkin_times(employee, attendance_date):
	start = get_datetime(f"{attendance_date} 00:00:00")
	end = get_datetime(f"{attendance_date} 23:59:59")

	checkins = frappe.get_all(
		"Employee Checkin",
		filters={"employee": employee, "time": ["between", [start, end]]},
		fields=["time", "log_type"],
		order_by="time asc",
	)

	check_in_time = None
	check_out_time = None

	for row in checkins:
		if row.log_type == "IN" and not check_in_time:
			check_in_time = row.time
		elif row.log_type == "OUT":
			check_out_time = row.time

	return check_in_time, check_out_time


def get_attendance_status(employee, attendance_date, check_in_time):
	if employee_on_approved_leave(employee, attendance_date):
		return "On Leave"
	if check_in_time:
		return "Present"
	return "Absent"


def employee_on_approved_leave(employee, attendance_date):
	return frappe.db.exists(
		"Leave Application",
		{
			"employee": employee,
			"docstatus": 1,
			"status": "Approved",
			"from_date": ["<=", attendance_date],
			"to_date": [">=", attendance_date],
		},
	)


def create_or_update_attendance(row, attendance_date, company=None):
	status_map = {
		"Present": "Present",
		"Absent": "Absent",
		"On Leave": "On Leave",
	}
	status = status_map.get(row.status, "Absent")
	attendance_date = getdate(attendance_date)

	if not company:
		company = frappe.db.get_value("Employee", row.employee, "company")

	existing = frappe.db.exists(
		"Attendance",
		{"employee": row.employee, "attendance_date": attendance_date},
	)

	if existing:
		att = frappe.get_doc("Attendance", existing)
		if att.docstatus == 1:
			frappe.db.set_value("Attendance", existing, "status", status)
			return
		att.status = status
		att.save(ignore_permissions=True)
		if att.docstatus == 0:
			att.submit()
		return

	att = frappe.get_doc(
		{
			"doctype": "Attendance",
			"employee": row.employee,
			"attendance_date": attendance_date,
			"status": status,
			"company": company,
		}
	)
	att.insert(ignore_permissions=True)
	att.submit()


def approve_employee_checkins(employee, attendance_date):
	start = get_datetime(f"{attendance_date} 00:00:00")
	end = get_datetime(f"{attendance_date} 23:59:59")

	checkins = frappe.get_all(
		"Employee Checkin",
		filters={"employee": employee, "time": ["between", [start, end]]},
		pluck="name",
	)

	for name in checkins:
		frappe.db.set_value(
			"Employee Checkin",
			name,
			{"approval_status": "Approved", "skip_auto_attendance": 0},
			update_modified=False,
		)


def send_branch_attendance_report(doc, file_url):
	recipients = get_role_emails()
	if not recipients:
		frappe.log_error(
			title="Branch Attendance Report Email",
			message=_("No users found for roles: HR Officer, HR Manager, Operations Manager, COO"),
		)
		return

	subject = _("Branch Attendance Report - {0} - {1}").format(doc.branch, doc.attendance_date)
	message = _(
		"""
		<p>Branch attendance for <b>{branch}</b> on <b>{date}</b> has been approved by the Branch Manager.</p>
		<p>Please find the color-coded Excel report attached.</p>
		<p>Document: {docname}</p>
		"""
	).format(branch=doc.branch, date=doc.attendance_date, docname=doc.name)

	try:
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message,
			attachments=[{"file_url": file_url}],
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)
	except Exception:
		frappe.log_error(title="Branch Attendance Report Email Failed")
