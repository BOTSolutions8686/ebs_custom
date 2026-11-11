# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

FIELD_MAP = {
	"Cell Number": "cell_number",
	"Personal Email": "personal_email",
	"Current Address": "current_address",
	"Permanent Address": "permanent_address",
	"Emergency Phone": "emergency_phone_number",
	"Contact Person": "person_to_be_contacted",
	"Bank Account": "bank_ac_no",
	"IBAN": "iban",
}


class EmployeeDataAdjustmentRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from ebs_custom.employee_requests.doctype.employee_adjustment_items.employee_adjustment_items import EmployeeAdjustmentItems
		from frappe.types import DF

		amended_from: DF.Link | None
		company: DF.Link | None
		department: DF.Link | None
		designation: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data
		hr_remarks: DF.SmallText | None
		items: DF.Table[EmployeeAdjustmentItems]
		request_date: DF.Date
		status: DF.Literal["Pending", "In Progress", "Completed"]
		supporting_document: DF.Attach | None
	# end: auto-generated types

	def on_submit(self):
		self.apply_to_employee()

	def apply_to_employee(self):
		if not self.items:
			frappe.throw(_("Add at least one change."))

		employee = frappe.get_doc("Employee", self.employee)
		meta = frappe.get_meta("Employee")
		for row in self.items:
			fieldname = FIELD_MAP.get(row.field_to_be_updated)
			if not fieldname or not meta.has_field(fieldname):
				frappe.throw(_("This field cannot be updated: {0}").format(row.field_to_be_updated))
			employee.set(fieldname, row.new_value)

		employee.save(ignore_permissions=True)
		frappe.db.set_value(self.doctype, self.name, "status", "Completed", update_modified=False)
