import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="MOL CargoFlow",
    page_icon="🚢",
    layout="wide"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

DB_NAME = "mol_cargoflow.db"


@st.cache_resource
def get_connection():
    return sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )


conn = get_connection()
cursor = conn.cursor()


# =========================================================
# DATABASE TABLES
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    severity TEXT,
    application TEXT,
    status TEXT,
    assigned_team TEXT,
    description TEXT,
    business_impact TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS service_requests (
    request_id TEXT PRIMARY KEY,
    request_type TEXT,
    priority TEXT,
    requested_by TEXT,
    status TEXT,
    assigned_team TEXT,
    description TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS rca_records (
    rca_id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT,
    observed_symptom TEXT,
    investigation TEXT,
    root_cause TEXT,
    resolution TEXT,
    prevention TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS alert_investigations (
    investigation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id TEXT,
    service TEXT,
    severity TEXT,
    alert TEXT,
    investigation_notes TEXT,
    recommended_action TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id TEXT PRIMARY KEY,
    customer_name TEXT,
    origin TEXT,
    destination TEXT,
    status TEXT,
    payment_status TEXT,
    amount REAL
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS releases (
    release_id TEXT PRIMARY KEY,
    version TEXT,
    environment TEXT,
    status TEXT,
    release_owner TEXT,
    deployment_datetime TEXT,
    change_summary TEXT,
    rollback_plan TEXT,
    release_outcome TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS audit_logs (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_type TEXT,
    reference_id TEXT,
    action TEXT,
    details TEXT,
    activity_time TEXT
)
""")

# =========================================================
# INCIDENT STATUS HISTORY
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS incident_status_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT,
    previous_status TEXT,
    new_status TEXT,
    updated_by TEXT,
    resolution_notes TEXT,
    status_change_time TEXT
)
""")

conn.commit()

# =========================================================
# INCIDENT SLA MANAGEMENT
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS incident_sla (
    sla_id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT UNIQUE,
    priority TEXT,
    sla_target_minutes INTEGER,
    incident_created_time TEXT,
    first_response_time TEXT,
    resolution_time TEXT,
    sla_status TEXT,
    escalation_required TEXT,
    escalation_level TEXT,
    last_updated TEXT
)
""")

conn.commit()

# =========================================================
# DATABASE MIGRATION
# ALERT INVESTIGATION → INCIDENT LINK
# =========================================================

cursor.execute("""
PRAGMA table_info(alert_investigations)
""")

alert_columns = [
    row[1]
    for row in cursor.fetchall()
]


if "incident_id" not in alert_columns:

    cursor.execute("""
    ALTER TABLE alert_investigations
    ADD COLUMN incident_id TEXT
    """)

    conn.commit()


# =========================================================
# DATABASE MIGRATION
# RELEASE → INCIDENT LINK
# =========================================================

cursor.execute("""
PRAGMA table_info(releases)
""")

release_columns = [
    row[1]
    for row in cursor.fetchall()
]


if "incident_id" not in release_columns:

    cursor.execute("""
    ALTER TABLE releases
    ADD COLUMN incident_id TEXT
    """)

    conn.commit()


# =========================================================
# SEED INITIAL INCIDENT DATA
# =========================================================

cursor.execute("""
SELECT COUNT(*)
FROM incidents
""")

if cursor.fetchone()[0] == 0:

    initial_incidents = [

        (
            "INC-1001",
            "P2 - High",
            "Tracking Service",
            "Investigating",
            "Application Support",
            "Shipment tracking information is delayed.",
            "Operations team cannot view real-time shipment updates."
        ),

        (
            "INC-1002",
            "P2 - High",
            "Payment Service",
            "Monitoring",
            "Development Team",
            "Payment API response time increased.",
            "Customers experienced payment failures during booking."
        ),

        (
            "INC-1003",
            "P3 - Medium",
            "Login / Authentication",
            "Resolved",
            "Application Support",
            "Some users were unable to log in.",
            "Affected users could not access the application."
        )

    ]

    cursor.executemany("""
    INSERT INTO incidents
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, initial_incidents)

    conn.commit()


# =========================================================
# SEED INITIAL SERVICE REQUEST DATA
# =========================================================

cursor.execute("""
SELECT COUNT(*)
FROM service_requests
""")

if cursor.fetchone()[0] == 0:

    initial_requests = [

        (
            "SR-3001",
            "Access Request",
            "High",
            "Operations Team",
            "In Progress",
            "Application Support",
            "User requires shipment tracking access."
        ),

        (
            "SR-3002",
            "Report Request",
            "Medium",
            "Finance Team",
            "Pending Approval",
            "Database Support",
            "Finance team requested monthly shipment report."
        ),

        (
            "SR-3003",
            "Password Reset",
            "Low",
            "Business User",
            "Resolved",
            "Application Support",
            "User requested password reset."
        )

    ]

    cursor.executemany("""
    INSERT INTO service_requests
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, initial_requests)

    conn.commit()


# =========================================================
# SEED INITIAL SHIPMENT DATA
# =========================================================

cursor.execute("""
SELECT COUNT(*)
FROM shipments
""")

if cursor.fetchone()[0] == 0:

    shipment_data = [

        (
            "SHP1001",
            "ABC Logistics",
            "Kolkata",
            "Singapore",
            "In Transit",
            "Paid",
            85000
        ),

        (
            "SHP1002",
            "Global Traders",
            "Mumbai",
            "Dubai",
            "Booked",
            "Paid",
            62000
        ),

        (
            "SHP1003",
            "Ocean Exports",
            "Chennai",
            "London",
            "Payment Failed",
            "Failed",
            91000
        ),

        (
            "SHP1004",
            "Eastern Cargo",
            "Kolkata",
            "Singapore",
            "Delivered",
            "Paid",
            45000
        ),

        (
            "SHP1005",
            "Prime Imports",
            "Delhi",
            "Rotterdam",
            "Booked",
            "Pending",
            73000
        ),

        (
            "SHP1006",
            "Blue Ocean Ltd",
            "Mumbai",
            "Hamburg",
            "In Transit",
            "Paid",
            56000
        ),

        (
            "SHP1007",
            "SeaBridge Corp",
            "Kolkata",
            "Dubai",
            "Payment Failed",
            "Failed",
            68000
        ),

        (
            "SHP1008",
            "Global Traders",
            "Chennai",
            "Singapore",
            "Booked",
            "Paid",
            52000
        )

    ]

    cursor.executemany("""
    INSERT INTO shipments
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, shipment_data)

    conn.commit()


# =========================================================
# ALERT MASTER DATA
# =========================================================

alerts = {

    "Alert ID": [
        "ALT-2001",
        "ALT-2002",
        "ALT-2003",
        "ALT-2004",
        "ALT-2005"
    ],

    "Service": [
        "Payment API",
        "Database",
        "Tracking Service",
        "Booking Service",
        "Authentication"
    ],

    "Alert": [
        "High API Response Time",
        "Database Connection Pool High",
        "Shipment Tracking Delay",
        "Booking Failure Rate Increased",
        "Multiple Login Failures"
    ],

    "Severity": [
        "P1 - Critical",
        "P2 - High",
        "P2 - High",
        "P3 - Medium",
        "P3 - Medium"
    ],

    "Status": [
        "Investigating",
        "Monitoring",
        "Investigating",
        "New",
        "Resolved"
    ]

}


alerts_df = pd.DataFrame(alerts)


# =========================================================
# HELPER FUNCTION
# =========================================================

def get_incident_options():

    incident_ids = pd.read_sql_query(
        """
        SELECT incident_id
        FROM incidents
        ORDER BY rowid DESC
        """,
        conn
    )["incident_id"].tolist()

    return ["Select Incident"] + incident_ids


def get_count(sql):

    result = pd.read_sql_query(
        sql,
        conn
    )

    return int(result.iloc[0]["count"] or 0)


# =========================================================
# HEADER
# =========================================================

st.title("🚢 MOL CargoFlow")

st.subheader(
    "Shipping & Logistics Application Support Simulation"
)

st.write(
    "Production-like Application Support environment "
    "for shipping and logistics operations."
)

st.divider()


# =========================================================
# APPLICATION HEALTH
# =========================================================

st.header("📊 Application Health")


incident_count = get_count("""
SELECT COUNT(*) AS count
FROM incidents
WHERE status NOT IN ('Resolved', 'Closed')
""")


request_count = get_count("""
SELECT COUNT(*) AS count
FROM service_requests
WHERE status NOT IN ('Resolved', 'Closed')
""")


alert_count = int(
    (alerts_df["Status"] != "Resolved").sum()
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Application Status",
        "🟢 UP"
    )


with col2:

    st.metric(
        "Active Incidents",
        incident_count
    )


with col3:

    st.metric(
        "Open Service Requests",
        request_count
    )


with col4:

    st.metric(
        "System Alerts",
        alert_count
    )


# =========================================================
# CORE SERVICES
# =========================================================

st.divider()

st.header("🔧 Core Services")


col1, col2, col3 = st.columns(3)


with col1:

    st.success(
        "🟢 Booking Service\n\nOperational"
    )


with col2:

    st.success(
        "🟢 Tracking Service\n\nOperational"
    )


with col3:

    st.warning(
        "🟡 Payment Service\n\nDegraded Performance"
    )


# =========================================================
# RECENT SUPPORT ACTIVITY
# =========================================================

st.divider()

st.header("📋 Recent Support Activity")


recent_incidents = pd.read_sql_query(
    """
    SELECT
        incident_id,
        application,
        status
    FROM incidents
    ORDER BY rowid DESC
    LIMIT 3
    """,
    conn
)


for _, row in recent_incidents.iterrows():

    message = (
        f"{row['incident_id']} — "
        f"{row['application']} — "
        f"{row['status']}"
    )

    if row["status"] in ["Resolved", "Closed"]:

        st.success(message)

    else:

        st.warning(message)


# =========================================================
# INCIDENT MANAGEMENT
# =========================================================

st.divider()

st.header("🚨 Incident Management")


with st.form(
    "incident_form",
    clear_on_submit=True
):

    incident_id = st.text_input(
        "Incident ID",
        placeholder="Example: INC-1006"
    )


    severity = st.selectbox(
        "Severity",
        [
            "Select Severity",
            "P1 - Critical",
            "P2 - High",
            "P3 - Medium",
            "P4 - Low"
        ]
    )


    application = st.selectbox(
        "Application / Service",
        [
            "Select Application",
            "Cargo Management",
            "Tracking Service",
            "Payment Service",
            "Booking Service",
            "Login / Authentication",
            "Reporting Service",
            "Database"
        ]
    )


    status = st.selectbox(
        "Status",
        [
            "Select Status",
            "New",
            "Assigned",
            "Investigating",
            "Monitoring",
            "Resolved",
            "Closed"
        ]
    )


    assigned_team = st.selectbox(
        "Assigned Team",
        [
            "Select Team",
            "Application Support",
            "Development Team",
            "Database Support",
            "Infrastructure Team"
        ]
    )


    description = st.text_area(
        "Incident Description",
        placeholder="Describe the incident/problem..."
    )


    business_impact = st.text_area(
        "Business Impact",
        placeholder="Describe how the incident is affecting business operations..."
    )


    create_incident = st.form_submit_button(
        "🚨 Create Incident"
    )


    if create_incident:

        if not incident_id.strip():

            st.error(
                "Please enter an Incident ID."
            )

        elif severity == "Select Severity":

            st.error(
                "Please select a Severity."
            )

        elif application == "Select Application":

            st.error(
                "Please select an Application / Service."
            )

        elif status == "Select Status":

            st.error(
                "Please select a Status."
            )

        elif assigned_team == "Select Team":

            st.error(
                "Please select an Assigned Team."
            )

        elif not description.strip():

            st.error(
                "Please enter an Incident Description."
            )

        elif not business_impact.strip():

            st.error(
                "Please enter the Business Impact."
            )

        else:

            try:

                cursor.execute(
                    """
                    INSERT INTO incidents
                    (
                        incident_id,
                        severity,
                        application,
                        status,
                        assigned_team,
                        description,
                        business_impact
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        incident_id.strip(),
                        severity,
                        application,
                        status,
                        assigned_team,
                        description.strip(),
                        business_impact.strip()
                    )
                )


                cursor.execute(
                    """
                    INSERT INTO audit_logs
                    (
                        activity_type,
                        reference_id,
                        action,
                        details,
                        activity_time
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        "Incident",
                        incident_id.strip(),
                        "Incident Created",
                        (
                            f"New {severity} incident created "
                            f"for {application}."
                        ),
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )
                )


                conn.commit()


                st.success(
                    f"{incident_id.strip()} created successfully "
                    "and audit activity recorded."
                )


            except sqlite3.IntegrityError:

                st.error(
                    f"Incident ID '{incident_id.strip()}' "
                    "already exists. Please use a unique Incident ID."
                )


            except Exception as e:

                st.error(
                    f"Unable to create incident: {e}"
                )


# =========================================================
# INCIDENT HISTORY
# =========================================================

st.subheader("📋 Incident History")


incident_df = pd.read_sql_query(
    """
    SELECT
        incident_id AS "Incident ID",
        severity AS "Severity",
        application AS "Application",
        status AS "Status",
        assigned_team AS "Assigned Team",
        description AS "Incident Description",
        business_impact AS "Business Impact"
    FROM incidents
    ORDER BY rowid DESC
    """,
    conn
)


if not incident_df.empty:

    st.dataframe(
        incident_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No incidents have been recorded yet."
    )


# =========================================================
# INCIDENT STATUS UPDATE / RESOLUTION
# =========================================================

st.divider()

st.header("🔄 Incident Status Update / Resolution")

st.write(
    "Update the lifecycle status of an existing incident and "
    "maintain a complete status history for audit and support tracking."
)


# =========================================================
# SELECT INCIDENT
# =========================================================

selected_status_incident = st.selectbox(
    "Select Incident",
    get_incident_options(),
    key="status_update_incident_selector"
)


# =========================================================
# CURRENT INCIDENT DETAILS
# SHOW ONLY AFTER INCIDENT IS SELECTED
# =========================================================

current_status = ""

if selected_status_incident != "Select Incident":

    current_incident_df = pd.read_sql_query(
        """
        SELECT
            incident_id,
            severity,
            application,
            status,
            assigned_team
        FROM incidents
        WHERE incident_id = ?
        """,
        conn,
        params=(selected_status_incident,)
    )

    if not current_incident_df.empty:

        current_incident = current_incident_df.iloc[0]

        current_status = current_incident["status"]


        # -----------------------------------------------------
        # CURRENT INCIDENT DETAILS
        # -----------------------------------------------------

        with st.container(border=True):

            st.subheader("📌 Current Incident Details")

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"**Incident ID:** "
                    f"{current_incident['incident_id']}"
                )

                st.write(
                    f"**Severity:** "
                    f"{current_incident['severity']}"
                )

                st.write(
                    f"**Application / Service:** "
                    f"{current_incident['application']}"
                )

            with col2:

                st.write(
                    f"**Current Status:** "
                    f"{current_incident['status']}"
                )

                st.write(
                    f"**Assigned Team:** "
                    f"{current_incident['assigned_team']}"
                )


# =========================================================
# STATUS UPDATE FORM
# =========================================================

with st.form(
    "incident_status_update_form",
    clear_on_submit=True
):

    new_status = st.selectbox(
        "New Status",
        [
            "Select New Status",
            "New",
            "Assigned",
            "Investigating",
            "Monitoring",
            "Resolved",
            "Closed"
        ]
    )


    updated_by = st.text_input(
        "Updated By",
        placeholder="e.g. Application Support"
    )


    resolution_notes = st.text_area(
        "Status Update / Resolution Notes",
        placeholder=(
            "Describe what was checked, what action was taken, "
            "or how the incident was resolved..."
        )
    )


    update_incident_status = st.form_submit_button(
        "🔄 Update Incident Status"
    )


    # =====================================================
    # VALIDATION & UPDATE
    # =====================================================

    if update_incident_status:

        if selected_status_incident == "Select Incident":

            st.error(
                "Please select an Incident."
            )

        elif new_status == "Select New Status":

            st.error(
                "Please select a New Status."
            )

        elif not updated_by.strip():

            st.error(
                "Please enter who updated the incident."
            )

        elif not resolution_notes.strip():

            st.error(
                "Please enter Status Update / Resolution Notes."
            )

        elif new_status == current_status:

            st.error(
                f"Incident is already in '{current_status}' status. "
                "Please select a different status."
            )

        else:

            try:

                # -------------------------------------------------
                # UPDATE INCIDENT STATUS
                # -------------------------------------------------

                cursor.execute(
                    """
                    UPDATE incidents
                    SET status = ?
                    WHERE incident_id = ?
                    """,
                    (
                        new_status,
                        selected_status_incident
                    )
                )


                # -------------------------------------------------
                # SAVE STATUS HISTORY
                # -------------------------------------------------

                cursor.execute(
                    """
                    INSERT INTO incident_status_history
                    (
                        incident_id,
                        previous_status,
                        new_status,
                        updated_by,
                        resolution_notes,
                        status_change_time
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        selected_status_incident,
                        current_status,
                        new_status,
                        updated_by.strip(),
                        resolution_notes.strip(),
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )
                )


                # -------------------------------------------------
                # AUDIT LOG
                # -------------------------------------------------

                cursor.execute(
                    """
                    INSERT INTO audit_logs
                    (
                        activity_type,
                        reference_id,
                        action,
                        details,
                        activity_time
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        "Incident",
                        selected_status_incident,
                        "Incident Status Updated",
                        (
                            f"Incident status changed from "
                            f"{current_status} to {new_status}. "
                            f"Updated by: {updated_by.strip()}. "
                            f"Notes: {resolution_notes.strip()}"
                        ),
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )
                )


                conn.commit()


                st.success(
                    f"{selected_status_incident} status successfully "
                    f"updated from '{current_status}' to "
                    f"'{new_status}'. Status history and audit "
                    "activity recorded."
                )


            except Exception as e:

                conn.rollback()

                st.error(
                    f"Unable to update incident status: {e}"
                )


# =========================================================
# INCIDENT STATUS HISTORY
# =========================================================

st.subheader("📜 Incident Status History")


status_history_df = pd.read_sql_query(
    """
    SELECT
        history_id AS "History ID",
        incident_id AS "Incident ID",
        previous_status AS "Previous Status",
        new_status AS "New Status",
        updated_by AS "Updated By",
        resolution_notes AS "Status / Resolution Notes",
        status_change_time AS "Changed At"
    FROM incident_status_history
    ORDER BY history_id DESC
    """,
    conn
)


if not status_history_df.empty:

    st.dataframe(
        status_history_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No incident status changes have been recorded yet."
    )

# =========================================================
# INCIDENT 360 VIEW
# =========================================================

st.divider()

st.header("🔄 Incident 360 View")


st.write(
    "Trace the complete support lifecycle of an incident "
    "across monitoring alerts, SQL investigation, RCA, "
    "releases and audit activities."
)


selected_360_incident = st.selectbox(
    "Select Incident to View",
    get_incident_options(),
    key="incident_360_selector"
)


if selected_360_incident != "Select Incident":

    # -----------------------------------------------------
    # INCIDENT DETAILS
    # -----------------------------------------------------

    st.subheader("🚨 Incident Details")


    incident_360_df = pd.read_sql_query(
        """
        SELECT
            incident_id AS "Incident ID",
            severity AS "Severity",
            application AS "Application",
            status AS "Status",
            assigned_team AS "Assigned Team",
            description AS "Incident Description",
            business_impact AS "Business Impact"
        FROM incidents
        WHERE incident_id = ?
        """,
        conn,
        params=(selected_360_incident,)
    )


    if not incident_360_df.empty:

        incident_row = incident_360_df.iloc[0]


        col1, col2, col3, col4 = st.columns(4)


        with col1:

            st.metric(
                "Incident ID",
                incident_row["Incident ID"]
            )


        with col2:

            st.metric(
                "Severity",
                incident_row["Severity"]
            )


        with col3:

            st.metric(
                "Status",
                incident_row["Status"]
            )


        with col4:

            st.metric(
                "Assigned Team",
                incident_row["Assigned Team"]
            )


        st.write(
            f"**Application / Service:** "
            f"{incident_row['Application']}"
        )


        st.write(
            f"**Incident Description:** "
            f"{incident_row['Incident Description']}"
        )


        st.write(
            f"**Business Impact:** "
            f"{incident_row['Business Impact']}"
        )


    # -----------------------------------------------------
    # RELATED ALERT INVESTIGATIONS
    # -----------------------------------------------------

    st.subheader("🔔 Related Alert Investigations")


    related_alerts_df = pd.read_sql_query(
        """
        SELECT
            investigation_id AS "Investigation ID",
            alert_id AS "Alert ID",
            service AS "Service",
            severity AS "Severity",
            alert AS "Alert",
            investigation_notes AS "Investigation Notes",
            recommended_action AS "Recommended Action"
        FROM alert_investigations
        WHERE incident_id = ?
        ORDER BY investigation_id DESC
        """,
        conn,
        params=(selected_360_incident,)
    )


    if not related_alerts_df.empty:

        st.dataframe(
            related_alerts_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No alert investigations are linked "
            "to this incident yet."
        )


    # -----------------------------------------------------
    # RELATED SQL INVESTIGATIONS
    # -----------------------------------------------------

    st.subheader("🗄️ Related SQL Investigations")


    related_sql_df = pd.read_sql_query(
        """
        SELECT
            activity_id AS "Activity ID",
            reference_id AS "Incident ID",
            action AS "Action",
            details AS "Investigation Details",
            activity_time AS "Activity Time"
        FROM audit_logs
        WHERE activity_type = 'SQL Investigation'
        AND reference_id = ?
        ORDER BY activity_id DESC
        """,
        conn,
        params=(selected_360_incident,)
    )


    if not related_sql_df.empty:

        st.dataframe(
            related_sql_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No SQL investigations are linked "
            "to this incident yet."
        )


    # -----------------------------------------------------
    # RELATED RCA
    # -----------------------------------------------------

    st.subheader("🔍 Related Root Cause Analysis")


    related_rca_df = pd.read_sql_query(
        """
        SELECT
            rca_id AS "RCA ID",
            incident_id AS "Incident ID",
            observed_symptom AS "Observed Symptom",
            investigation AS "Investigation Performed",
            root_cause AS "Root Cause",
            resolution AS "Resolution",
            prevention AS "Preventive Action"
        FROM rca_records
        WHERE incident_id = ?
        ORDER BY rca_id DESC
        """,
        conn,
        params=(selected_360_incident,)
    )


    if not related_rca_df.empty:

        st.dataframe(
            related_rca_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No RCA record is linked to this incident yet."
        )


    # -----------------------------------------------------
    # RELATED RELEASES
    # -----------------------------------------------------

    st.subheader("🚀 Related Releases")


    related_release_df = pd.read_sql_query(
        """
        SELECT
            release_id AS "Release ID",
            version AS "Version",
            environment AS "Environment",
            status AS "Release Status",
            release_owner AS "Release Owner",
            deployment_datetime AS "Deployment Date & Time",
            change_summary AS "Change Summary",
            rollback_plan AS "Rollback Plan",
            release_outcome AS "Release Outcome"
        FROM releases
        WHERE incident_id = ?
        ORDER BY rowid DESC
        """,
        conn,
        params=(selected_360_incident,)
    )


    if not related_release_df.empty:

        st.dataframe(
            related_release_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No release is linked to this incident yet."
        )


    # -----------------------------------------------------
    # RELATED AUDIT ACTIVITIES
    # -----------------------------------------------------

    st.subheader("📜 Related Audit Activities")


    related_audit_df = pd.read_sql_query(
        """
        SELECT
            activity_id AS "Activity ID",
            activity_type AS "Activity Type",
            reference_id AS "Reference ID",
            action AS "Action",
            details AS "Details",
            activity_time AS "Activity Time"
        FROM audit_logs
        WHERE
            reference_id = ?

            OR reference_id IN (
                SELECT alert_id
                FROM alert_investigations
                WHERE incident_id = ?
            )

            OR reference_id IN (
                SELECT release_id
                FROM releases
                WHERE incident_id = ?
            )

        ORDER BY activity_id DESC
        """,
        conn,
        params=(
            selected_360_incident,
            selected_360_incident,
            selected_360_incident
        )
    )


    if not related_audit_df.empty:

        st.dataframe(
            related_audit_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No audit activities are linked "
            "to this incident yet."
        )


# =========================================================
# SQL & DATABASE TROUBLESHOOTING
# =========================================================

st.divider()

st.header("🗄️ SQL & Database Troubleshooting")


st.write(
    "Use read-only SQL queries to investigate shipment, "
    "booking and payment-related application issues."
)


st.subheader("📋 Shipment Database")


shipment_df = pd.read_sql_query(
    """
    SELECT
        shipment_id AS "Shipment ID",
        customer_name AS "Customer Name",
        origin AS "Origin",
        destination AS "Destination",
        status AS "Status",
        payment_status AS "Payment Status",
        amount AS "Amount"
    FROM shipments
    """,
    conn
)


st.dataframe(
    shipment_df,
    use_container_width=True,
    hide_index=True
)


st.subheader("🔎 SQL Query Console")


selected_sql_incident = st.selectbox(
    "Related Incident (Optional)",
    get_incident_options(),
    key="sql_incident_selector"
)


query = st.text_area(
    "Enter SQL Query",
    value="SELECT * FROM shipments;",
    height=120,
    key="sql_query_console"
)


if st.button(
    "▶️ Execute Query",
    key="execute_sql"
):

    cleaned_query = query.strip()


    if not cleaned_query:

        st.error(
            "Please enter a SQL query."
        )


    elif not (
        cleaned_query.upper().startswith("SELECT")
        or cleaned_query.upper().startswith("WITH")
        or cleaned_query.upper().startswith("PRAGMA")
    ):

        st.error(
            "For this simulation, the SQL console supports "
            "read-only SELECT, WITH and PRAGMA queries only."
        )


    else:

        try:

            result = pd.read_sql_query(
                cleaned_query,
                conn
            )


            st.success(
                "Query executed successfully."
            )


            st.dataframe(
                result,
                use_container_width=True
            )


            if selected_sql_incident != "Select Incident":

                cursor.execute(
                    """
                    INSERT INTO audit_logs
                    (
                        activity_type,
                        reference_id,
                        action,
                        details,
                        activity_time
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        "SQL Investigation",
                        selected_sql_incident,
                        "SQL Query Executed",
                        (
                            f"Read-only SQL investigation executed "
                            f"for incident {selected_sql_incident}. "
                            f"Query: {cleaned_query}"
                        ),
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )
                )


                conn.commit()


                st.info(
                    f"SQL investigation linked to "
                    f"{selected_sql_incident} and audit activity recorded."
                )


        except Exception as e:

            st.error(
                f"SQL Error: {e}"
            )


# =========================================================
# ROOT CAUSE ANALYSIS
# =========================================================

st.divider()

st.header("🔍 Root Cause Analysis (RCA)")


with st.form(
    "rca_form",
    clear_on_submit=True
):

    selected_incident = st.selectbox(
        "Incident ID",
        get_incident_options(),
        key="rca_incident_selector"
    )


    observed_symptom = st.text_area(
        "Observed Symptom",
        placeholder="Describe the issue observed by users or monitoring..."
    )


    investigation = st.text_area(
        "Investigation Performed",
        placeholder="Describe logs reviewed, SQL queries, API checks, etc..."
    )


    root_cause = st.text_area(
        "Root Cause",
        placeholder="Describe the identified root cause..."
    )


    resolution = st.text_area(
        "Resolution",
        placeholder="Describe how the issue was resolved..."
    )


    prevention = st.text_area(
        "Preventive Action",
        placeholder="Describe what will be done to prevent recurrence..."
    )


    save_rca = st.form_submit_button(
        "🔍 Save RCA"
    )


    if save_rca:

        if selected_incident == "Select Incident":

            st.error(
                "Please select an Incident."
            )

        elif not observed_symptom.strip():

            st.error(
                "Please enter the Observed Symptom."
            )

        elif not investigation.strip():

            st.error(
                "Please enter the Investigation Performed."
            )

        elif not root_cause.strip():

            st.error(
                "Please enter the Root Cause."
            )

        elif not resolution.strip():

            st.error(
                "Please enter the Resolution."
            )

        elif not prevention.strip():

            st.error(
                "Please enter the Preventive Action."
            )

        else:

            try:

                cursor.execute(
                    """
                    INSERT INTO rca_records
                    (
                        incident_id,
                        observed_symptom,
                        investigation,
                        root_cause,
                        resolution,
                        prevention
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        selected_incident,
                        observed_symptom.strip(),
                        investigation.strip(),
                        root_cause.strip(),
                        resolution.strip(),
                        prevention.strip()
                    )
                )


                rca_id = cursor.lastrowid


                cursor.execute(
                    """
                    INSERT INTO audit_logs
                    (
                        activity_type,
                        reference_id,
                        action,
                        details,
                        activity_time
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        "RCA",
                        selected_incident,
                        "RCA Recorded",
                        (
                            f"Root Cause Analysis recorded "
                            f"for incident {selected_incident}."
                        ),
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )
                )


                conn.commit()


                st.success(
                    f"RCA-{rca_id} recorded successfully "
                    f"for {selected_incident} and audit activity recorded."
                )


            except Exception as e:

                st.error(
                    f"Unable to save RCA: {e}"
                )


# =========================================================
# RCA HISTORY
# =========================================================

st.subheader("📋 RCA History")


rca_df = pd.read_sql_query(
    """
    SELECT
        rca_id AS "RCA ID",
        incident_id AS "Incident ID",
        observed_symptom AS "Observed Symptom",
        investigation AS "Investigation Performed",
        root_cause AS "Root Cause",
        resolution AS "Resolution",
        prevention AS "Preventive Action"
    FROM rca_records
    ORDER BY rca_id DESC
    """,
    conn
)


if not rca_df.empty:

    st.dataframe(
        rca_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No RCA records have been recorded yet."
    )


# =========================================================
# ALERTS & MONITORING
# =========================================================

st.divider()

st.header("🔔 Alerts & Monitoring")


st.write(
    "Monitor application health and investigate alerts "
    "generated by production systems."
)


st.subheader("📋 Active & Recent Alerts")


st.dataframe(
    alerts_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# ALERT INVESTIGATION
# =========================================================

st.subheader("🔎 Alert Investigation")


with st.form(
    "alert_investigation_form",
    clear_on_submit=True
):

    selected_alert = st.selectbox(
        "Select Alert",
        ["Select Alert"] + alerts_df["Alert ID"].tolist(),
        key="alert_selector"
    )


    selected_incident_for_alert = st.selectbox(
        "Related Incident",
        get_incident_options(),
        key="alert_incident_selector"
    )


    if selected_alert != "Select Alert":

        selected_row = alerts_df[
            alerts_df["Alert ID"] == selected_alert
        ].iloc[0]


        st.info(
            f"**Service:** {selected_row['Service']}\n\n"
            f"**Alert:** {selected_row['Alert']}\n\n"
            f"**Severity:** {selected_row['Severity']}\n\n"
            f"**Current Status:** {selected_row['Status']}"
        )


    investigation_notes = st.text_area(
        "Investigation Notes",
        placeholder="Document what you checked during alert investigation..."
    )


    action = st.selectbox(
        "Recommended Action",
        [
            "Select Action",
            "Check application logs",
            "Run SQL investigation",
            "Check API response time",
            "Check database connections",
            "Escalate to Development Team",
            "Escalate to Infrastructure Team",
            "Monitor after corrective action"
        ]
    )


    investigate_alert = st.form_submit_button(
        "🔧 Investigate & Save Alert"
    )


    if investigate_alert:

        if selected_alert == "Select Alert":

            st.error(
                "Please select an Alert."
            )

        elif selected_incident_for_alert == "Select Incident":

            st.error(
                "Please select the Related Incident."
            )

        elif not investigation_notes.strip():

            st.error(
                "Please enter Investigation Notes."
            )

        elif action == "Select Action":

            st.error(
                "Please select a Recommended Action."
            )

        else:

            try:

                selected_row = alerts_df[
                    alerts_df["Alert ID"] == selected_alert
                ].iloc[0]


                cursor.execute(
                    """
                    INSERT INTO alert_investigations
                    (
                        alert_id,
                        service,
                        severity,
                        alert,
                        investigation_notes,
                        recommended_action,
                        incident_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        selected_alert,
                        selected_row["Service"],
                        selected_row["Severity"],
                        selected_row["Alert"],
                        investigation_notes.strip(),
                        action,
                        selected_incident_for_alert
                    )
                )


                cursor.execute(
                    """
                    INSERT INTO audit_logs
                    (
                        activity_type,
                        reference_id,
                        action,
                        details,
                        activity_time
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        "Alert Investigation",
                        selected_alert,
                        "Alert Investigated",
                        (
                            f"Alert investigation completed for "
                            f"{selected_row['Service']} service and "
                            f"linked to incident "
                            f"{selected_incident_for_alert}."
                        ),
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )
                )


                conn.commit()


                st.success(
                    f"{selected_alert} investigation completed "
                    f"successfully and linked to "
                    f"{selected_incident_for_alert}. "
                    "Audit activity recorded."
                )


            except Exception as e:

                st.error(
                    f"Unable to save alert investigation: {e}"
                )


# =========================================================
# INVESTIGATION HISTORY
# =========================================================

st.subheader("📋 Investigation History")


investigation_df = pd.read_sql_query(
    """
    SELECT
        investigation_id AS "Investigation ID",
        alert_id AS "Alert ID",
        incident_id AS "Related Incident",
        service AS "Service",
        alert AS "Alert",
        severity AS "Severity",
        investigation_notes AS "Investigation Notes",
        recommended_action AS "Recommended Action"
    FROM alert_investigations
    ORDER BY investigation_id DESC
    """,
    conn
)


if not investigation_df.empty:

    st.dataframe(
        investigation_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No alert investigations have been recorded yet."
    )


# =========================================================
# SERVICE REQUEST MANAGEMENT
# =========================================================

st.divider()

st.header("🎫 Service Request Management")


st.write(
    "Manage user and business requests that do not represent "
    "a production incident."
)


with st.expander(
    "➕ Create New Service Request"
):

    with st.form(
        "service_request_form",
        clear_on_submit=True
    ):

        col1, col2 = st.columns(2)


        with col1:

            request_id = st.text_input(
                "Request ID",
                placeholder="e.g. SR-3006"
            )


            request_type = st.selectbox(
                "Request Type",
                [
                    "Select Request Type",
                    "Access Request",
                    "Password Reset",
                    "Report Request",
                    "User Account Creation",
                    "Data Correction",
                    "Application Configuration"
                ]
            )


            priority = st.selectbox(
                "Priority",
                [
                    "Select Priority",
                    "High",
                    "Medium",
                    "Low"
                ]
            )


        with col2:

            requested_by = st.text_input(
                "Requested By",
                placeholder="e.g. Operations Team"
            )


            assigned_team = st.selectbox(
                "Assigned Team",
                [
                    "Select Team",
                    "Application Support",
                    "Database Support",
                    "Infrastructure Team",
                    "Security Team"
                ]
            )


            request_status = st.selectbox(
                "Status",
                [
                    "Select Status",
                    "New",
                    "In Progress",
                    "Pending Approval",
                    "Resolved",
                    "Closed"
                ]
            )


        request_description = st.text_area(
            "Request Description",
            placeholder="Describe the user's request..."
        )


        create_service_request = st.form_submit_button(
            "🎫 Create Service Request"
        )


        if create_service_request:

            if not request_id.strip():

                st.error(
                    "Please enter a Request ID."
                )

            elif request_type == "Select Request Type":

                st.error(
                    "Please select a Request Type."
                )

            elif priority == "Select Priority":

                st.error(
                    "Please select a Priority."
                )

            elif not requested_by.strip():

                st.error(
                    "Please enter who requested the service."
                )

            elif assigned_team == "Select Team":

                st.error(
                    "Please select an Assigned Team."
                )

            elif request_status == "Select Status":

                st.error(
                    "Please select a Status."
                )

            elif not request_description.strip():

                st.error(
                    "Please provide a Request Description."
                )

            else:

                try:

                    cursor.execute(
                        """
                        INSERT INTO service_requests
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            request_id.strip(),
                            request_type,
                            priority,
                            requested_by.strip(),
                            request_status,
                            assigned_team,
                            request_description.strip()
                        )
                    )


                    cursor.execute(
                        """
                        INSERT INTO audit_logs
                        (
                            activity_type,
                            reference_id,
                            action,
                            details,
                            activity_time
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            "Service Request",
                            request_id.strip(),
                            "Service Request Created",
                            (
                                f"{request_type} created with "
                                f"{priority} priority for "
                                f"{requested_by.strip()}."
                            ),
                            datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        )
                    )


                    conn.commit()


                    st.success(
                        f"Service Request {request_id.strip()} "
                        "created successfully and saved to the "
                        "database. Audit activity recorded."
                    )


                except sqlite3.IntegrityError:

                    st.error(
                        f"Request ID {request_id.strip()} "
                        "already exists."
                    )


                except Exception as e:

                    st.error(
                        f"Unable to create service request: {e}"
                    )


# =========================================================
# SERVICE REQUEST HISTORY
# =========================================================

st.subheader("📋 Existing Service Requests")


service_request_df = pd.read_sql_query(
    """
    SELECT
        request_id AS "Request ID",
        request_type AS "Request Type",
        priority AS "Priority",
        requested_by AS "Requested By",
        status AS "Status",
        assigned_team AS "Assigned Team",
        description AS "Request Description"
    FROM service_requests
    ORDER BY rowid DESC
    """,
    conn
)


if not service_request_df.empty:

    st.dataframe(
        service_request_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No service requests have been recorded yet."
    )


# =========================================================
# RELEASE MANAGEMENT
# =========================================================

st.divider()

st.header("🚀 Release Management")


st.write(
    "Track application releases, deployments, change details, "
    "rollback plans, deployment outcomes and incident relationships."
)


with st.expander(
    "➕ Create New Release"
):

    with st.form(
        "release_form",
        clear_on_submit=True
    ):

        col1, col2 = st.columns(2)


        with col1:

            release_id = st.text_input(
                "Release ID",
                placeholder="e.g. REL-2026-002"
            )


            version = st.text_input(
                "Version",
                placeholder="e.g. v2.4.2"
            )


            environment = st.selectbox(
                "Environment",
                [
                    "Select Environment",
                    "Development",
                    "Testing",
                    "QA",
                    "Staging",
                    "Production"
                ]
            )


            release_status = st.selectbox(
                "Release Status",
                [
                    "Select Release Status",
                    "Planned",
                    "In Progress",
                    "Successful",
                    "Failed",
                    "Rolled Back"
                ]
            )


            release_owner = st.text_input(
                "Release Owner",
                placeholder="e.g. Application Support"
            )


            selected_release_incident = st.selectbox(
                "Related Incident",
                get_incident_options(),
                key="release_incident_selector"
            )


        with col2:

            deployment_date = st.date_input(
                "Deployment Date",
                value=datetime.now().date()
            )


            deployment_time = st.time_input(
                "Deployment Time",
                value=datetime.now().time().replace(
                    second=0,
                    microsecond=0
                )
            )


            change_summary = st.text_area(
                "Change Summary",
                placeholder="Describe the changes included in this release..."
            )


            rollback_plan = st.text_area(
                "Rollback Plan",
                placeholder="Describe the rollback steps if the release fails..."
            )


            release_outcome = st.text_area(
                "Release Outcome",
                placeholder="Describe the final deployment result..."
            )


        create_release = st.form_submit_button(
            "🚀 Save Release"
        )


        if create_release:

            if not release_id.strip():

                st.error(
                    "Please enter a Release ID."
                )

            elif not version.strip():

                st.error(
                    "Please enter a Version."
                )

            elif environment == "Select Environment":

                st.error(
                    "Please select an Environment."
                )

            elif release_status == "Select Release Status":

                st.error(
                    "Please select a Release Status."
                )

            elif not release_owner.strip():

                st.error(
                    "Please enter the Release Owner."
                )

            elif selected_release_incident == "Select Incident":

                st.error(
                    "Please select the Related Incident."
                )

            elif not change_summary.strip():

                st.error(
                    "Please enter a Change Summary."
                )

            elif not rollback_plan.strip():

                st.error(
                    "Please provide a Rollback Plan."
                )

            elif not release_outcome.strip():

                st.error(
                    "Please provide the Release Outcome."
                )

            else:

                try:

                    deployment_datetime = datetime.combine(
                        deployment_date,
                        deployment_time
                    ).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )


                    cursor.execute(
                        """
                        INSERT INTO releases
                        (
                            release_id,
                            version,
                            environment,
                            status,
                            release_owner,
                            deployment_datetime,
                            change_summary,
                            rollback_plan,
                            release_outcome,
                            incident_id
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            release_id.strip(),
                            version.strip(),
                            environment,
                            release_status,
                            release_owner.strip(),
                            deployment_datetime,
                            change_summary.strip(),
                            rollback_plan.strip(),
                            release_outcome.strip(),
                            selected_release_incident
                        )
                    )


                    cursor.execute(
                        """
                        INSERT INTO audit_logs
                        (
                            activity_type,
                            reference_id,
                            action,
                            details,
                            activity_time
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            "Release",
                            release_id.strip(),
                            "Release Created",
                            (
                                f"Release {version.strip()} deployed to "
                                f"{environment} with status "
                                f"{release_status} and linked to "
                                f"incident {selected_release_incident}."
                            ),
                            datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        )
                    )


                    conn.commit()


                    st.success(
                        f"Release {release_id.strip()} saved successfully "
                        f"and linked to {selected_release_incident}. "
                        "Audit activity recorded."
                    )


                except sqlite3.IntegrityError:

                    st.error(
                        f"Release ID {release_id.strip()} "
                        "already exists. Please use a unique Release ID."
                    )


                except Exception as e:

                    st.error(
                        f"Unable to save release: {e}"
                    )


# =========================================================
# RELEASE HISTORY
# =========================================================

st.subheader("📋 Release History")


release_df = pd.read_sql_query(
    """
    SELECT
        release_id AS "Release ID",
        version AS "Version",
        environment AS "Environment",
        status AS "Release Status",
        release_owner AS "Release Owner",
        incident_id AS "Related Incident",
        deployment_datetime AS "Deployment Date & Time",
        change_summary AS "Change Summary",
        rollback_plan AS "Rollback Plan",
        release_outcome AS "Release Outcome"
    FROM releases
    ORDER BY rowid DESC
    """,
    conn
)


if not release_df.empty:

    st.dataframe(
        release_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No releases have been recorded yet."
    )


# =========================================================
# AUDIT / ACTIVITY HISTORY
# =========================================================

st.divider()

st.header("📜 Audit / Activity History")


st.write(
    "Track important application support activities and maintain "
    "a centralized audit trail of incidents, SQL investigations, "
    "alert investigations, service requests, RCA activities and releases."
)


audit_summary = pd.read_sql_query(
    """
    SELECT

        COUNT(*) AS total_activities,

        SUM(
            CASE
                WHEN activity_type = 'Incident'
                THEN 1
                ELSE 0
            END
        ) AS incident_activities,

        SUM(
            CASE
                WHEN activity_type = 'RCA'
                THEN 1
                ELSE 0
            END
        ) AS rca_activities,

        SUM(
            CASE
                WHEN activity_type = 'Alert Investigation'
                THEN 1
                ELSE 0
            END
        ) AS alert_activities,

        SUM(
            CASE
                WHEN activity_type = 'SQL Investigation'
                THEN 1
                ELSE 0
            END
        ) AS sql_activities,

        SUM(
            CASE
                WHEN activity_type = 'Service Request'
                THEN 1
                ELSE 0
            END
        ) AS service_request_activities,

        SUM(
            CASE
                WHEN activity_type = 'Release'
                THEN 1
                ELSE 0
            END
        ) AS release_activities

    FROM audit_logs
    """,
    conn
)


total_activities = int(
    audit_summary.iloc[0]["total_activities"] or 0
)


incident_activities = int(
    audit_summary.iloc[0]["incident_activities"] or 0
)


rca_activities = int(
    audit_summary.iloc[0]["rca_activities"] or 0
)


alert_activities = int(
    audit_summary.iloc[0]["alert_activities"] or 0
)


sql_activities = int(
    audit_summary.iloc[0]["sql_activities"] or 0
)


service_request_activities = int(
    audit_summary.iloc[0]["service_request_activities"] or 0
)


release_activities = int(
    audit_summary.iloc[0]["release_activities"] or 0
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Total Activities",
        total_activities
    )


with col2:

    st.metric(
        "Incidents",
        incident_activities
    )


with col3:

    st.metric(
        "RCA",
        rca_activities
    )


with col4:

    st.metric(
        "Alerts",
        alert_activities
    )


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "SQL Investigations",
        sql_activities
    )


with col2:

    st.metric(
        "Service Requests",
        service_request_activities
    )


with col3:

    st.metric(
        "Releases",
        release_activities
    )


# =========================================================
# AUDIT FILTER
# =========================================================

st.subheader("🔎 Filter Audit Activities")


audit_type_options = [
    "All Activities",
    "Incident",
    "SQL Investigation",
    "RCA",
    "Alert Investigation",
    "Service Request",
    "Release"
]


selected_audit_type = st.selectbox(
    "Activity Type",
    audit_type_options
)


if selected_audit_type == "All Activities":

    audit_df = pd.read_sql_query(
        """
        SELECT
            activity_id AS "Activity ID",
            activity_type AS "Activity Type",
            reference_id AS "Reference ID",
            action AS "Action",
            details AS "Details",
            activity_time AS "Activity Time"
        FROM audit_logs
        ORDER BY activity_id DESC
        """,
        conn
    )


else:

    audit_df = pd.read_sql_query(
        """
        SELECT
            activity_id AS "Activity ID",
            activity_type AS "Activity Type",
            reference_id AS "Reference ID",
            action AS "Action",
            details AS "Details",
            activity_time AS "Activity Time"
        FROM audit_logs
        WHERE activity_type = ?
        ORDER BY activity_id DESC
        """,
        conn,
        params=(selected_audit_type,)
    )


st.subheader("📋 Activity History")


if not audit_df.empty:

    st.dataframe(
        audit_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No audit activities have been recorded yet."
    )


# =========================================================
# SUPPORT METRICS / REPORTS DASHBOARD
# =========================================================

st.divider()

st.header("📈 Support Metrics / Reports Dashboard")


st.write(
    "Monitor operational support performance using dynamic "
    "metrics calculated directly from the application's SQLite database."
)


# =========================================================
# INCIDENT METRICS
# =========================================================

total_incidents = get_count("""
SELECT COUNT(*) AS count
FROM incidents
""")


open_incidents = get_count("""
SELECT COUNT(*) AS count
FROM incidents
WHERE status NOT IN ('Resolved', 'Closed')
""")


resolved_incidents = get_count("""
SELECT COUNT(*) AS count
FROM incidents
WHERE status IN ('Resolved', 'Closed')
""")


# =========================================================
# SERVICE REQUEST METRICS
# =========================================================

total_service_requests = get_count("""
SELECT COUNT(*) AS count
FROM service_requests
""")


open_service_requests = get_count("""
SELECT COUNT(*) AS count
FROM service_requests
WHERE status NOT IN ('Resolved', 'Closed')
""")


# =========================================================
# RCA METRICS
# =========================================================

total_rca = get_count("""
SELECT COUNT(*) AS count
FROM rca_records
""")


# =========================================================
# RELEASE METRICS
# =========================================================

total_releases = get_count("""
SELECT COUNT(*) AS count
FROM releases
""")


successful_releases = get_count("""
SELECT COUNT(*) AS count
FROM releases
WHERE status = 'Successful'
""")


failed_releases = get_count("""
SELECT COUNT(*) AS count
FROM releases
WHERE status = 'Failed'
""")


rolled_back_releases = get_count("""
SELECT COUNT(*) AS count
FROM releases
WHERE status = 'Rolled Back'
""")


# =========================================================
# SHIPMENT METRICS
# =========================================================

total_shipments = get_count("""
SELECT COUNT(*) AS count
FROM shipments
""")


successful_payments = get_count("""
SELECT COUNT(*) AS count
FROM shipments
WHERE payment_status = 'Paid'
""")


failed_payments = get_count("""
SELECT COUNT(*) AS count
FROM shipments
WHERE payment_status = 'Failed'
""")


pending_payments = get_count("""
SELECT COUNT(*) AS count
FROM shipments
WHERE payment_status = 'Pending'
""")


# =========================================================
# SUPPORT KPI CARDS
# =========================================================

st.subheader("🎯 Support KPIs")


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Total Incidents",
        total_incidents
    )


with col2:

    st.metric(
        "Open Incidents",
        open_incidents
    )


with col3:

    st.metric(
        "Resolved Incidents",
        resolved_incidents
    )


with col4:

    st.metric(
        "Total Service Requests",
        total_service_requests
    )


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Open Service Requests",
        open_service_requests
    )


with col2:

    st.metric(
        "RCA Records",
        total_rca
    )


with col3:

    st.metric(
        "Total Releases",
        total_releases
    )


with col4:

    st.metric(
        "Total Shipments",
        total_shipments
    )


# =========================================================
# INCIDENT SEVERITY BREAKDOWN
# =========================================================

st.subheader("🚨 Incident Severity Breakdown")


severity_df = pd.read_sql_query(
    """
    SELECT
        severity AS "Severity",
        COUNT(*) AS "Incident Count"
    FROM incidents
    GROUP BY severity
    ORDER BY
        CASE severity
            WHEN 'P1 - Critical' THEN 1
            WHEN 'P2 - High' THEN 2
            WHEN 'P3 - Medium' THEN 3
            WHEN 'P4 - Low' THEN 4
            ELSE 5
        END
    """,
    conn
)


if not severity_df.empty:

    st.bar_chart(
        severity_df.set_index("Severity")
    )

else:

    st.info(
        "No incident severity data available."
    )


# =========================================================
# INCIDENT STATUS BREAKDOWN
# =========================================================

st.subheader("📊 Incident Status Breakdown")


incident_status_df = pd.read_sql_query(
    """
    SELECT
        status AS "Status",
        COUNT(*) AS "Incident Count"
    FROM incidents
    GROUP BY status
    ORDER BY "Incident Count" DESC
    """,
    conn
)


if not incident_status_df.empty:

    st.bar_chart(
        incident_status_df.set_index("Status")
    )

else:

    st.info(
        "No incident status data available."
    )


# =========================================================
# RELEASE OUTCOME BREAKDOWN
# =========================================================

st.subheader("🚀 Release Outcome Breakdown")


release_outcome_df = pd.read_sql_query(
    """
    SELECT
        status AS "Release Status",
        COUNT(*) AS "Release Count"
    FROM releases
    GROUP BY status
    ORDER BY "Release Count" DESC
    """,
    conn
)


if not release_outcome_df.empty:

    st.bar_chart(
        release_outcome_df.set_index("Release Status")
    )

else:

    st.info(
        "No release data available."
    )


# =========================================================
# SHIPMENT STATUS BREAKDOWN
# =========================================================

st.subheader("🚢 Shipment Status")


shipment_status_df = pd.read_sql_query(
    """
    SELECT
        status AS "Shipment Status",
        COUNT(*) AS "Shipment Count"
    FROM shipments
    GROUP BY status
    ORDER BY "Shipment Count" DESC
    """,
    conn
)


if not shipment_status_df.empty:

    st.bar_chart(
        shipment_status_df.set_index("Shipment Status")
    )

else:

    st.info(
        "No shipment status data available."
    )


# =========================================================
# PAYMENT HEALTH
# =========================================================

st.subheader("💳 Payment Health")


payment_df = pd.DataFrame(
    {
        "Payment Status": [
            "Paid",
            "Pending",
            "Failed"
        ],

        "Shipment Count": [
            successful_payments,
            pending_payments,
            failed_payments
        ]
    }
)


st.bar_chart(
    payment_df.set_index("Payment Status")
)


# =========================================================
# SERVICE REQUEST STATUS
# =========================================================

st.subheader("🎫 Service Request Status")


service_request_status_df = pd.read_sql_query(
    """
    SELECT
        status AS "Status",
        COUNT(*) AS "Request Count"
    FROM service_requests
    GROUP BY status
    ORDER BY "Request Count" DESC
    """,
    conn
)


if not service_request_status_df.empty:

    st.bar_chart(
        service_request_status_df.set_index("Status")
    )

else:

    st.info(
        "No service request data available."
    )


# =========================================================
# RELEASE PERFORMANCE SUMMARY
# =========================================================

st.subheader("📋 Release Performance Summary")


release_performance_df = pd.DataFrame(
    {
        "Release Metric": [
            "Total Releases",
            "Successful Releases",
            "Failed Releases",
            "Rolled Back Releases"
        ],

        "Count": [
            total_releases,
            successful_releases,
            failed_releases,
            rolled_back_releases
        ]
    }
)


st.dataframe(
    release_performance_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# OPERATIONAL SUMMARY
# =========================================================

st.subheader("📝 Operational Summary")


st.write(
    f"""
**Incident Management:** {open_incidents} incident(s) currently require active support attention.

**Service Requests:** {open_service_requests} service request(s) remain open or in progress.

**RCA:** {total_rca} Root Cause Analysis record(s) have been documented.

**SQL Investigations:** {sql_activities} SQL investigation activity/activities have been recorded.

**Alert Investigations:** {alert_activities} alert investigation activity/activities have been recorded.

**Releases:** {successful_releases} successful release(s), {failed_releases} failed release(s), and {rolled_back_releases} rolled-back release(s) are recorded.

**Shipment Operations:** {total_shipments} shipment(s) are currently present in the operational database.

**Payment Health:** {failed_payments} shipment payment(s) have failed and {pending_payments} payment(s) remain pending.

**Active Alerts:** {alert_count} alert(s) currently require monitoring or investigation.
"""
)


# =========================================================
# FOOTER
# =========================================================

st.divider()


st.success(
    "MOL CargoFlow Application Support Environment Ready ✅"
)


st.caption(
    "Production-like support workflow: "
    "Incident → Alert → SQL Investigation → RCA → Release → Audit → Metrics"
)