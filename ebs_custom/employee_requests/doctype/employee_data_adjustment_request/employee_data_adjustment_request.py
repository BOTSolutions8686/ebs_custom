# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

FIELD_MAP = {
	"Cell Number": "cell_number",
	"Mobile": "cell_number",
	"Mobile No": "cell_number",
	"Personal Email": "personal_email",
	"Current Address": "current_address",
	"Permanent Address": "permanent_address",
	"Emergency Phone": "emergency_phone_number",
	"Contact Person": "person_to_be_contacted",
	"Bank Account": "bank_ac_no",
	"Bank A/C No.": "bank_ac_no",
	"IBAN": "iban",
}

SKIP_FIELDTYPES = {
	"Section Break",
	"Column Break",
	"Tab Break",
	"Button",
	"HTML",
	"Image",
	"Attach Image",
	"Series",
	"Table",
	"Table MultiSelect",
	"Fold",
	"Heading",
	"Check",
}
SKIP_FIELDNAMES = {
	"name",
	"naming_series",
	"owner",
	"creation",
	"modified",
	"modified_by",
	"docstatus",
	"idx",
	"lft",
	"rgt",
	"old_parent",
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
		for row in self.items:
			fieldname = employee_fieldname(row.field_to_be_updated)
			if not fieldname:
				frappe.throw(_("This field cannot be updated: {0}").format(row.field_to_be_updated))
			employee.set(fieldname, row.new_value)

		employee.save(ignore_permissions=True)
		frappe.db.set_value(self.doctype, self.name, "status", "Completed", update_modified=False)


def employee_fieldname(label):
	meta = frappe.get_meta("Employee")
	fieldname = FIELD_MAP.get(label)
	if not fieldname:
		for df in meta.fields:
			if df.label == label:
				fieldname = df.fieldname
				break

	df = meta.get_field(fieldname) if fieldname else None
	if (
		not df
		or df.hidden
		or df.read_only
		or df.fieldtype in SKIP_FIELDTYPES
		or df.fieldname in SKIP_FIELDNAMES
	):
		return None
	return df.fieldname
