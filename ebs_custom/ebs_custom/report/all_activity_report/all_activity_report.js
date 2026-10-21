// Copyright (c) 2026, Arslan and contributors
// For license information, please see license.txt

frappe.query_reports["All Activity Report"] = {
    filters: [
        {
            fieldname: "user",
            label: "User",
            fieldtype: "Link",
            options: "User",
        },
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
        },
    ],
};
