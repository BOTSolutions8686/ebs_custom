# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class OffboardingInterview(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		comments_feedback: DF.LongText | None
		department: DF.Link | None
		employee: DF.Link
		employee_id: DF.Data | None
		employee_name: DF.Data | None
		exit_interview_date: DF.Date
		interviewer_name: DF.Link
		naming_series: DF.Literal["EXIT-.YYYY.-.#####"]
		overall_experience_rating: DF.Literal["", "1 - Very Poor", "2 - Poor", "3 - Average", "4 - Good", "5 - Excellent"]
		reason_for_leaving: DF.Literal["", "Better Opportunity", "Compensation", "Work Environment", "Career Growth", "Personal Reasons", "Relocation", "Health Reasons", "Family Reasons", "Higher Education", "Other"]
		reason_for_leaving_details: DF.SmallText | None
		resignation_request: DF.Link | None
		would_recommend: DF.Literal["", "Yes", "No"]
	# end: auto-generated types

	# ------------------------------------------------------------------ #
	# Lifecycle hooks                                                      #
	# ------------------------------------------------------------------ #

	def before_insert(self):
		"""Auto-fill employee from linked Resignation Request if provided."""
		if self.resignation_request and not self.employee:
			emp = frappe.db.get_value(
				"Resignation Request", self.resignation_request, "employee"
			)
			if emp:
				self.employee = emp

		if self.employee and not self.employee_id:
			self.employee_id = self.employee

	def validate(self):
		self._validate_resignation_link()

	def on_submit(self):
		pass
		# frappe.db.set_value(self.doctype, self.name, "status", "Pending Line Manager")
		# self._notify_approver("Line Manager", "Pending Line Manager")

	def on_cancel(self):
		pass
		# frappe.db.set_value(self.doctype, self.name, "status", "Scheduled")

	# ------------------------------------------------------------------ #
	# Validation helpers                                                   #
	# ------------------------------------------------------------------ #

	def _validate_resignation_link(self):
		"""If linked resignation exists, ensure the employee matches."""
		if not self.resignation_request:
			return
		res_employee = frappe.db.get_value(
			"Resignation Request", self.resignation_request, "employee"
		)
		if res_employee and self.employee and res_employee != self.employee:
			frappe.throw(
				_("The linked Resignation Request belongs to a different employee.")
			)

	# ------------------------------------------------------------------ #
	# Approval workflow (mirrors Resignation Request)                     #
	# ------------------------------------------------------------------ #

	APPROVAL_CHAIN = [
		("Line Manager",        "Pending Line Manager"),
		("HR Officer",          "Pending HR Officer"),
		("Operations Manager",  "Pending Operations Manager"),
		("COO",                 "Pending COO"),
		("HR Manager",          "Pending HR Manager"),
	]

	@frappe.whitelist()
	def approve(self):
		self._check_approver_permission()

		current_status = self.status
		statuses = [s for _, s in self.APPROVAL_CHAIN]

		if current_status not in statuses:
			frappe.throw(_("This record is not pending any approval."))

		idx = statuses.index(current_status)

		if idx + 1 < len(self.APPROVAL_CHAIN):
			next_role, next_status = self.APPROVAL_CHAIN[idx + 1]
			frappe.db.set_value(self.doctype, self.name, "status", next_status)
			self.reload()
			self._notify_approver(next_role, next_status)
		else:
			frappe.db.set_value(self.doctype, self.name, "status", "Approved")
			self.reload()
			self._on_final_approval()

		frappe.msgprint(_("Approved. Status updated successfully."))

	@frappe.whitelist()
	def reject(self, reason=None):
		self._check_approver_permission()
		frappe.db.set_value(self.doctype, self.name, "status", "Rejected")
		self.reload()
		frappe.msgprint(_("Offboarding Interview has been rejected."))

	def _check_approver_permission(self):
		if frappe.session.user == "Administrator":
			return

		current_status = frappe.db.get_value(self.doctype, self.name, "status")
		role_map = {s: r for r, s in self.APPROVAL_CHAIN}
		required_role = role_map.get(current_status)

		if required_role and not frappe.db.exists(
			"Has Role", {"parent": frappe.session.user, "role": required_role}
		):
			frappe.throw(
				_("You do not have permission to approve at this stage. "
				  "Required role: {0}").format(required_role)
			)

	def _on_final_approval(self):
		"""Final HR Manager approval — notify external stakeholders."""
		self._notify_external_stakeholders()

	def _notify_external_stakeholders(self):
		notify_roles = ["CFO", "CEO", "Accounts Officer"]
		recipients = []

		for role in notify_roles:
			users = frappe.get_all(
				"Has Role",
				filters={"role": role, "parenttype": "User"},
				fields=["parent"],
			)
			recipients += [u["parent"] for u in users if u["parent"] != "Administrator"]

		if not recipients:
			return

		subject = _("Offboarding Interview Approved — Final Notification: {0}").format(self.name)
		message = self._build_email(
			"Offboarding Interview Approved",
			"The exit interview for the following employee has received final HR Manager approval."
		)

		frappe.sendmail(
			recipients=list(set(recipients)),
			subject=subject,
			message=message,
			reference_doctype=self.doctype,
			reference_name=self.name,
		)

		for user in list(set(recipients)):
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": subject,
				"email_content": message,
				"document_type": self.doctype,
				"document_name": self.name,
				"for_user": user,
				"type": "Alert",
			}).insert(ignore_permissions=True)

	# ------------------------------------------------------------------ #
	# Notification helpers                                                 #
	# ------------------------------------------------------------------ #

	def _notify_approver(self, role, status_label):
		users = frappe.get_all(
			"Has Role",
			filters={"role": role, "parenttype": "User"},
			fields=["parent"],
		)
		recipients = [u["parent"] for u in users if u["parent"] != "Administrator"]

		if not recipients:
			return

		subject = _("Action Required — Offboarding Interview Approval ({0}): {1}").format(
			status_label, self.name
		)
		message = self._build_email(
			"Offboarding Interview Requires Your Approval",
			"Please review and approve or reject the offboarding interview below."
		)

		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message,
			reference_doctype=self.doctype,
			reference_name=self.name,
		)

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

	def _build_email(self, heading, note):
		return """
			<p>{note}</p>
			<table style="border-collapse:collapse; width:100%; font-family:sans-serif; font-size:14px;">
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Interview ID</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{name}</td>
				</tr>
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Employee</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{employee_name} ({employee})</td>
				</tr>
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Interview Date</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{interview_date}</td>
				</tr>
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Reason for Leaving</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{reason}</td>
				</tr>
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Rating</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{rating}</td>
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
					View Offboarding Interview
				</a>
			</p>
		""".format(
			note=note,
			name=self.name,
			employee_name=self.employee_name or "",
			employee=self.employee or "",
			interview_date=frappe.format(self.exit_interview_date, {"fieldtype": "Date"}),
			reason=self.reason_for_leaving or "",
			rating=self.overall_experience_rating or "",
			status=self.status or "",
			url=frappe.utils.get_url_to_form(self.doctype, self.name),
		)
