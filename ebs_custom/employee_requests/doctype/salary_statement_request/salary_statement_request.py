# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SalaryStatementRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		company: DF.Link | None
		date_of_joining: DF.Date | None
		designation: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data | None
		purpose: DF.SmallText
		remarks: DF.SmallText | None
		request_date: DF.Date
		salary_statement: DF.Attach | None
	# end: auto-generated types

	pass
