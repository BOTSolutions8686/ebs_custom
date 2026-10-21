// Copyright (c) 2026, Arslan and contributors
// For license information, please see license.txt

frappe.listview_settings["Employee Complaint"] = {
	get_indicator: function (doc) {
		const colourMap = {
			"Submitted":    "blue",
			"Under Review": "orange",
			"Resolved":     "green",
		};
		return [
			__(doc.status),
			colourMap[doc.status] || "gray",
			"status,=," + doc.status,
		];
	},
};
