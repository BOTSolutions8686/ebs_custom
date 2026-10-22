import re

import frappe


PWA_ACCESS_ROLES = [
	"Employee",
	"HR User",
	"HR Manager",
	"HR Officer",
	"Leave Approver",
	"Expense Approver",
	"Branch Manager",
	"Division Manager",
	"Operations Manager",
	"COO",
	"CFO",
	"CEO",
	"Accounts Officer",
	"Accounts User",
	"Line Manager",
	"Finance Manager",
	"Finance Manger",
]


def get_users_by_roles(roles):
	users = set()
	for role in roles or []:
		if not role or role == "All":
			continue
		for user in frappe.get_all(
			"Has Role",
			filters={"parenttype": "User", "role": role},
			pluck="parent",
		):
			if not user or user in ("Guest", "Administrator"):
				continue
			if frappe.db.get_value("User", user, "enabled"):
				users.add(user)
	return list(users)


def notify_users(doc, roles, subject, message, skip_session_user=True):
	notify_user_list(
		doc,
		get_users_by_roles(roles),
		subject,
		message,
		skip_session_user=skip_session_user,
	)


def notify_user_list(doc, users, subject, message, skip_session_user=True):
	"""Desk bell (Notification Log) and mobile in-app + push (PWA Notification)."""
	plain = _plain_text(message) or subject
	session_user = frappe.session.user if frappe.session else None

	for user in dict.fromkeys(users or []):
		if not user or user in ("Guest", "Administrator"):
			continue
		if skip_session_user and user == session_user:
			continue
		_create_notification_log(user, doc, subject, message or plain)
		_create_pwa_notification(user, doc, plain)


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
		frappe.log_error(title=f"HR Request Email: {doc.name}", message=frappe.get_traceback())


def ensure_pwa_notification_access():
	"""Let HR roles read and mark mobile notifications. Employee can already read them."""
	if not frappe.db.exists("DocType", "PWA Notification"):
		return

	from frappe.permissions import add_permission, update_permission_property

	for role in PWA_ACCESS_ROLES:
		if not frappe.db.exists("Role", role):
			continue
		add_permission("PWA Notification", role, 0)
		update_permission_property("PWA Notification", role, 0, "read", 1)
		update_permission_property("PWA Notification", role, 0, "write", 1)


def _create_notification_log(user, doc, subject, message):
	try:
		notification = frappe.new_doc("Notification Log")
		notification.for_user = user
		notification.type = "Alert"
		notification.document_type = doc.doctype
		notification.document_name = doc.name
		notification.subject = subject
		notification.email_content = message
		if notification.meta.has_field("from_user") and frappe.session.user not in ("Guest",):
			notification.from_user = frappe.session.user
		notification.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(title=f"HR Request Notification: {doc.name}", message=frappe.get_traceback())


def _create_pwa_notification(user, doc, message):
	if not frappe.db.exists("DocType", "PWA Notification"):
		return

	try:
		notification = frappe.new_doc("PWA Notification")
		notification.to_user = user
		notification.message = message
		notification.reference_document_type = doc.doctype
		notification.reference_document_name = doc.name
		notification.read = 0
		if frappe.session.user and frappe.session.user != "Guest":
			notification.from_user = frappe.session.user
		notification.insert(ignore_permissions=True)
		_refetch_mobile_notifications(user)
	except Exception:
		frappe.log_error(title=f"HR Push Notification: {doc.name}", message=frappe.get_traceback())


def _refetch_mobile_notifications(user):
	try:
		import hrms

		hrms.refetch_resource("hrms:notifications", user)
		hrms.refetch_resource("hrms:unread_notifications_count", user)
	except Exception:
		pass


def _plain_text(value):
	if not value:
		return ""
	text = re.sub(r"<[^>]+>", " ", str(value))
	return re.sub(r"\s+", " ", text).strip()
