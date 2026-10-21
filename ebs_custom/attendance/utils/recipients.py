import frappe


REPORT_ROLES = [
	"HR Officer",
	"HR Manager",
	"Operations Manager",
	"COO",
]


def get_role_emails(roles=None):
	roles = roles or REPORT_ROLES
	emails = set()

	for role in roles:
		users = frappe.get_all(
			"Has Role",
			filters={"parenttype": "User", "role": role},
			pluck="parent",
		)
		for user in users:
			if not user or user == "Guest":
				continue
			enabled = frappe.db.get_value("User", user, "enabled")
			if not enabled:
				continue
			email = frappe.db.get_value("User", user, "email")
			if email:
				emails.add(email)

	return sorted(emails)
