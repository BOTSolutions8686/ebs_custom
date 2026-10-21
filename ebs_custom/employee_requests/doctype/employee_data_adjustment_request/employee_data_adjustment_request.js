// Copyright (c) 2026, Arslan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Data Adjustment Request", {

    onload: function(frm) {
        frm.trigger("set_employee_fields");
    },

    refresh: function(frm) {
        if (frm.doc.__islocal) {
            frm.trigger("set_employee_fields");
        }
    },

    set_employee_fields: function(frm) {

        frappe.model.with_doctype("Employee", function() {

            let fields = frappe.meta.get_docfields("Employee");
            let options = [""];
            let field_map = {};

            $.each(fields, function(i, field) {

                if (
                    field.fieldtype &&
                    field.label &&
                    !field.hidden &&
                    !field.read_only &&
                    field.fieldtype !== "Check" &&
                    ![
                        "Section Break",
                        "Column Break",
                        "Tab Break",
                        "Button",
                        "HTML",
                        "Image",
                        "Attach Image",
                        "Series",
                        "Table",
                        "Table MultiSelect",
                        "Fold",
                        "Heading"
                    ].includes(field.fieldtype) &&
                    ![
                        "name",
                        "naming_series",
                        "owner",
                        "creation",
                        "modified",
                        "modified_by",
                        "docstatus",
                        "idx",
                        "lft",
                        "rgt",
                        "old_parent"
                    ].includes(field.fieldname)
                ) {

                    // Show only label in dropdown
                    options.push(field.label);

                    // Store label -> fieldname mapping
                    field_map[field.label] = field.fieldname;
                }
            });

            // Save mapping on form
            frm.employee_field_map = field_map;

            console.log("Field Map:", field_map);

            if (frm.fields_dict["items"]) {
                frm.fields_dict["items"].grid.update_docfield_property(
                    "field_to_be_updated",
                    "options",
                    options
                );
            }
        });
    }
});

frappe.ui.form.on("Employee Adjustment Items", {

    before_items_add: function(frm) {
        frm.trigger("set_employee_fields");
    },

    field_to_be_updated: function(frm, cdt, cdn) {

        let row = locals[cdt][cdn];

        if (!frm.doc.employee) {
            frappe.msgprint("Please select Employee first");
            return;
        }

        if (row.field_to_be_updated) {

            let fieldname =
                frm.employee_field_map &&
                frm.employee_field_map[row.field_to_be_updated];

            if (!fieldname) {
                return;
            }

            console.log("Selected Label:", row.field_to_be_updated);
            console.log("Actual Fieldname:", fieldname);

            frappe.db.get_value(
                "Employee",
                frm.doc.employee,
                fieldname
            ).then(r => {

                console.log("DB Response:", r);

                if (r.message) {
                    row.current_value = r.message[fieldname] || "";
                    frm.refresh_field("items");
                }
            });
        }
    }
});