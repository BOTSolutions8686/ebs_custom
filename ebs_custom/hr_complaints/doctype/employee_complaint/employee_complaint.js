// Copyright (c) 2026, Arslan and contributors
// For license information, please see license.txt

function isHRUser() {
	const roles = frappe.user_roles || [];
	return roles.includes("HR Officer") || frappe.session.user === "Administrator";
}

frappe.ui.form.on("Employee Complaint", {

	onload: function (frm) {
		// Auto-fill Employee details for new documents
		if (frm.is_new()) {
			frappe.db.get_value(
				"Employee",
				{ user_id: frappe.session.user },
				["name", "employee_name", "department"],
				function (r) {
					if (r && r.name) {
						frm.set_value("employee", r.name);
						frm.set_value("employee_name", r.employee_name);
						frm.set_value("employee_id", r.name);
						frm.set_value("department", r.department);
					}
				}
			);

			// Set default status only for new records
			if (!frm.doc.status) {
				frm.set_value("status", "Submitted");
			}
		}
	},

	setup: function (frm) {
		// Lock fields for non-HR users
		if (!isHRUser()) {
			frm.set_df_property("status", "read_only", 1);
			frm.set_df_property("hr_remarks", "read_only", 1);

			if (!frm.is_new()) {
				frm.set_df_property("employee", "read_only", 1);
			}
		}
	},

	refresh: function (frm) {
		// Status indicator
		const statusColours = {
			"Submitted": "blue",
			"Under Review": "orange",
			"Resolved": "green"
		};

		if (frm.doc.status) {
			frm.page.set_indicator(
				__(frm.doc.status),
				statusColours[frm.doc.status] || "gray"
			);
		}

		// Ensure fields remain read-only after refresh
		if (!isHRUser()) {
			frm.set_df_property("status", "read_only", 1);
			frm.set_df_property("hr_remarks", "read_only", 1);

			if (!frm.is_new()) {
				frm.set_df_property("employee", "read_only", 1);
			}
		}

		// HR/Admin action buttons
		if (isHRUser() && !frm.is_new()) {

			if (frm.doc.status === "Submitted") {
				frm.add_custom_button(__("Mark Under Review"), function () {
					frm.set_value("status", "Under Review");
					frm.save();
				}, __("Actions"));
			}

			if (frm.doc.status === "Under Review") {
				frm.add_custom_button(__("Mark Resolved"), function () {
					frm.set_value("status", "Resolved");
					frm.save();
				}, __("Actions"));
			}
		}
	},

	employee: function (frm) {
		if (frm.doc.employee) {
			frappe.db.get_value(
				"Employee",
				frm.doc.employee,
				["employee_name", "department"],
				function (r) {
					if (r) {
						frm.set_value("employee_name", r.employee_name);
						frm.set_value("employee_id", frm.doc.employee);
						frm.set_value("department", r.department);
					}
				}
			);
		}
	}

});