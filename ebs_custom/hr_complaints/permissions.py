# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt
#
# Permission query controller for Employee Complaint.
# Registered in hooks.py under permission_query_conditions and has_permission.

import frappe


def get_permission_query_conditions(user: str | None = None) -> str:
	"""
	Returns an SQL WHERE fragment used by Frappe when building list/report
	queries for Employee Complaint.

	Access rules:
	  - Administrator         → no restriction (sees all)
	  - HR Officer role       → no restriction (sees all)
	  - Employee (self only)  → restricted to records where employee = their own ID
	  - Anyone else           → impossible condition; sees nothing
	"""
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return ""

	if frappe.db.exists("Has Role", {"parent": user, "role": "HR Officer"}):
		return ""

	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
	if employee:
		return "`tabEmployee Complaint`.`employee` = {0}".format(
			frappe.db.escape(employee)
		)

	# No matching employee record — show nothing
	return "1=0"


def has_permission(doc, ptype: str = "read", user: str | None = None) -> bool:
	"""
	Document-level permission check called by Frappe when a specific record
	is opened, written, or deleted.

	Access rules:
	  - Administrator   → always True
	  - HR Officer      → always True (full access)
	  - Own employee    → read & create only; write/delete blocked
	  - Others          → False
	"""
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return True

	if frappe.db.exists("Has Role", {"parent": user, "role": "HR Officer"}):
		return True

	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
	if employee and doc.employee == employee:
		# Employees may read and create their own complaints, but not edit them
		if ptype in ("read", "create"):
			return True

	return False
