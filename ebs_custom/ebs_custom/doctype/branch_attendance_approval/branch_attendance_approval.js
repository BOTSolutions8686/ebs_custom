// Copyright (c) 2026, Arslan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Branch Attendance Approval", {
	refresh(frm) {
		if (frm.is_new() && !frm.doc.branch) {
			frappe.db
				.get_value("Employee", { user_id: frappe.session.user }, "custom_branch")
				.then((r) => {
					if (r.message && r.message.custom_branch) {
						frm.set_value("branch", r.message.custom_branch);
					}
				});
		}

		if (!frm.doc.excel_generated && frm.doc.workflow_state !== "Approved") {
			frm.add_custom_button(__("Load Check-ins"), () => load_checkins(frm));
		}
	},

	branch(frm) {
		if (frm.doc.branch && frm.doc.attendance_date) {
			set_company_from_branch(frm);
		}
	},

	attendance_date(frm) {
		if (frm.doc.branch && frm.doc.attendance_date) {
			set_company_from_branch(frm);
		}
	},
});

function set_company_from_branch(frm) {
	frappe.db.get_value("Employee", { user_id: frappe.session.user }, "company").then((r) => {
		if (r.message && r.message.company) {
			frm.set_value("company", r.message.company);
		}
	});
}

function load_checkins(frm) {
	if (!frm.doc.branch || !frm.doc.attendance_date) {
		frappe.msgprint(__("Please select Branch and Attendance Date first."));
		return;
	}

	frappe.call({
		method: "ebs_custom.attendance.events.attendance.load_branch_checkins",
		args: {
			branch: frm.doc.branch,
			attendance_date: frm.doc.attendance_date,
		},
		freeze: true,
		freeze_message: __("Loading check-ins..."),
		callback(r) {
			if (!r.message || !r.message.length) {
				frappe.msgprint(__("No employees found for this branch."));
				return;
			}

			frm.clear_table("employees");
			r.message.forEach((row) => {
				const child = frm.add_child("employees");
				child.employee = row.employee;
				child.employee_name = row.employee_name;
				child.employee_id = row.employee_id;
				child.check_in_time = row.check_in_time;
				child.check_out_time = row.check_out_time;
				child.status = row.status;
			});
			frm.refresh_field("employees");
			frappe.show_alert({
				message: __("{0} employee(s) loaded", [r.message.length]),
				indicator: "green",
			});
		},
	});
}
