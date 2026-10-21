import frappe

from frappe import _
from frappe.utils import flt, nowtime

from erpnext.controllers.stock_controller import StockController
from erpnext.stock.stock_ledger import make_sl_entries
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.stock import get_warehouse_account_map


class StockConsumption(StockController):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from ebs_custom.ebs_custom.doctype.stock_consumption_item.stock_consumption_item import StockConsumptionItem
        from frappe.types import DF

        amended_from: DF.Link | None
        company: DF.Link
        consumption_type: DF.Link | None
        cost_center: DF.Link | None
        custom_branch: DF.Link
        department: DF.Link | None
        employee: DF.Link
        items: DF.Table[StockConsumptionItem]
        naming_series: DF.Literal["SC-.YYYY.-.#####"]
        posting_date: DF.Date
        posting_time: DF.Time | None
        project: DF.Link | None
        remarks: DF.SmallText | None
        total_amount: DF.Currency
        total_qty: DF.Float
        warehouse: DF.Link
    # end: auto-generated types

    # =========================================================
    # VALIDATE
    # =========================================================

    def validate(self):

        self.set_posting_time()

        self.validate_mandatory_fields()

        self.validate_items()

        self.calculate_totals()

    # =========================================================
    # ON SUBMIT
    # =========================================================

    def on_submit(self):

        self.make_stock_ledger_entries()

        self.make_gl_entries()

    # =========================================================
    # ON CANCEL
    # =========================================================

    def on_cancel(self):

        self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry")

        self.make_stock_ledger_entries()

        self.cancel_gl_entries()

    # =========================================================
    # PREVENT DELETE
    # =========================================================

    def on_trash(self):

        if self.docstatus == 1:

            frappe.throw(
                _("Submitted document cannot be deleted")
            )

    # =========================================================
    # POSTING TIME
    # =========================================================

    def set_posting_time(self):

        if not self.posting_time:

            self.posting_time = nowtime()

    # =========================================================
    # VALIDATE HEADER
    # =========================================================

    def validate_mandatory_fields(self):

        if not self.company:

            frappe.throw(_("Company is required"))

        if not self.warehouse:

            frappe.throw(_("Warehouse is required"))

        if not self.posting_date:

            frappe.throw(_("Posting Date is required"))

    # =========================================================
    # VALIDATE ITEMS
    # =========================================================

    def validate_items(self):

        if not self.items:

            frappe.throw(_("Items are required"))

        for row in self.items:

            if not row.item_code:

                frappe.throw(
                    _("Item missing in row {0}").format(row.idx)
                )

            if flt(row.qty) <= 0:

                frappe.throw(
                    _("Qty must be greater than zero in row {0}").format(row.idx)
                )

    # =========================================================
    # CALCULATE TOTALS
    # =========================================================

    def calculate_totals(self):

        self.total_qty = 0
        self.total_amount = 0

        for row in self.items:

            valuation_rate = 0

            if self.warehouse:

                valuation_rate = frappe.db.get_value(
                    "Bin",
                    {
                        "item_code": row.item_code,
                        "warehouse": self.warehouse
                    },
                    "valuation_rate"
                ) or 0

            if not valuation_rate:

                valuation_rate = frappe.db.get_value(
                    "Item",
                    row.item_code,
                    "valuation_rate"
                ) or 0

            row.valuation_rate = flt(valuation_rate)

            row.amount = (
                flt(row.qty)
                * flt(row.valuation_rate)
            )

            self.total_qty += flt(row.qty)

            self.total_amount += flt(row.amount)

    # =========================================================
    # STOCK LEDGER ENTRIES
    # =========================================================

    def make_stock_ledger_entries(self):

        sl_entries = []

        for row in self.items:

            sle = frappe._dict({

                "item_code": row.item_code,

                "warehouse": self.warehouse,

                "posting_date": self.posting_date,

                "posting_time": self.posting_time,

                "voucher_type": self.doctype,

                "voucher_no": self.name,

                "voucher_detail_no": row.name,

                "actual_qty": (
                    -flt(row.qty)
                    if self.docstatus == 1
                    else flt(row.qty)
                ),

                "stock_uom": row.uom,

                "incoming_rate": 0,

                "valuation_rate": flt(row.valuation_rate),

                "company": self.company,

                "batch_no": row.batch_no,

                "serial_no": row.serial_no,

                "project": self.project,

                "custom_branch": getattr(self, "custom_branch", None),

                "employee": getattr(self, "employee", None),

                "department": getattr(self, "department", None),

                "consumption_type": getattr(self, "consumption_type", None),

                "is_cancelled": 1 if self.docstatus == 2 else 0

            })

            sl_entries.append(sle)

        make_sl_entries(
            sl_entries,
            allow_negative_stock=True
        )

    # =========================================================
    # GL ENTRIES
    # =========================================================

    def make_gl_entries(self):

        gl_entries = []

        warehouse_account_data = (
            get_warehouse_account_map(
                self.company
            ).get(self.warehouse)
        )

        if not warehouse_account_data:

            frappe.throw(
                _("Warehouse Account Missing for {0}").format(
                    self.warehouse
                )
            )

        warehouse_account = warehouse_account_data.account

        for row in self.items:

            amount = flt(row.amount)

            if not amount:

                continue

            expense_account = row.expense_account

            # =============================================
            # AUTO FETCH EXPENSE ACCOUNT
            # =============================================

            if not expense_account:

                expense_account = frappe.db.get_value(
                    "Item Default",
                    {
                        "parent": row.item_code,
                        "company": self.company
                    },
                    "expense_account"
                )

            if not expense_account:

                frappe.throw(
                    _("Expense Account Missing for Item {0}").format(
                        row.item_code
                    )
                )

            # =============================================
            # EXPENSE DEBIT
            # =============================================

            gl_entries.append(

                self.get_gl_dict({

                    "account": expense_account,

                    "against": warehouse_account,

                    "debit": amount,

                    "debit_in_account_currency": amount,

                    "cost_center": self.cost_center,

                    "project": self.project,

                    "remarks": self.remarks

                })

            )

            # =============================================
            # STOCK CREDIT
            # =============================================

            gl_entries.append(

                self.get_gl_dict({

                    "account": warehouse_account,

                    "against": expense_account,

                    "credit": amount,

                    "credit_in_account_currency": amount,

                    "cost_center": self.cost_center,

                    "project": self.project,

                    "remarks": self.remarks

                })

            )

        if gl_entries:

            make_gl_entries(
                gl_entries,
                cancel=False,
                merge_entries=False
            )

    # =========================================================
    # CANCEL GL ENTRIES
    # =========================================================

    def cancel_gl_entries(self):

        # make_gl_entries(

        #     gl_map=[],

        #     cancel=True,

        #     adv_adj=False,

        #     merge_entries=False,

        #     update_outstanding="No",

        #     from_repost=False
        # )
        gl_entries = frappe.get_all(
            "GL Entry",
            filters={
                "voucher_type": self.doctype,
                "voucher_no": self.name,
                "is_cancelled": 0
            },
            fields=["name"]
        )

        for gle in gl_entries:

            doc = frappe.get_doc("GL Entry", gle.name)

            doc.flags.ignore_validate_update_after_submit = True
            doc.db_set("is_cancelled", 1)


# =============================================================
# ITEM DETAILS API
# =============================================================

@frappe.whitelist()
def get_item_details(
    item_code,
    warehouse=None,
    company=None
):

    item = frappe.get_cached_doc(
        "Item",
        item_code
    )

    valuation_rate = 0

    if warehouse:

        valuation_rate = frappe.db.get_value(
            "Bin",
            {
                "item_code": item_code,
                "warehouse": warehouse
            },
            "valuation_rate"
        ) or 0

    expense_account = None

    if company:

        expense_account = frappe.db.get_value(
            "Item Default",
            {
                "parent": item_code,
                "company": company
            },
            "expense_account"
        )

    return {

        "item_name": item.item_name,

        "stock_uom": item.stock_uom,

        "valuation_rate": valuation_rate,

        "expense_account": expense_account

    }