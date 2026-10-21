frappe.ui.form.on("Stock Consumption", {

    // =========================================================
    // SETUP
    // =========================================================

    setup(frm) {

        // =====================================================
        // WAREHOUSE FILTER
        // =====================================================

        frm.set_query("warehouse", () => {

            return {
                filters: {
                    company: frm.doc.company
                }
            };

        });


        // =====================================================
        // CHILD TABLE EXPENSE ACCOUNT FILTER
        // =====================================================

        frm.set_query(
            "expense_account",
            "items",
            () => {

                return {
                    filters: {
                        company: frm.doc.company,
                        account_type: "Stock Adjustment",
                        is_group: 0
                    }
                };

            }
        );


        // =====================================================
        // BATCH FILTER
        // =====================================================

        frm.set_query(
            "batch_no",
            "items",
            (doc, cdt, cdn) => {

                let row = locals[cdt][cdn];

                return {
                    filters: {
                        item: row.item_code
                    }
                };

            }
        );

    },


    // =========================================================
    // REFRESH
    // =========================================================

    refresh(frm) {

        toggle_employee(frm);


        // =====================================================
        // VIEW BUTTONS
        // =====================================================

        if (frm.doc.docstatus === 1) {

            frm.add_custom_button(
                "Stock Ledger",
                () => {

                    frappe.route_options = {
                        voucher_no: frm.doc.name
                    };

                    frappe.set_route(
                        "query-report",
                        "Stock Ledger"
                    );

                },
                "View"
            );

            frm.add_custom_button(
                "Accounting Ledger",
                () => {

                    frappe.route_options = {
                        voucher_no: frm.doc.name
                    };

                    frappe.set_route(
                        "query-report",
                        "General Ledger"
                    );

                },
                "View"
            );

        }

    },


    // =========================================================
    // CONSUMPTION TYPE
    // =========================================================

    consumption_type(frm) {

        toggle_employee(frm);

    }

});


// =============================================================
// CHILD TABLE
// =============================================================

frappe.ui.form.on(
    "Stock Consumption Item",
    {

        // =====================================================
        // ITEM CODE
        // =====================================================

        item_code(frm, cdt, cdn) {

            let row = locals[cdt][cdn];

            if (!row.item_code) return;

            if (!frm.doc.warehouse) {

                frappe.msgprint(
                    "Please select warehouse first"
                );

                return;

            }

            frappe.call({

                method:
                    "ebs_custom.ebs_custom.doctype.stock_consumption.stock_consumption.get_item_details",

                args: {

                    item_code: row.item_code,

                    warehouse: frm.doc.warehouse,

                    company: frm.doc.company

                },

                callback: function(r) {

                    if (!r.message) return;

                    let data = r.message;


                    // =========================================
                    // ITEM NAME
                    // =========================================

                    frappe.model.set_value(
                        cdt,
                        cdn,
                        "item_name",
                        data.item_name
                    );


                    // =========================================
                    // UOM
                    // =========================================

                    frappe.model.set_value(
                        cdt,
                        cdn,
                        "uom",
                        data.stock_uom
                    );


                    // =========================================
                    // VALUATION RATE
                    // =========================================

                    frappe.model.set_value(
                        cdt,
                        cdn,
                        "valuation_rate",
                        data.valuation_rate
                    );


                    // =========================================
                    // EXPENSE ACCOUNT
                    // =========================================

                    let expense_account =
                        row.expense_account
                        || get_common_expense_account(frm)
                        || data.expense_account;

                    frappe.model.set_value(
                        cdt,
                        cdn,
                        "expense_account",
                        expense_account
                    );


                    // =========================================
                    // CALCULATE ROW
                    // =========================================

                    calculate_row(
                        frm,
                        cdt,
                        cdn
                    );

                }

            });

        },


        // =====================================================
        // EXPENSE ACCOUNT
        // =====================================================

        expense_account(frm, cdt, cdn) {

            let row = locals[cdt][cdn];

            if (!row.expense_account) return;


            // ================================================
            // APPLY SAME ACCOUNT TO ALL ITEMS
            // ================================================

            (frm.doc.items || []).forEach((item) => {

                if (item.name !== row.name) {

                    frappe.model.set_value(
                        item.doctype,
                        item.name,
                        "expense_account",
                        row.expense_account
                    );

                }

            });

        },


        // =====================================================
        // QTY
        // =====================================================

        qty(frm, cdt, cdn) {

            calculate_row(
                frm,
                cdt,
                cdn
            );

        },


        // =====================================================
        // VALUATION RATE
        // =====================================================

        valuation_rate(frm, cdt, cdn) {

            calculate_row(
                frm,
                cdt,
                cdn
            );

        },


        // =====================================================
        // REMOVE ITEM
        // =====================================================

        items_remove(frm) {

            calculate_totals(frm);

        }

    }
);


// =============================================================
// GET COMMON EXPENSE ACCOUNT
// =============================================================

function get_common_expense_account(frm) {

    let account = null;

    (frm.doc.items || []).forEach((row) => {

        if (
            row.expense_account
            && !account
        ) {

            account = row.expense_account;

        }

    });

    return account;

}


// =============================================================
// ROW CALCULATION
// =============================================================

function calculate_row(
    frm,
    cdt,
    cdn
) {

    let row = locals[cdt][cdn];

    row.amount =
        flt(row.qty)
        * flt(row.valuation_rate);

    refresh_field("items");

    calculate_totals(frm);

}


// =============================================================
// TOTALS
// =============================================================

function calculate_totals(frm) {

    let total_qty = 0;

    let total_amount = 0;

    (frm.doc.items || []).forEach((row) => {

        total_qty += flt(row.qty);

        total_amount += flt(row.amount);

    });

    frm.set_value(
        "total_qty",
        total_qty
    );

    frm.set_value(
        "total_amount",
        total_amount
    );

}


// =============================================================
// EMPLOYEE TOGGLE
// =============================================================

function toggle_employee(frm) {

    if (
        frm.doc.consumption_type
        === "Employee Meal"
    ) {

        frm.set_df_property(
            "employee",
            "reqd",
            1
        );

    } else {

        frm.set_df_property(
            "employee",
            "reqd",
            0
        );

    }

}