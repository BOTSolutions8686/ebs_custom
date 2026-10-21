# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

import frappe


def _is_privileged_role(user):
	"""Returns True if user has any elevated HR/management role."""
	privileged = (
		"HR Officer", "HR Manager", "Operations Manager",
		"COO", "CEO", "CFO", "Accounts Officer", "System Manager"
	)
	for role in privileged:
		if frappe.db.exists("Has Role", {"parent": user, "role": role}):
			return True
	return False


def _get_employee_for_user(user):
	return frappe.db.get_value("Employee", {"user_id": user}, "name")


# ------------------------------------------------------------------ #
# Resignation Request                                                  #
# ------------------------------------------------------------------ #

def get_resignation_query_conditions(user):
	"""Employees only see their own records; privileged roles see all."""
	if user == "Administrator" or _is_privileged_role(user):
		return ""

	employee = _get_employee_for_user(user)
	if employee:
		return "(`tabResignation Request`.employee = '{0}')".format(
			frappe.db.escape(employee)
		)

	return "1=0"  # No access if no linked employee


def has_resignation_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if user == "Administrator" or _is_privileged_role(user):
		return True

	employee = _get_employee_for_user(user)
	return bool(employee and doc.employee == employee)


# ------------------------------------------------------------------ #
# Offboarding Interview                                                #
# ------------------------------------------------------------------ #

def get_offboarding_query_conditions(user):
	"""Employees can read their own; HR roles see all."""
	if user == "Administrator" or _is_privileged_role(user):
		return ""

	employee = _get_employee_for_user(user)
	if employee:
		return "(`tabOffboarding Interview`.employee = '{0}')".format(
			frappe.db.escape(employee)
		)

	return "1=0"


def has_offboarding_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if user == "Administrator" or _is_privileged_role(user):
		return True

	employee = _get_employee_for_user(user)
	return bool(employee and doc.employee == employee)
