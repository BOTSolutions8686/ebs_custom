import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


# =====================================================
# UTILITIES
# =====================================================

def field_exists(doctype, fieldname):
    return frappe.get_meta(doctype).has_field(fieldname)


def create_field_if_missing(doctype, field):
    if not field_exists(doctype, field.get("fieldname")):
        create_custom_fields({doctype: [field]})
        frappe.logger().info(f"Created field {field['fieldname']} in {doctype}")


def delete_field(doctype, fieldname):
    field = frappe.db.get_value(
        "Custom Field",
        {"dt": doctype, "fieldname": fieldname},
        "name"
    )
    if field:
        frappe.delete_doc("Custom Field", field)
        frappe.logger().info(f"Deleted field {fieldname} from {doctype}")


# =====================================================
# FIELD DEFINITIONS
# =====================================================

def get_fields():
    return {
        "branch_field": {
            "fieldname": "custom_branch",
            "fieldtype": "Link",
            "label": "Branch",
            "options": "Branch",
            "module": "Custom"
        },
        "invoice_number_field": {
            "fieldname": "invoice_number",
            "fieldtype": "Data",
            "label": "Invoice Number",
            "module": "Custom"
        },
        "employee_field": {
            "fieldname": "employee",
            "fieldtype": "Link",
            "label": "Employee",
            "options": "Employee",
            "module": "Custom"
        },

        "department_field": {
            "fieldname": "department",
            "fieldtype": "Link",
            "label": "Department",
            "options": "Department",
            "module": "Custom"
        },

        "consumption_type_field": {
            "fieldname": "consumption_type",
            "fieldtype": "Link",
            "label": "Consumption Type",
            "options": "Consumption Item",
            "module": "Custom"
        },
    }


# =====================================================
# MAIN SETUP (INSTALL)
# =====================================================

def setup_custom_fields():

    fields = get_fields()

    branch_field = fields["branch_field"]
    invoice_number_field = fields["invoice_number_field"]
    employee_field = fields["employee_field"]
    department_field = fields["department_field"]
    consumption_type_field = fields["consumption_type_field"]

    create_field_if_missing("Sales Invoice", {
        **branch_field,
        "insert_after": "customer"
    })

    create_field_if_missing("Expense Claim", {
        **branch_field,
        "insert_after": "company"
    })
    create_field_if_missing("Purchase Invoice", {
        **branch_field,
        "insert_after": "company"
    })
    create_field_if_missing("Purchase Receipt", {
        **branch_field,
        "insert_after": "company"
    })
    create_field_if_missing("Delivery Note", {
        **branch_field,
        "insert_after": "company"
    })
    create_field_if_missing("Expense Claim", {
        **branch_field,
        "insert_after": "company"
    })

    create_field_if_missing("Expense Claim Detail", {
        **invoice_number_field,
        "insert_after": "approval_status"
    })

    create_field_if_missing("Journal Entry", {
        **branch_field,
        "insert_after": "voucher_type"
    })

    create_field_if_missing("Payment Entry", {
        **branch_field,
        "insert_after": "party_name"
    })

    create_field_if_missing("Stock Entry", {
        **branch_field,
        "insert_after": "stock_entry_type"
    })

    create_field_if_missing("Material Request", {
        **branch_field,
        "insert_after": "material_request_type"
    })

    create_field_if_missing("GL Entry", {
        **branch_field,
        "insert_after": "project"
    })

    create_field_if_missing("Stock Ledger Entry", {
        **branch_field,
        "insert_after": "project"
    })
    create_field_if_missing("GL Entry", {
        **employee_field,
        "insert_after": "custom_branch"
    })

    create_field_if_missing("GL Entry", {
        **department_field,
        "insert_after": "employee"
    })

    create_field_if_missing("GL Entry", {
        **consumption_type_field,
        "insert_after": "department"
    })
    create_field_if_missing("Stock Ledger Entry", {
        **employee_field,
        "insert_after": "custom_branch"
    })

    create_field_if_missing("Stock Ledger Entry", {
        **department_field,
        "insert_after": "employee"
    })

    create_field_if_missing("Stock Ledger Entry", {
        **consumption_type_field,
        "insert_after": "department"
    })

    create_field_if_missing("Employee Checkin", {
        "fieldname": "approval_status",
        "fieldtype": "Select",
        "label": "Approval Status",
        "options": "Pending\nApproved\nRejected",
        "default": "Pending",
        "insert_after": "log_type",
    })

    create_field_if_missing("Employee", {
        "fieldname": "custom_current_salary",
        "fieldtype": "Currency",
        "label": "Current Salary",
        "insert_after": "custom_branch",
    })


# =====================================================
# REMOVE FIELDS (UNINSTALL)
# =====================================================

def remove_custom_fields():

    fields = get_fields()

    branch_field = fields["branch_field"]["fieldname"]
    invoice_number_field = fields["invoice_number_field"]["fieldname"]
    employee_field = fields["employee_field"]
    department_field = fields["department_field"]
    consumption_type_field = fields["consumption_type_field"]

    doctypes_with_branch = [
        "Sales Invoice",
        "Expense Claim",
        "Journal Entry",
        "Payment Entry",
        "Stock Entry",
        "Material Request",
        "GL Entry",
        "Stock Ledger Entry"
    ]

    # Remove branch field
    for dt in doctypes_with_branch:
        delete_field(dt, branch_field)

    # Remove invoice number field
    delete_field("Expense Claim", invoice_number_field)

    delete_field("Employee Checkin", "approval_status")
    delete_field("Employee", "custom_current_salary")


# =====================================================
# RUN (INSTALL)
# =====================================================

def execute():
    setup_custom_fields()