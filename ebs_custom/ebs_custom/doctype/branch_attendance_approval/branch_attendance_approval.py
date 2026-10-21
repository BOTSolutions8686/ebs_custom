# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class BranchAttendanceApproval(Document):
	def before_insert(self):
		self.set_branch_manager()

	def validate(self):
		self.set_branch_manager()
		self.validate_branch_manager_branch()

	def set_branch_manager(self):
		if self.branch_manager:
			return

		employee = frappe.db.get_value(
			"Employee",
			{"user_id": frappe.session.user, "status": "Active"},
			["name", "company"],
			as_dict=True,
		)
		if employee:
			self.branch_manager = employee.name
			if not self.company:
				self.company = employee.company

	def validate_branch_manager_branch(self):
		if not self.branch_manager or not self.branch:
			return

		manager_branch = frappe.db.get_value("Employee", self.branch_manager, "custom_branch")
		if manager_branch and manager_branch != self.branch:
			frappe.throw(
				_("Branch Manager belongs to branch {0}. You can only approve branch {0}.").format(
					manager_branch
				)
			)
