import frappe

try:
	from hrms.hr.doctype.pwa_notification.pwa_notification import PWANotification as _BasePWANotification
except Exception:
	from frappe.model.document import Document as _BasePWANotification


# Mobile routes. Detail view names follow the HR app: DocType name without spaces + DetailView.
PWA_PATHS = {
	"Leave Application": "/hrms/leave-applications/{name}",
	"Expense Claim": "/hrms/expense-claims/{name}",
	"Employee Advance": "/hrms/employee-advances/{name}",
	"Attendance Request": "/hrms/attendance-requests/{name}",
	"Shift Request": "/hrms/shift-requests/{name}",
	"Shift Assignment": "/hrms/shift-assignments/{name}",
	"Salary Slip": "/hrms/salary-slips/{name}",
	"Salary Adjustment Request": "/hrms/salary-adjustment/{name}",
	"Promotion Request": "/hrms/promotion-request/{name}",
	"Branch Attendance Approval": "/hrms/branch-attendance-approval/{name}",
	"Branch Transfer Request": "/hrms/branch-transfer-request/{name}",
	"Shift Transfer Request": "/hrms/shift-transfer-request/{name}",
	"Salary Statement Request": "/hrms/salary-statement-request/{name}",
	"Resignation Request": "/hrms/resignation-request/{name}",
	"Offboarding Interview": "/hrms/offboarding-interview/{name}",
	"Employee Complaint": "/hrms/employee-complaint/{name}",
	"Employee Data Adjustment Request": "/hrms/employee-data-adjustment/{name}",
}


class CustomPWANotification(_BasePWANotification):
	def get_notification_link(self):
		template = PWA_PATHS.get(self.reference_document_type)
		if template and self.reference_document_name:
			return f"{frappe.utils.get_url()}{template.format(name=self.reference_document_name)}"

		parent = super()
		if hasattr(parent, "get_notification_link"):
			return parent.get_notification_link()
		return f"{frappe.utils.get_url()}/hrms"
