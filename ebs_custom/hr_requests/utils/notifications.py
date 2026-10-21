import frappe


def get_users_by_roles(roles):
	users = set()
	for role in roles:
		for user in frappe.get_all(
			"Has Role",
			filters={"parenttype": "User", "role": role},
			pluck="parent",
		):
			if not user or user == "Guest":
				continue
			if frappe.db.get_value("User", user, "enabled"):
				users.add(user)
	return list(users)


def notify_users(doc, roles, subject, message):
	users = get_users_by_roles(roles)
	for user in users:
		_create_notification_log(user, doc, subject, message)


def notify_users_by_email(doc, roles, subject, message):
	recipients = []
	for user in get_users_by_roles(roles):
		email = frappe.db.get_value("User", user, "email")
		if email:
			recipients.append(email)

	if not recipients:
		return

	try:
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message,
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)
	except Exception:
		frappe.log_error(title=f"HR Request Email: {doc.name}")


def _create_notification_log(user, doc, subject, message):
	try:
		notification = frappe.new_doc("Notification Log")
		notification.for_user = user
		notification.type = "Alert"
		notification.document_type = doc.doctype
		notification.document_name = doc.name
		notification.subject = subject
		notification.email_content = message
		notification.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(title=f"HR Request Notification: {doc.name}")
