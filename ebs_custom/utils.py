import frappe
from frappe import _
from frappe.model.naming import getseries

def set_domain_item_code(doc, method):
    # Agar record naya nahi hai toh bypass karein
    if not doc.is_new():
        return

    # At least one domain is required
    if not doc.get("custom_item_domains"):
        frappe.throw(_("Please add at least one Item Domain."))

    primary_domain = None

    # Find the selected Primary Domain
    for row in doc.custom_item_domains:
        if row.get("primary_domain"):
            if primary_domain:
                frappe.throw(_("Only one Item Domain can be marked as Primary."))
            primary_domain = row

    # No Primary Domain selected
    if not primary_domain:
        frappe.throw(_("Please select one Primary Domain."))

    # Get Domain Code
    domain_code = (primary_domain.get("domain_code") or "").strip()

    if not domain_code:
        frappe.throw(_("Domain Code not found for the selected Domain."))

    # Generate Item Code using getseries
    series_key = f"{domain_code}-"
    series = getseries(series_key, 4)
    generated_code = f"{series_key}{series}"

    # ZAROORI: ERPNext ki primary key (doc.name) aur field dono ko change karna lazmi hai
    doc.name = generated_code
    doc.item_code = generated_code
