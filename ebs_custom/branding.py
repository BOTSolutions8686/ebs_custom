import frappe

def after_install():
    desk_logo = "/assets/ebs_custom/images/desk-logo.png"

    ns = frappe.get_single("Navbar Settings")
    ns.app_logo = desk_logo
    ns.save(ignore_permissions=True)

    # Commit changes to the database
    frappe.db.commit()

def after_uninstall():
    # Remove the custom navbar logo and revert to default
    ns = frappe.get_single("Navbar Settings")
    ns.app_logo = None
    ns.save(ignore_permissions=True)

    # Commit changes to the database
    frappe.db.commit()
