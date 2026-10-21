# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class EmployeeComplaint(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		date_of_incident: DF.Date
		department: DF.Link | None
		description: DF.LongText
		employee: DF.Link
		employee_id: DF.Data | None
		employee_name: DF.Data | None
		hr_remarks: DF.LongText | None
		incident_type: DF.Literal["", "Harassment", "Misconduct", "Policy Violation", "Other"]
		naming_series: DF.Literal["COMP-.YYYY.-.#####"]
		persons_involved: DF.SmallText
		status: DF.Literal["Submitted", "Under Review", "Resolved"]
		supporting_documents: DF.Attach | None
	# end: auto-generated types

	def before_insert(self):
		"""Auto-fill employee details from the logged-in user if not already set."""
		if not self.employee:
			employee = frappe.db.get_value(
				"Employee", {"user_id": frappe.session.user}, "name"
			)
			if employee:
				self.employee = employee

		if self.employee and not self.employee_id:
			self.employee_id = self.employee

	def validate(self):
		self._validate_employee_ownership()
		self._validate_status_change()

	def _validate_employee_ownership(self):
		"""Employees can only submit complaints for themselves."""
		if frappe.session.user == "Administrator":
			return

		is_hr_officer = frappe.db.exists(
			"Has Role", {"parent": frappe.session.user, "role": "HR Officer"}
		)
		if is_hr_officer:
			return

		linked_employee = frappe.db.get_value(
			"Employee", {"user_id": frappe.session.user}, "name"
		)
		if self.employee and linked_employee and self.employee != linked_employee:
			frappe.throw(_("You can only submit a complaint on behalf of yourself."))

	def _validate_status_change(self):
		"""Only HR Officers can change the Status field."""
		if frappe.session.user == "Administrator":
			return

		is_hr_officer = frappe.db.exists(
			"Has Role", {"parent": frappe.session.user, "role": "HR Officer"}
		)
		if is_hr_officer:
			return

		if self.is_new():
			# Force default status for new records submitted by employees
			self.status = "Submitted"
		else:
			original_status = frappe.db.get_value(
				"Employee Complaint", self.name, "status"
			)
			if original_status and self.status != original_status:
				frappe.throw(_("Only an HR Officer can change the complaint status."))

	def after_insert(self):
		"""Send system notification + email to all HR Officers on new submission."""
		self._notify_hr_officers()

	def _notify_hr_officers(self):
		hr_officer_users = frappe.get_all(
			"Has Role",
			filters={"role": "HR Officer", "parenttype": "User"},
			fields=["parent"],
		)

		recipients = [
			r["parent"]
			for r in hr_officer_users
			if r["parent"] != "Administrator"
		]

		if not recipients:
			frappe.log_error(
				"No HR Officer users found to notify for Employee Complaint: " + self.name,
				"HR Complaint Notification"
			)
			return

		subject = _("New Employee Complaint Submitted: {0}").format(self.name)

		message = """
			<p>A new complaint has been submitted and requires your attention.</p>
			<table style="border-collapse:collapse; width:100%; font-family:sans-serif; font-size:14px;">
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Complaint ID</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{complaint_id}</td>
				</tr>
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Employee</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{employee_name} ({employee})</td>
				</tr>
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Incident Type</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{incident_type}</td>
				</tr>
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Date of Incident</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{date_of_incident}</td>
				</tr>
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Status</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{status}</td>
				</tr>
			</table>
			<p style="margin-top:20px;">
				<a href="{url}"
				   style="background:#4e73df; color:#ffffff; padding:10px 20px;
				          text-decoration:none; border-radius:4px; font-family:sans-serif;">
					View Complaint
				</a>
			</p>
		""".format(
			complaint_id=self.name,
			employee_name=self.employee_name or "",
			employee=self.employee or "",
			incident_type=self.incident_type or "",
			date_of_incident=frappe.format(self.date_of_incident, {"fieldtype": "Date"}),
			status=self.status,
			url=frappe.utils.get_url_to_form("Employee Complaint", self.name),
		)

		# Email notification
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message,
			reference_doctype=self.doctype,
			reference_name=self.name,
		)

		# In-app bell notifications
		for user in recipients:
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": subject,
				"email_content": message,
				"document_type": self.doctype,
				"document_name": self.name,
				"for_user": user,
				"type": "Alert",
			}).insert(ignore_permissions=True)
