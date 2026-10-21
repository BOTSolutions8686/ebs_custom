// Copyright (c) 2026, Arslan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Adjustment Request", {
	employee(frm) {
		if (!frm.doc.employee) {
			return;
		}
		frappe.db.get_value("Employee", frm.doc.employee, "custom_current_salary").then((r) => {
			if (r.message && r.message.custom_current_salary) {
				frm.set_value("current_salary", r.message.custom_current_salary);
			}
		});
	},
});
