import frappe


def execute(filters=None):
    filters = frappe._dict(filters or {})

    columns = [
        {
            "label": "Activity Date",
            "fieldname": "activity_date",
            "fieldtype": "Datetime",
            "width": 160,
        },
        {
            "label": "User",
            "fieldname": "user",
            "fieldtype": "Link",
            "options": "User",
            "width": 180,
        },
        {
            "label": "Activity Type",
            "fieldname": "activity_type",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": "Reference DocType",
            "fieldname": "reference_doctype",
            "fieldtype": "Link",
            "options": "DocType",
            "width": 180,
        },
        {
            "label": "Reference Name",
            "fieldname": "reference_name",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Description",
            "fieldname": "description",
            "fieldtype": "Text",
            "width": 350,
        },
    ]

    comment_conditions = []
    activity_log_conditions = []
    file_conditions = []
    version_conditions = []

    # USER FILTER
    if filters.get("user"):
        comment_conditions.append(
            "COALESCE(c.comment_by, c.owner) = %(user)s"
        )

        activity_log_conditions.append(
            "COALESCE(al.user, al.owner) = %(user)s"
        )

        file_conditions.append(
            "f.owner = %(user)s"
        )

        version_conditions.append(
            "v.owner = %(user)s"
        )

    # FROM DATE FILTER
    if filters.get("from_date"):
        comment_conditions.append(
            "c.creation >= %(from_date)s"
        )

        activity_log_conditions.append(
            "al.communication_date >= %(from_date)s"
        )

        file_conditions.append(
            "f.creation >= %(from_date)s"
        )

        version_conditions.append(
            "v.creation >= %(from_date)s"
        )

    # TO DATE FILTER
    if filters.get("to_date"):
        comment_conditions.append(
            "c.creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)"
        )

        activity_log_conditions.append(
            "al.communication_date < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)"
        )

        file_conditions.append(
            "f.creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)"
        )

        version_conditions.append(
            "v.creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)"
        )

    # Convert conditions to SQL
    comment_where = ""
    if comment_conditions:
        comment_where = "WHERE " + " AND ".join(comment_conditions)

    activity_log_where = ""
    if activity_log_conditions:
        activity_log_where = "WHERE " + " AND ".join(activity_log_conditions)

    file_where = ""
    if file_conditions:
        file_where = "WHERE " + " AND ".join(file_conditions)

    version_where = ""
    if version_conditions:
        version_where = "WHERE " + " AND ".join(version_conditions)

    query = f"""
        SELECT
            c.creation AS activity_date,
            COALESCE(c.comment_by, c.owner) AS user,
            c.comment_type AS activity_type,
            c.reference_doctype AS reference_doctype,
            c.reference_name AS reference_name,
            c.content AS description
        FROM `tabComment` c
        {comment_where}

        UNION ALL

        SELECT
            al.communication_date AS activity_date,
            COALESCE(al.user, al.owner) AS user,
            CONCAT_WS(' - ', al.operation, al.status) AS activity_type,
            al.reference_doctype AS reference_doctype,
            al.reference_name AS reference_name,
            COALESCE(al.subject, al.content) AS description
        FROM `tabActivity Log` al
        {activity_log_where}

        UNION ALL

        SELECT
            f.creation AS activity_date,
            f.owner AS user,
            'File Upload' AS activity_type,
            f.attached_to_doctype AS reference_doctype,
            f.attached_to_name AS reference_name,
            f.file_name AS description
        FROM `tabFile` f
        {file_where}

        UNION ALL

        SELECT
            v.creation AS activity_date,
            v.owner AS user,
            'Document Updated' AS activity_type,
            v.ref_doctype AS reference_doctype,
            v.docname AS reference_name,
            CONCAT('Document version: ', v.name) AS description
        FROM `tabVersion` v
        {version_where}

        ORDER BY activity_date DESC
    """

    data = frappe.db.sql(
        query,
        filters,
        as_dict=True
    )

    return columns, data