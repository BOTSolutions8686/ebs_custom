# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ItemDomainDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		domain: DF.Link
		domain_code: DF.Data
		domain_description: DF.SmallText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		primary_domain: DF.Check
	# end: auto-generated types

	pass
