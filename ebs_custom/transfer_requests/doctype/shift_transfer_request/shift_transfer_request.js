// Copyright (c) 2026, Arslan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift Transfer Request", {
    setup(frm) {
        frm.set_query("shift_assignment", function () {
            if (!frm.doc.employee) {
                return {
                    filters: {
                        name: ["=", ""]
                    }
                };
            }
            return {
                filters: {
                    employee: frm.doc.employee,
                    docstatus: 1,
                    status: "Active"
                }
            };
        });
    },
});
