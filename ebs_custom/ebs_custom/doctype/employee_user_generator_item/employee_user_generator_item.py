# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class EmployeeUserGeneratorItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		employee: DF.Link | None
		employee_name: DF.Data | None
		message: DF.SmallText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		password: DF.Data | None
		select: DF.Check
		status: DF.Literal["Pending", "Created", "Skipped", "Failed"]
		user: DF.Link | None
	# end: auto-generated types

	pass
