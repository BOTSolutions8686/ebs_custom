import frappe

from ebs_custom.hr_requests.utils.workflow_helpers import create_workflow_if_missing


def execute():
	create_workflow_if_missing(
		"Salary Adjustment Request",
		"Salary Adjustment Request Workflow",
	)
	create_workflow_if_missing(
		"Promotion Request",
		"Promotion Request Workflow",
	)
	frappe.db.commit()
