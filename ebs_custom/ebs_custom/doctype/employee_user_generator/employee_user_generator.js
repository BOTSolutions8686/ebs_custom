// Copyright (c) 2026, EBS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee User Generator", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Get Employees"), () => {
				get_employees(frm);
			}).addClass("btn-primary");

			frm.add_custom_button(__("Create Users"), () => {
				create_users_click(frm);
			}).addClass("btn-primary");
		} else {
			frm.dashboard.set_headline(
				__("Save the document first, then click Get Employees.")
			);
		}

		bind_select_header(frm);
	},

	company(frm) {
		if (frm.doc.employee_list && frm.doc.employee_list.length) {
			frappe.confirm(
				__("Clear current employee list because Company changed?"),
				() => {
					frm.clear_table("employee_list");
					frm.refresh_field("employee_list");
				}
			);
		}
	},
});

frappe.ui.form.on("Employee User Generator Item", {
	employee(frm, cdt, cdn) {
		const row = locals[cdt][cdn];

		if (!row.employee) {
			frappe.model.set_value(cdt, cdn, "employee_name", "");
			frappe.model.set_value(cdt, cdn, "select", 0);
			frappe.model.set_value(cdt, cdn, "status", "Pending");
			frappe.model.set_value(cdt, cdn, "message", "");
			frappe.model.set_value(cdt, cdn, "user", "");
			frappe.model.set_value(cdt, cdn, "password", "");
			return;
		}

		frappe.db.get_value(
			"Employee",
			row.employee,
			["employee_name", "user_id"],
			(r) => {
				if (!r) return;

				frappe.model.set_value(cdt, cdn, "employee_name", r.employee_name || "");

				if (r.user_id) {
					frappe.model.set_value(cdt, cdn, "select", 1);
					frappe.model.set_value(cdt, cdn, "status", "Created");
					frappe.model.set_value(cdt, cdn, "user", r.user_id);
					frappe.model.set_value(
						cdt,
						cdn,
						"message",
						__("User already linked: {0}", [r.user_id])
					);
				} else {
					frappe.model.set_value(cdt, cdn, "select", 0);
					frappe.model.set_value(cdt, cdn, "status", "Pending");
					frappe.model.set_value(cdt, cdn, "user", "");
					frappe.model.set_value(cdt, cdn, "password", "");
					frappe.model.set_value(cdt, cdn, "message", "");
				}
			}
		);
	},

	select(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const MAX_SELECTABLE = 20;

		if (cint(row.select)) {
			const selected_count = (frm.doc.employee_list || []).filter(
				(r) => cint(r.select)
			).length;

			if (selected_count > MAX_SELECTABLE) {
				// Revert this row's checkbox and warn the user
				frappe.model.set_value(cdt, cdn, "select", 0);
				frappe.show_alert({
					message: __("You can select a maximum of {0} employees at a time.", [MAX_SELECTABLE]),
					indicator: "orange",
				});
				return;
			}
		}

		if (row.select && row.status === "Skipped" && row.user) {
			if (row.__skip_msg_shown) return;
			row.__skip_msg_shown = true;

			const msg_dialog = frappe.msgprint(
				__(
					"User already exists for this employee ({0}). It will be skipped by Create Users, but you can still update its password.",
					[row.user]
				)
			);

			// Auto-close this message after 2 seconds
			setTimeout(() => {
				if (msg_dialog && msg_dialog.hide) {
					msg_dialog.hide();
				}
			}, 2000);
		} else {
			row.__skip_msg_shown = false;
		}
	},

	update_password(frm, cdt, cdn) {
		const row = locals[cdt][cdn];

		if (!row.user) {
			frappe.msgprint(__("This row has no linked User."));
			return;
		}

		if (frappe.__epwd_dialog_open) {
			return;
		}
		frappe.__epwd_dialog_open = true;

		let d = new frappe.ui.Dialog({
			title: __("Update Password"),
			fields: [
				{
					fieldname: "new_password",
					label: __("New Password"),
					fieldtype: "Password",
					reqd: 1,
					description: __("This password will be set for user {0}.", [row.user]),
				},
			],
			primary_action_label: __("Update"),
			primary_action(values) {
				d.get_primary_btn().prop("disabled", true);

				frappe.call({
					method:
						"ebs_custom.ebs_custom.doctype.employee_user_generator.employee_user_generator.update_password",
					args: {
						name: frm.doc.name,
						rows: [row.name],
						new_password: values.new_password,
					},
					freeze: true,
					freeze_message: __("Updating password..."),
					callback(r) {
						frappe.dom.unfreeze();

						frappe.model.set_value(cdt, cdn, "password", values.new_password);
						frappe.model.set_value(cdt, cdn, "select", 0);
						frappe.model.set_value(
							cdt,
							cdn,
							"message",
							r.message || __("Password updated successfully")
						);
						frm.refresh_field("employee_list");

						frappe.show_alert({
							message: __("Password updated for employee {0}", [row.employee]),
							indicator: "green",
						});
						d.hide();

						frm.reload_doc();

					},
					error() {
						frappe.dom.unfreeze();
						d.get_primary_btn().prop("disabled", false);
						frappe.msgprint(__("Could not update password. Please check Error Log."));
					},
				});
			},
		});

		// Reliable single point of cleanup: fires whether the dialog is closed
		// via the primary action, the X button, ESC, or clicking outside.
		d.$wrapper.on("hidden.bs.modal", () => {
			frappe.__epwd_dialog_open = false;
			d.$wrapper.remove();
			d = null;
		});

		d.show();
	},
});

function get_employees(frm) {
	frappe.call({
		method:
			"ebs_custom.ebs_custom.doctype.employee_user_generator.employee_user_generator.get_employees",
		args: {
			docname: frm.doc.name,
		},
		freeze: true,
		freeze_message: __("Loading employees..."),
		callback(r) {
			frm.reload_doc();

			if (r.message) {
				frappe.show_alert({
					message: r.message,
					indicator: "green",
				});
			}
		},
	});
}

function create_users_click(frm) {
	const rows = frm.doc.employee_list || [];
	const selected = rows.filter((r) => Number(r.select) === 1);
	const has_stale_created_rows = rows.some((r) => r.status === "Created");

	if (!selected.length && !has_stale_created_rows) {
		frappe.msgprint(
			__("Please check at least one Pending employee, then click Create Users.")
		);
		return;
	}

	const confirm_message = selected.length
		? __("Create users for {0} selected employee(s)?", [selected.length])
		: __("No new employees selected. Refresh the status of already-linked employees?");

	frappe.confirm(
		confirm_message,
		() => {
			frm.save()
				.then(() => {
					return frappe.call({
						method:
							"ebs_custom.ebs_custom.doctype.employee_user_generator.employee_user_generator.create_users",
						args: {
							name: frm.doc.name,
						},
						freeze: true,
						freeze_message: __("Creating users..."),
					});
				})
				.then((r) => {
					return frm.reload_doc().then(() => r);
				})
				.then((r) => {
					if (r && r.message) {
						frappe.show_alert({
							message: r.message,
							indicator: "green",
						});
					}
				})
				.catch(() => {
					frappe.msgprint(__("Could not create users. Please check Error Log."));
				});
		}
	);
}

function bind_select_header(frm) {
	const BATCH_SIZE = 20;
	const BATCH_STATUSES = ["Pending", "Failed"];
	const header_selector = '.grid-heading-row [data-fieldname="select"]';

	frappe.dom.set_style(
		`.grid-heading-row [data-fieldname="select"] { cursor: pointer; }`,
		"epg-select-header-style"
	);

	const wrapper = frm.fields_dict.employee_list.grid.wrapper;

	// Delegated + namespaced, so it survives grid re-renders and is not bound twice
	wrapper.off(".epgselect");

	wrapper.on("mouseenter.epgselect", header_selector, function () {
		$(this).attr(
			"title",
			__("Click to select {0} Pending/Failed employees", [BATCH_SIZE])
		);
	});

	wrapper.on("click.epgselect", header_selector, function () {
		const rows = frm.doc.employee_list || [];

		if (!rows.length) {
			frappe.msgprint(__("No employees in the list. Click Get Employees first."));
			return;
		}

		// Second click on header clears the selection
		if (rows.some((r) => cint(r.select))) {
			rows.forEach((r) => (r.select = 0));
			frm.refresh_field("employee_list");
			frm.dirty();
			return;
		}

		const eligible = rows.filter((r) => BATCH_STATUSES.includes(r.status));

		if (!eligible.length) {
			frappe.msgprint(__("No Pending or Failed employees available to select."));
			return;
		}

		const to_select = eligible.slice(0, BATCH_SIZE);
		to_select.forEach((r) => (r.select = 1));
		frm.refresh_field("employee_list");
		frm.dirty();

		let msg = __("{0} employees selected.", [to_select.length]);
		if (eligible.length > BATCH_SIZE) {
			msg +=
				" " +
				__("Limit is {0} per run; run Create Users again for the remaining.", [BATCH_SIZE]);
		}
		frappe.show_alert({ message: msg, indicator: "green" });
	});
}