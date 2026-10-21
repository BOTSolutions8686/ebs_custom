import click
import frappe

from ebs_custom.customizations.fields_setup import execute as setup_custom_fields


def after_install():
	"""Run on bench install-app ebs_custom."""
	setup_custom_fields()
	_apply_pwa_overlay_and_build()


def after_migrate():
	"""Run on bench migrate — re-applies PWA after hrms update."""
	from ebs_custom.patches.v1_0.setup_attendance_workflow import execute as setup_attendance_workflow
	from ebs_custom.patches.v1_0.setup_hr_request_workflows import execute as setup_hr_workflows

	setup_custom_fields()
	setup_attendance_workflow()
	setup_hr_workflows()
	_apply_pwa_overlay_and_build()


def _apply_pwa_overlay_and_build():
	from ebs_custom.patches.v1_0.apply_hrms_pwa_overlay import (
		apply_hrms_pwa_overlay,
		build_hrms_pwa,
	)

	if "hrms" not in frappe.get_installed_apps():
		frappe.logger().info("ebs_custom: hrms not installed — PWA overlay skipped")
		return

	apply_hrms_pwa_overlay()

	if build_hrms_pwa():
		click.secho("ebs_custom: BOT HR PWA built successfully.", fg="green")
	else:
		click.secho(
			"ebs_custom: PWA files copied into hrms. If forms do not show, run:\n"
			"  cd apps/hrms/frontend && yarn install && yarn build\n"
			"  bench build --app hrms && bench restart",
			fg="yellow",
		)
