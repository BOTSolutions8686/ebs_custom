// Copyright (c) 2026, Arslan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Resignation Request", {

	refresh(frm) {
		// frm.trigger("set_approval_buttons");
		// frm.trigger("lock_status_field");
	},

	employee(frm) {
		if (frm.doc.employee) {
			frappe.db.get_value("Employee", frm.doc.employee, ["employee_name", "name", "department"], (r) => {
				if (r) {
					frm.set_value("employee_name", r.employee_name);
					frm.set_value("employee_id", r.name);
					frm.set_value("department", r.department);
				}
			});
		}
	},

	resignation_date(frm) {
		frm.trigger("calc_notice_period");
	},

	last_working_day(frm) {
		frm.trigger("calc_notice_period");
	},

	calc_notice_period(frm) {
		if (frm.doc.resignation_date && frm.doc.last_working_day) {
			const start = frappe.datetime.str_to_obj(frm.doc.resignation_date);
			const end   = frappe.datetime.str_to_obj(frm.doc.last_working_day);
			const diff  = frappe.datetime.get_diff(end, start);
			frm.set_value("notice_period_days", diff > 0 ? diff : 0);
		}
	},

	set_approval_buttons(frm) {
		const approvalStatuses = [
			"Pending Line Manager",
			"Pending HR Officer",
			"Pending Operations Manager",
			"Pending COO",
			"Pending HR Manager"
		];

		if (!frm.doc.__islocal && approvalStatuses.includes(frm.doc.status)) {
			frm.add_custom_button(__("Approve"), () => {
				frappe.confirm(
					__("Are you sure you want to approve this resignation request?"),
					() => {
						frm.call("approve").then(() => frm.reload_doc());
					}
				);
			}, __("Actions")).addClass("btn-success");

			frm.add_custom_button(__("Reject"), () => {
				frappe.prompt(
					{label: __("Reason for Rejection"), fieldname: "reason", fieldtype: "Small Text"},
					(values) => {
						frm.call("reject", {reason: values.reason}).then(() => frm.reload_doc());
					},
					__("Reject Resignation"),
					__("Confirm Rejection")
				);
			}, __("Actions")).addClass("btn-danger");
		}
	},

	lock_status_field(frm) {
		// Status is always read-only; driven by workflow
		frm.set_df_property("status", "read_only", 1);
	}
});
