app_name = "ebs_custom"
app_title = "Ebs Custom"
app_publisher = "Arslan"
app_description = "System customizatiins for branches"
app_email = "malikarslan000009@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

fixtures = [
    {
        "dt": "Custom Field", "filters": [
            [
                "name", "in", [
                    "Employee-custom_branch",
                    "Employee Checkin-approval_status",
                    "Employee-custom_current_salary",
                    "Item-custom_section_break_3ieq4",
                    "Item-custom_item_domains"
                ]
            ]
        ]
    },
    {
        "dt": "Print Format", "filters": [
            [
                "name", "in", [
                    "Salary Statement Request Fromat",
                ]
            ]
        ]
    },
    # {
    #     "dt": "Workflow", "filters": [
    #         [
    #             "name", "in", [
    #                 "Offboarding Interview Workflow",
    #                 "Resignation Request Workflow",
    #                 "Salary Statement Request Workflow",
    #                 "Shift Transfer Request Workflow",
    #                 "Branch Transfer Request Workflow",
    #                 "Loan Approval Multi Level",
    #                 "Leave Approval Multi Level"
    #             ]
    #         ]
    #     ],   
    # },
    {
        "dt": "Property Setter",
        "filters": [
            ["doc_type", "=", "Item"],
            # ["field_name", "=", "item_code"]
        ]
    },
    {
        "dt": "Client Script",
        "filters": [
            ["dt", "=", "Item"]
        ]
    }
]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "ebs_custom",
# 		"logo": "/assets/ebs_custom/logo.png",
# 		"title": "Ebs Custom",
# 		"route": "/ebs_custom",
# 		"has_permission": "ebs_custom.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/ebs_custom/css/ebs_custom.css"
# app_include_js = "/assets/ebs_custom/js/ebs_custom.js"

# include js, css files in header of web template
# web_include_css = "/assets/ebs_custom/css/ebs_custom.css"
# web_include_js = "/assets/ebs_custom/js/ebs_custom.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "ebs_custom/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
	"Branch Attendance Approval": "ebs_custom/doctype/branch_attendance_approval/branch_attendance_approval.js",
	"Salary Adjustment Request": "ebs_custom/doctype/salary_adjustment_request/salary_adjustment_request.js",
	"Promotion Request": "ebs_custom/doctype/promotion_request/promotion_request.js",
    "Employee User Generator": "ebs_custom/doctype/employee_user_generator/employee_user_generator.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "ebs_custom/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "ebs_custom.utils.jinja_methods",
# 	"filters": "ebs_custom.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "ebs_custom.install.before_install"
# after_install = "ebs_custom.install.after_install"
before_uninstall = "ebs_custom.customizations.fields_setup.remove_custom_fields"
after_install = "ebs_custom.install.after_install"
after_migrate = "ebs_custom.setup.after_migrate"

after_install = "ebs_custom.branding.after_install"
after_uninstall = "ebs_custom.branding.after_uninstall"

# Uninstallation
# ------------

# before_uninstall = "ebs_custom.uninstall.before_uninstall"
# after_uninstall = "ebs_custom.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "ebs_custom.utils.before_app_install"
# after_app_install = "ebs_custom.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "ebs_custom.utils.before_app_uninstall"
# after_app_uninstall = "ebs_custom.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ebs_custom.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

doc_events = {
    "GL Entry": {
        "before_insert": "ebs_custom.overrides.branch_logic.set_branch_in_gl",
        "before_save": "ebs_custom.overrides.branch_logic.set_branch_in_gl"
    },
    "Stock Ledger Entry": {
        "before_insert": "ebs_custom.overrides.branch_logic.set_branch_in_sle",
        "before_save": "ebs_custom.overrides.branch_logic.set_branch_in_gl"
    },
    "Employee Checkin": {
        "validate": "ebs_custom.attendance.events.attendance.validate_checkin",
    },
    "Branch Attendance Approval": {
        "on_update": "ebs_custom.attendance.events.attendance.on_branch_approval_update",
    },
    "Salary Adjustment Request": {
        "on_update": "ebs_custom.hr_requests.events.salary_promotion.on_hr_request_update",
    },
    "Promotion Request": {
        "on_update": "ebs_custom.hr_requests.events.salary_promotion.on_hr_request_update",
    },
    "Item": {
        "autoname": "ebs_custom.utils.set_domain_item_code"
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"ebs_custom.hr_requests.events.salary_promotion.apply_scheduled_hr_updates",
	],
}

# scheduler_events = {
# 	"all": [
# 		"ebs_custom.tasks.all"
# 	],
# 	"daily": [
# 		"ebs_custom.tasks.daily"
# 	],
# 	"hourly": [
# 		"ebs_custom.tasks.hourly"
# 	],
# 	"weekly": [
# 		"ebs_custom.tasks.weekly"
# 	],
# 	"monthly": [
# 		"ebs_custom.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "ebs_custom.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "ebs_custom.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "ebs_custom.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "ebs_custom.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["ebs_custom.utils.before_request"]
# after_request = ["ebs_custom.utils.after_request"]

# Job Events
# ----------
# before_job = ["ebs_custom.utils.before_job"]
# after_job = ["ebs_custom.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]


permission_query_conditions = {
	"Employee Complaint": "ebs_custom.hr_complaints.permissions.get_permission_query_conditions",
	"Resignation Request": "ebs_custom.employee_exit.permissions.get_resignation_query_conditions",
	"Offboarding Interview": "ebs_custom.employee_exit.permissions.get_offboarding_query_conditions",
}

has_permission = {
	"Employee Complaint": "ebs_custom.hr_complaints.permissions.has_permission",
	"Resignation Request": "ebs_custom.employee_exit.permissions.has_resignation_permission",
	"Offboarding Interview": "ebs_custom.employee_exit.permissions.has_offboarding_permission",
}

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"ebs_custom.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

