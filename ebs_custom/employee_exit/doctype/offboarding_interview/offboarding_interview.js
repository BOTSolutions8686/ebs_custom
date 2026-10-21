// Copyright (c) 2026, Arslan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Offboarding Interview", {

	refresh(frm) {
		// frm.trigger("set_approval_buttons");
		// frm.set_df_property("status", "read_only", 1);
	},

	resignation_request(frm) {
		if (frm.doc.resignation_request) {
			frappe.db.get_value(
				"Resignation Request",
				frm.doc.resignation_request,
				["employee", "employee_name", "employee_id", "department"],
				(r) => {
					if (r) {
						frm.set_value("employee",      r.employee);
						frm.set_value("employee_name", r.employee_name);
						frm.set_value("employee_id",   r.employee_id);
						frm.set_value("department",    r.department);
					}
				}
			);
		}
	},

	employee(frm) {
		if (frm.doc.employee) {
			frappe.db.get_value("Employee", frm.doc.employee, ["employee_name", "name", "department"], (r) => {
				if (r) {
					frm.set_value("employee_name", r.employee_name);
					frm.set_value("employee_id",   r.name);
					frm.set_value("department",    r.department);
				}
			});
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
					__("Approve this offboarding interview?"),
					() => frm.call("approve").then(() => frm.reload_doc())
				);
			}, __("Actions")).addClass("btn-success");

			frm.add_custom_button(__("Reject"), () => {
				frappe.prompt(
					{label: __("Reason"), fieldname: "reason", fieldtype: "Small Text"},
					(values) => {
						frm.call("reject", {reason: values.reason}).then(() => frm.reload_doc());
					},
					__("Reject Interview"),
					__("Confirm")
				);
			}, __("Actions")).addClass("btn-danger");
		}
	}
});
