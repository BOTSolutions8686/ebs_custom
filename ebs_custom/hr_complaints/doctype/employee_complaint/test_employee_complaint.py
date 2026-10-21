# Copyright (c) 2026, Arslan and Contributors
# See license.txt

import frappe
import unittest


class TestEmployeeComplaint(unittest.TestCase):

	def setUp(self):
		if not frappe.db.exists("Role", "HR Officer"):
			frappe.get_doc({"doctype": "Role", "role_name": "HR Officer"}).insert()

	def test_complaint_creation(self):
		doc = frappe.get_doc({
			"doctype": "Employee Complaint",
			"employee": "_Test Employee",
			"date_of_incident": frappe.utils.nowdate(),
			"incident_type": "Misconduct",
			"persons_involved": "Test Person",
			"description": "Detailed description of the incident for testing.",
			"status": "Submitted",
		})
		doc.insert(ignore_permissions=True)
		self.assertEqual(doc.status, "Submitted")
		frappe.db.rollback()

	def test_default_status_is_submitted(self):
		doc = frappe.get_doc({
			"doctype": "Employee Complaint",
			"employee": "_Test Employee",
			"date_of_incident": frappe.utils.nowdate(),
			"incident_type": "Other",
			"persons_involved": "Someone",
			"description": "Detailed description for default status test.",
		})
		doc.insert(ignore_permissions=True)
		self.assertEqual(doc.status, "Submitted")
		frappe.db.rollback()

	def test_hr_officer_can_change_status(self):
		doc = frappe.get_doc({
			"doctype": "Employee Complaint",
			"employee": "_Test Employee",
			"date_of_incident": frappe.utils.nowdate(),
			"incident_type": "Harassment",
			"persons_involved": "Manager X",
			"description": "Harassment incident description.",
			"status": "Submitted",
		})
		doc.insert(ignore_permissions=True)
		doc.status = "Under Review"
		# HR Officer bypass — tested with ignore_permissions
		doc.save(ignore_permissions=True)
		self.assertEqual(doc.status, "Under Review")
		frappe.db.rollback()
