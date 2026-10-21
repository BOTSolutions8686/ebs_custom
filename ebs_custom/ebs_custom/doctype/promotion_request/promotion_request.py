# Copyright (c) 2026, Arslan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PromotionRequest(Document):
	def before_insert(self):
		if not self.initiated_by:
			self.initiated_by = frappe.session.user

	def validate(self):
		self.sync_status()

	def on_update(self):
		self.sync_status()

	def sync_status(self):
		if self.workflow_state:
			self.status = self.workflow_state
