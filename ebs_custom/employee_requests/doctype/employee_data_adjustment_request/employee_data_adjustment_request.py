# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


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

	pass
