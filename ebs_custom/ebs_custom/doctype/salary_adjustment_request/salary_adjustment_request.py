# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SalaryAdjustmentRequest(Document):
	def before_insert(self):
		if not self.initiated_by:
			self.initiated_by = frappe.session.user

	def validate(self):
		self.sync_status()
		self.fetch_current_salary()

	def on_update(self):
		self.sync_status()

	def sync_status(self):
		if self.workflow_state:
			self.status = self.workflow_state

	def fetch_current_salary(self):
		if self.employee and not self.current_salary:
			salary = frappe.db.get_value("Employee", self.employee, "custom_current_salary")
			if salary:
				self.current_salary = salary
