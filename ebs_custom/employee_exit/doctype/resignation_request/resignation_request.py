# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import date_diff, getdate


class ResignationRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		department: DF.Link | None
		employee: DF.Link
		employee_id: DF.Data | None
		employee_name: DF.Data | None
		last_working_day: DF.Date
		naming_series: DF.Literal["RES-.YYYY.-.#####"]
		notice_period_acknowledgement: DF.Check
		notice_period_days: DF.Int
		reason_for_resignation: DF.LongText
		resignation_date: DF.Date
	# end: auto-generated types

	# ------------------------------------------------------------------ #
	# Lifecycle hooks                                                      #
	# ------------------------------------------------------------------ #

	def before_insert(self):
		"""Auto-fill employee from the logged-in user if not set."""
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
		self._calculate_notice_period()
		self._validate_dates()

	def on_submit(self):
		"""Move status to first approver stage on submission."""
		pass
		# frappe.db.set_value(self.doctype, self.name, "status", "Pending Line Manager")
		# self._notify_approver("Line Manager", "Pending Line Manager")

	def on_cancel(self):
		pass
		# frappe.db.set_value(self.doctype, self.name, "status", "Draft")

	# ------------------------------------------------------------------ #
	# Validation helpers                                                   #
	# ------------------------------------------------------------------ #

	def _validate_employee_ownership(self):
		"""Employees can only submit resignation for themselves."""
		if frappe.session.user == "Administrator":
			return
		if self._is_hr_role():
			return

		linked_employee = frappe.db.get_value(
			"Employee", {"user_id": frappe.session.user}, "name"
		)
		if self.employee and linked_employee and self.employee != linked_employee:
			frappe.throw(_("You can only submit a resignation on your own behalf."))

	def _calculate_notice_period(self):
		"""Auto-calculate notice period in days."""
		if self.resignation_date and self.last_working_day:
			self.notice_period_days = date_diff(
				getdate(self.last_working_day), getdate(self.resignation_date)
			)

	def _validate_dates(self):
		if self.resignation_date and self.last_working_day:
			if getdate(self.last_working_day) <= getdate(self.resignation_date):
				frappe.throw(
					_("Last Working Day must be after the Resignation Date.")
				)

	# ------------------------------------------------------------------ #
	# Approval workflow                                                    #
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
		"""Advance to next approver or mark Approved on final step."""
		self._check_approver_permission()

		current_status = self.status
		chain = self.APPROVAL_CHAIN
		statuses = [s for _, s in chain]

		if current_status not in statuses:
			frappe.throw(_("This record is not pending any approval."))

		idx = statuses.index(current_status)

		if idx + 1 < len(chain):
			next_role, next_status = chain[idx + 1]
			frappe.db.set_value(self.doctype, self.name, "status", next_status)
			self.reload()
			self._notify_approver(next_role, next_status)
		else:
			# Final approval — HR Manager
			frappe.db.set_value(self.doctype, self.name, "status", "Approved")
			self.reload()
			self._on_final_approval()

		frappe.msgprint(_("Approved. Status updated successfully."))

	@frappe.whitelist()
	def reject(self, reason=None):
		"""Reject the resignation at any stage."""
		self._check_approver_permission()
		frappe.db.set_value(self.doctype, self.name, "status", "Rejected")
		self.reload()
		self._notify_rejection(reason)
		frappe.msgprint(_("Resignation has been rejected."))

	def _check_approver_permission(self):
		if frappe.session.user == "Administrator":
			return

		current_status = frappe.db.get_value(
			self.doctype, self.name, "status"
		)
		role_map = {s: r for r, s in self.APPROVAL_CHAIN}
		required_role = role_map.get(current_status)

		if required_role and not frappe.db.exists(
			"Has Role", {"parent": frappe.session.user, "role": required_role}
		):
			frappe.throw(
				_("You do not have permission to approve at this stage. "
				  "Required role: {0}").format(required_role)
			)

	# ------------------------------------------------------------------ #
	# Final approval actions                                               #
	# ------------------------------------------------------------------ #

	def _on_final_approval(self):
		"""Update Employee status to Left and notify external stakeholders."""
		# Update Employee master
		if self.employee:
			employee_doc = frappe.get_doc("Employee", self.employee)
			employee_doc.status = "Left"
			employee_doc.relieving_date = self.last_working_day
			employee_doc.save(ignore_permissions=True)

		# Notify CFO, CEO, Accounts Officer
		self._notify_external_stakeholders()

	def _notify_external_stakeholders(self):
		"""Send notifications to CFO, CEO, and Accounts Officer roles."""
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

		subject = _("Resignation Approved — Final Notification: {0}").format(self.name)
		message = self._build_notification_email(
			heading="Resignation Approved",
			note="The following resignation has received final HR Manager approval. "
			     "Please take necessary action for payroll clearance and offboarding.",
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

		subject = _("Action Required — Resignation Approval ({0}): {1}").format(
			status_label, self.name
		)
		message = self._build_notification_email(
			heading="Resignation Requires Your Approval",
			note="Please review and approve or reject the resignation request below.",
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

	def _notify_rejection(self, reason=None):
		employee_user = frappe.db.get_value(
			"Employee", self.employee, "user_id"
		)
		if not employee_user:
			return

		subject = _("Resignation Request Rejected: {0}").format(self.name)
		rejection_note = (
			"Reason: {0}".format(reason) if reason
			else "No reason was provided."
		)
		message = self._build_notification_email(
			heading="Your Resignation Request Has Been Rejected",
			note=rejection_note,
		)

		frappe.sendmail(
			recipients=[employee_user],
			subject=subject,
			message=message,
			reference_doctype=self.doctype,
			reference_name=self.name,
		)

	def _build_notification_email(self, heading, note):
		return """
			<p>{note}</p>
			<table style="border-collapse:collapse; width:100%; font-family:sans-serif; font-size:14px;">
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Request ID</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{name}</td>
				</tr>
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Employee</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{employee_name} ({employee})</td>
				</tr>
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Resignation Date</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{resignation_date}</td>
				</tr>
				<tr>
					<td style="padding:8px 12px; font-weight:bold; background:#f5f5f5; border:1px solid #e0e0e0;">Last Working Day</td>
					<td style="padding:8px 12px; border:1px solid #e0e0e0;">{last_working_day}</td>
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
					View Resignation Request
				</a>
			</p>
		""".format(
			note=note,
			name=self.name,
			employee_name=self.employee_name or "",
			employee=self.employee or "",
			resignation_date=frappe.format(self.resignation_date, {"fieldtype": "Date"}),
			last_working_day=frappe.format(self.last_working_day, {"fieldtype": "Date"}),
			status=self.status or "",
			url=frappe.utils.get_url_to_form(self.doctype, self.name),
		)

	# ------------------------------------------------------------------ #
	# Internal helpers                                                     #
	# ------------------------------------------------------------------ #

	def _is_hr_role(self):
		for role in ("HR Officer", "HR Manager", "Operations Manager", "COO", "CEO", "CFO"):
			if frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": role}):
				return True
		return False
