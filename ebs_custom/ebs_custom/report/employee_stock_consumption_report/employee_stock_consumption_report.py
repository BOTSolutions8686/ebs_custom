# employee_stock_consumption_report.p
import frappe
from frappe import _
from frappe.utils import flt


# =========================================================
# EXECUTE
# =========================================================

def execute(filters=None):

    columns = get_columns()

    data = get_data(filters)

    return columns, data


# =========================================================
# COLUMNS
# =========================================================

def get_columns():

    return [

        {
            "label": _("Employee"),
            "fieldname": "employee",
            "fieldtype": "Data",
            "width": 250
        },

        {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Data",
            "width": 180
        },

        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 110
        },

        {
            "label": _("Voucher"),
            "fieldname": "voucher_no",
            "fieldtype": "Link",
            "options": "Stock Consumption",
            "width": 180
        },

        {
            "label": _("Consumption Type"),
            "fieldname": "consumption_type",
            "fieldtype": "Data",
            "width": 180
        },

        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 180
        },

        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 220
        },

        {
            "label": _("Warehouse"),
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 180
        },

        {
            "label": _("Qty"),
            "fieldname": "qty",
            "fieldtype": "Float",
            "width": 120
        },

        {
            "label": _("Valuation Rate"),
            "fieldname": "valuation_rate",
            "fieldtype": "Currency",
            "width": 140
        },

        {
            "label": _("Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 140
        }

    ]


# =========================================================
# DATA
# =========================================================

def get_data(filters):

    conditions = get_conditions(filters)

    records = frappe.db.sql(
        f"""
        SELECT

            sc.name as voucher_no,
            sc.posting_date,
            sc.employee,
            emp.employee_name,
            sc.department,
            sc.consumption_type,
            sc.warehouse,

            sci.item_code,
            sci.item_name,
            sci.qty,
            sci.valuation_rate,
            sci.amount

        FROM
            `tabStock Consumption` sc

        INNER JOIN
            `tabStock Consumption Item` sci
            ON sci.parent = sc.name

        LEFT JOIN
            `tabEmployee` emp
            ON emp.name = sc.employee

        WHERE
            sc.docstatus = 1
            {conditions}

        ORDER BY
            sc.employee,
            sc.posting_date,
            sc.name

        """,
        filters,
        as_dict=True
    )

    data = []

    employee_map = {}

    # =====================================================
    # GROUP TOTALS
    # =====================================================

    for row in records:

        employee = row.employee or "No Employee"

        if employee not in employee_map:

            employee_map[employee] = {

                "employee_name":
                    row.employee_name or employee,

                "department":
                    row.department,

                "total_qty": 0,

                "total_amount": 0
            }

        employee_map[employee]["total_qty"] += flt(row.qty)

        employee_map[employee]["total_amount"] += flt(row.amount)

    # =====================================================
    # TREE DATA
    # =====================================================

    added_parents = set()

    for row in records:

        employee = row.employee or "No Employee"

        # =================================================
        # PARENT ROW
        # =================================================

        if employee not in added_parents:

            summary = employee_map[employee]

            data.append({

                "employee":
                    f"{employee} - {summary['employee_name']}",

                "department":
                    summary["department"],

                "qty":
                    summary["total_qty"],

                "amount":
                    summary["total_amount"],

                "indent": 0,

                "is_group": 1,

                "bold": 1

            })

            added_parents.add(employee)

        # =================================================
        # CHILD ROW
        # =================================================

        data.append({

            "employee": "",

            "department": row.department,

            "posting_date": row.posting_date,

            "voucher_no": row.voucher_no,

            "consumption_type": row.consumption_type,

            "item_code": row.item_code,

            "item_name": row.item_name,

            "warehouse": row.warehouse,

            "qty": row.qty,

            "valuation_rate": row.valuation_rate,

            "amount": row.amount,

            "indent": 1

        })

    return data


# =========================================================
# CONDITIONS
# =========================================================

def get_conditions(filters):

    conditions = ""

    if filters.get("company"):

        conditions += """
            AND sc.company = %(company)s
        """

    if filters.get("from_date"):

        conditions += """
            AND sc.posting_date >= %(from_date)s
        """

    if filters.get("to_date"):

        conditions += """
            AND sc.posting_date <= %(to_date)s
        """

    if filters.get("employee"):

        conditions += """
            AND sc.employee = %(employee)s
        """

    if filters.get("department"):

        conditions += """
            AND sc.department = %(department)s
        """

    if filters.get("consumption_type"):

        conditions += """
            AND sc.consumption_type = %(consumption_type)s
        """

    if filters.get("warehouse"):

        conditions += """
            AND sc.warehouse = %(warehouse)s
        """

    if filters.get("custom_branch"):

        conditions += """
            AND sc.custom_branch = %(custom_branch)s
        """

    return conditions
