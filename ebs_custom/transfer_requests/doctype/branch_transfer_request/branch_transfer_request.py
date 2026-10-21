# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class BranchTransferRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		company: DF.Link | None
		current_branch: DF.Link
		employee: DF.Link
		employee_name: DF.Data | None
		reason: DF.LongText | None
		request_date: DF.Date
		requested_branch: DF.Link
	# end: auto-generated types

	def validate(self):
		self.check_employee_branch()
		self.check_same_branch()

	def check_same_branch(self):
		if self.current_branch == self.requested_branch:
			frappe.throw(_("Current Branch and Requested Branch cannot be the same."))

	def check_employee_branch(self):
		employee = frappe.get_doc("Employee", self.employee, fields=["employee_name", "custom_branch"])
		if employee.custom_branch != self.current_branch:
			frappe.throw(_("{0} branch {1} does not match the selected Branch {2}.").format(employee.employee_name, employee.custom_branch, self.current_branch))

	def on_submit(self):
		self.change_employee_branch()
	
	def change_employee_branch(self):
		frappe.db.set_value(
			"Employee",
			self.employee,
			"custom_branch",
			self.requested_branch,
			update_modified=True,
		)