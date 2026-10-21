// Copyright (c) 2026, Arslan and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Stock Consumption Report"] = {

    filters: [

        {
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company",
            reqd: 1,
            default: frappe.defaults.get_default("company")
        },

        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_start()
        },

        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_end()
        },

        {
            fieldname: "employee",
            label: "Employee",
            fieldtype: "Link",
            options: "Employee"
        },

        {
            fieldname: "department",
            label: "Department",
            fieldtype: "Link",
            options: "Department"
        },

        {
            fieldname: "consumption_type",
            label: "Consumption Type",
            fieldtype: "Link",
            options: "Consumption Item"
        },

        {
            fieldname: "warehouse",
            label: "Warehouse",
            fieldtype: "Link",
            options: "Warehouse"
        },

        {
            fieldname: "custom_branch",
            label: "Branch",
            fieldtype: "Link",
            options: "Branch"
        }

    ],

    tree: true,

    name_field: "employee",

    parent_field: "parent_employee",

    initial_depth: 1
};

