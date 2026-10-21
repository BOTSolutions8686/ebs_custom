import frappe


def get_source_doc(voucher_type, voucher_no):

    if not voucher_type or not voucher_no:
        return None

    try:
        return frappe.get_doc(voucher_type, voucher_no)

    except Exception:
        return None


# =====================================================
# GL ENTRY
# =====================================================

def set_branch_in_gl(doc, method):

    source_doc = get_source_doc(
        doc.voucher_type,
        doc.voucher_no
    )

    if not source_doc:
        return

    # =========================================
    # BRANCH
    # =========================================

    if hasattr(source_doc, "custom_branch"):

        doc.custom_branch = source_doc.custom_branch

    # =========================================
    # EMPLOYEE
    # =========================================

    if hasattr(source_doc, "employee"):

        doc.employee = source_doc.employee

    # =========================================
    # DEPARTMENT
    # =========================================

    if hasattr(source_doc, "department"):

        doc.department = source_doc.department

    # =========================================
    # CONSUMPTION TYPE
    # =========================================

    if hasattr(source_doc, "consumption_type"):

        doc.consumption_type = source_doc.consumption_type


# =====================================================
# STOCK LEDGER ENTRY
# =====================================================

def set_branch_in_sle(doc, method):

    source_doc = get_source_doc(
        doc.voucher_type,
        doc.voucher_no
    )

    if not source_doc:
        return

    # =========================================
    # BRANCH
    # =========================================

    if hasattr(source_doc, "custom_branch"):

        doc.custom_branch = source_doc.custom_branch

    # =========================================
    # EMPLOYEE
    # =========================================

    if hasattr(source_doc, "employee"):

        doc.employee = source_doc.employee

    # =========================================
    # DEPARTMENT
    # =========================================

    if hasattr(source_doc, "department"):

        doc.department = source_doc.department

    # =========================================
    # CONSUMPTION TYPE
    # =========================================

    if hasattr(source_doc, "consumption_type"):

        doc.consumption_type = source_doc.consumption_type