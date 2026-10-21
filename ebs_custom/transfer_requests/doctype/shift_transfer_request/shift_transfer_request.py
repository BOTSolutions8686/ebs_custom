# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, add_days, today


class ShiftTransferRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		company: DF.Link | None
		current_end_date: DF.Date | None
		current_shift: DF.Link
		current_start_date: DF.Date | None
		effective_date: DF.Date
		employee: DF.Link
		employee_name: DF.Data | None
		reason: DF.LongText | None
		requested_shift: DF.Link
		shift_assignment: DF.Link
	# end: auto-generated types

	def validate(self):
		self.check_same_shift()
		self.check_dates()

	def check_same_shift(self):
		if self.current_shift == self.requested_shift:
			frappe.throw(_("Current Shift and Requested Shift cannot be the same."))
	
	def check_dates(self):
		if getdate(self.effective_date) < getdate(today()):
			frappe.throw(_("Effective Date cannot be before today's date."))		
	
		if getdate(self.effective_date) <= getdate(self.current_start_date):
			frappe.throw(_("Effective Date cannot be before or equal to Current Start Date."))

		if self.current_end_date and getdate(self.effective_date) > getdate(self.current_end_date):
			frappe.throw(_("Effective Date cannot be after Current End Date."))

	def on_submit(self):
		self.change_employee_shift()
	
	def change_employee_shift(self):
		old_assignment = frappe.get_doc("Shift Assignment", self.shift_assignment)
		old_end_date = old_assignment.end_date
		new_old_end_date = add_days(self.effective_date, -1)

		frappe.db.set_value(
			"Shift Assignment",
			old_assignment.name,
			"end_date",
			new_old_end_date,
			update_modified=True,
		)

		# Create new shift assignment from effective date
		new_assignment = frappe.new_doc("Shift Assignment")
		new_assignment.employee = self.employee
		new_assignment.company = self.company
		new_assignment.shift_type = self.requested_shift
		new_assignment.start_date = self.effective_date
		new_assignment.status = "Active"
		if old_assignment.end_date:
			new_assignment.end_date = old_assignment.end_date

		new_assignment.insert(ignore_permissions=True)
		new_assignment.submit()

		self.add_comment(
			"Comment",
			_("Old Shift Assignment {0} end date updated to {1}. New Shift Assignment {2} created from {3}.").format(
				frappe.bold(old_assignment.name),
				frappe.bold(new_old_end_date),
				frappe.bold(new_assignment.name),
				frappe.bold(self.effective_date),
			)
		)

		frappe.msgprint(
			_("Shift has been changed successfully. New Shift Assignment: {0}").format(
				frappe.bold(new_assignment.name)
			)
		)
