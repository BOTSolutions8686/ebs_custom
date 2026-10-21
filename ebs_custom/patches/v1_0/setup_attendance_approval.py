import frappe

from ebs_custom.customizations.fields_setup import setup_custom_fields


def execute():
	setup_custom_fields()
	frappe.db.commit()
