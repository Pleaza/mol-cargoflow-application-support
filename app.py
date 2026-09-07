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


def get_connection():
    return sqlite3.connect(DB_NAME)


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

conn.commit()


# =========================================================
# INSERT INITIAL INCIDENT DATA
# =========================================================

cursor.execute("SELECT COUNT(*) FROM incidents")

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
# INSERT INITIAL SERVICE REQUEST DATA
# =========================================================

cursor.execute("SELECT COUNT(*) FROM service_requests")

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
# INSERT INITIAL SHIPMENT DATA
# =========================================================

cursor.execute("SELECT COUNT(*) FROM shipments")

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

incident_count = pd.read_sql_query(
    """
    SELECT COUNT(*) AS count
    FROM incidents
    WHERE status != 'Resolved'
    """,
    conn
).iloc[0]["count"]

request_count = pd.read_sql_query(
    """
    SELECT COUNT(*) AS count
    FROM service_requests
    WHERE status NOT IN ('Resolved', 'Closed')
    """,
    conn
).iloc[0]["count"]

alert_count = 2

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Application Status", "🟢 UP")

with col2:
    st.metric("Active Incidents", int(incident_count))

with col3:
    st.metric("Open Service Requests", int(request_count))

with col4:
    st.metric("System Alerts", alert_count)


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

recent_incidents = pd.read_sql_query("""
    SELECT incident_id, application, status
    FROM incidents
    ORDER BY rowid DESC
    LIMIT 3
""", conn)

for _, row in recent_incidents.iterrows():

    if row["status"] == "Resolved":

        st.success(
            f"{row['incident_id']} — "
            f"{row['application']} — "
            f"{row['status']}"
        )

    else:

        st.warning(
            f"{row['incident_id']} — "
            f"{row['application']} — "
            f"{row['status']}"
        )


# =========================================================
# INCIDENT MANAGEMENT
# =========================================================

st.divider()

st.header("🚨 Incident Management")

st.write(
    "Create and manage production incidents reported by "
    "users or detected through monitoring systems."
)


with st.expander("➕ Create New Incident"):

    with st.form("incident_form", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:

            incident_id = st.text_input(
                "Incident ID",
                placeholder="e.g. INC-1006"
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
                "Application",
                [
                    "Select Application",
                    "Booking Service",
                    "Tracking Service",
                    "Payment Service",
                    "Login / Authentication",
                    "Cargo Management"
                ]
            )

        with col2:

            status = st.selectbox(
                "Status",
                [
                    "Select Status",
                    "New",
                    "Investigating",
                    "Assigned",
                    "Monitoring",
                    "Resolved"
                ]
            )

            assigned_team = st.selectbox(
                "Assigned Team",
                [
                    "Select Team",
                    "Application Support",
                    "Database Support",
                    "Infrastructure Team",
                    "Network Team",
                    "Development Team"
                ]
            )

        description = st.text_area(
            "Incident Description",
            placeholder="Describe the production issue..."
        )

        impact = st.text_area(
            "Business Impact",
            placeholder=(
                "Describe how the issue is affecting users "
                "or business operations..."
            )
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
                    "Please select an Application."
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
                    "Please provide an Incident Description."
                )

            elif not impact.strip():

                st.error(
                    "Please provide the Business Impact."
                )

            else:

                try:

                    cursor.execute("""
                        INSERT INTO incidents
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        incident_id.strip(),
                        severity,
                        application,
                        status,
                        assigned_team,
                        description.strip(),
                        impact.strip()
                    ))

                    conn.commit()

                    st.success(
                        f"Incident {incident_id.strip()} "
                        "created successfully and saved to the database."
                    )

                except sqlite3.IntegrityError:

                    st.error(
                        f"Incident ID {incident_id.strip()} "
                        "already exists."
                    )


# Existing Incidents

st.subheader("📋 Existing Incidents")

incident_df = pd.read_sql_query("""
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
""", conn)

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
# SQL & DATABASE TROUBLESHOOTING
# =========================================================

st.divider()

st.header("🗄️ SQL & Database Troubleshooting")

st.write(
    "Use SQL queries to investigate shipment, booking "
    "and payment-related application issues."
)

st.subheader("📋 Shipment Database")

df = pd.read_sql_query(
    "SELECT * FROM shipments",
    conn
)

st.dataframe(
    df,
    use_container_width=True
)


# SQL Console

st.subheader("🔎 SQL Query Console")

query = st.text_area(
    "Enter SQL Query",
    value="SELECT * FROM shipments;",
    height=120
)

if st.button(
    "▶️ Execute Query",
    key="execute_sql"
):

    try:

        result = pd.read_sql_query(
            query,
            conn
        )

        st.success(
            "Query executed successfully."
        )

        st.dataframe(
            result,
            use_container_width=True
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

st.write(
    "Investigate production incidents, identify the root cause, "
    "and document corrective and preventive actions."
)


rca_incidents = pd.read_sql_query("""
    SELECT incident_id
    FROM incidents
    ORDER BY rowid DESC
""", conn)

incident_options = [
    "Select Incident"
] + rca_incidents["incident_id"].tolist()


with st.form("rca_form", clear_on_submit=True):

    incident = st.selectbox(
        "Select Incident",
        incident_options
    )

    st.subheader("📝 RCA Investigation")

    symptom = st.text_area(
        "Observed Symptom",
        placeholder="What did the user or monitoring system observe?"
    )

    investigation = st.text_area(
        "Investigation Performed",
        placeholder=(
            "What checks, logs, SQL queries or validations "
            "were performed?"
        )
    )

    root_cause = st.text_area(
        "Root Cause",
        placeholder="What was the actual underlying cause?"
    )

    resolution = st.text_area(
        "Resolution / Corrective Action",
        placeholder="What action was taken to resolve the incident?"
    )

    prevention = st.text_area(
        "Preventive Action",
        placeholder=(
            "What can be done to prevent the issue "
            "from happening again?"
        )
    )

    generate_rca = st.form_submit_button(
        "📄 Generate & Save RCA"
    )

    if generate_rca:

        if incident == "Select Incident":

            st.error(
                "Please select an Incident."
            )

        elif not symptom.strip():

            st.error(
                "Please provide the Observed Symptom."
            )

        elif not investigation.strip():

            st.error(
                "Please provide the Investigation Performed."
            )

        elif not root_cause.strip():

            st.error(
                "Please provide the Root Cause."
            )

        elif not resolution.strip():

            st.error(
                "Please provide the Resolution / Corrective Action."
            )

        elif not prevention.strip():

            st.error(
                "Please provide the Preventive Action."
            )

        else:

            cursor.execute("""
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
            """, (
                incident,
                symptom.strip(),
                investigation.strip(),
                root_cause.strip(),
                resolution.strip(),
                prevention.strip()
            ))

            conn.commit()

            st.success(
                "RCA completed and permanently saved to the database."
            )


# RCA History

st.subheader("📋 RCA History")

rca_df = pd.read_sql_query("""
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
""", conn)

if not rca_df.empty:

    st.dataframe(
        rca_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No RCA records have been created yet."
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

st.subheader("📋 Active & Recent Alerts")

st.dataframe(
    alerts_df,
    use_container_width=True
)

# =========================
# ALERT INVESTIGATION
# =========================

st.subheader("🔎 Alert Investigation")


with st.form("alert_investigation_form", clear_on_submit=True):

    # Alert dropdown
    alert_options = [
        "Select Alert"
    ] + alerts_df["Alert ID"].tolist()

    selected_alert = st.selectbox(
        "Select Alert",
        alert_options
    )

    # Default values
    selected_service = ""
    selected_alert_name = ""
    selected_severity = ""
    selected_status = ""

    # Dynamically display selected alert information
    if selected_alert != "Select Alert":

        selected_row = alerts_df[
            alerts_df["Alert ID"] == selected_alert
        ].iloc[0]

        selected_service = selected_row["Service"]
        selected_alert_name = selected_row["Alert"]
        selected_severity = selected_row["Severity"]
        selected_status = selected_row["Status"]

        st.info(
            f"**Service:** {selected_service}\n\n"
            f"**Alert:** {selected_alert_name}\n\n"
            f"**Severity:** {selected_severity}\n\n"
            f"**Current Status:** {selected_status}"
        )

    # Investigation Notes
    investigation_notes = st.text_area(
        "Investigation Notes",
        placeholder=(
            "Document what you checked during "
            "alert investigation..."
        )
    )

    # Recommended Action
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

    # Submit button
    investigate_alert = st.form_submit_button(
        "🔧 Investigate & Save Alert"
    )

    # =========================
    # VALIDATION & SAVE
    # =========================

    if investigate_alert:

        if selected_alert == "Select Alert":

            st.error(
                "Please select an Alert."
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

            # Get selected alert information
            selected_row = alerts_df[
                alerts_df["Alert ID"] == selected_alert
            ].iloc[0]

            # Save investigation to SQLite database
            cursor.execute(
                """
                INSERT INTO alert_investigations
                (
                    alert_id,
                    service,
                    severity,
                    alert,
                    investigation_notes,
                    recommended_action
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    selected_alert,
                    selected_row["Service"],
                    selected_row["Severity"],
                    selected_row["Alert"],
                    investigation_notes.strip(),
                    action
                )
            )

            conn.commit()

            st.success(
                f"{selected_alert} investigation completed "
                "and saved to the database."
            )


# =========================
# ALERT INVESTIGATION HISTORY
# =========================

st.subheader("📋 Investigation History")


investigation_df = pd.read_sql_query(
    """
    SELECT
        investigation_id AS "Investigation ID",
        alert_id AS "Alert ID",
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


with st.expander("➕ Create New Service Request"):

    with st.form("service_request_form", clear_on_submit=True):

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

                    cursor.execute("""
                        INSERT INTO service_requests
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        request_id.strip(),
                        request_type,
                        priority,
                        requested_by.strip(),
                        request_status,
                        assigned_team,
                        request_description.strip()
                    ))

                    conn.commit()

                    st.success(
                        f"Service Request {request_id.strip()} "
                        "created successfully and saved to the database."
                    )

                except sqlite3.IntegrityError:

                    st.error(
                        f"Request ID {request_id.strip()} "
                        "already exists."
                    )


# Existing Service Requests

st.subheader("📋 Existing Service Requests")

service_request_df = pd.read_sql_query("""
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
""", conn)

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
    "Manage application releases, deployments, production changes "
    "and rollback information."
)


with st.expander("➕ Create New Release"):

    with st.form("release_form", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:

            release_id = st.text_input(
                "Release ID",
                placeholder="e.g. REL-2026-001"
            )

            version = st.text_input(
                "Version",
                placeholder="e.g. v2.4.1"
            )

            environment = st.selectbox(
                "Environment",
                [
                    "Select Environment",
                    "Development",
                    "Testing / QA",
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

        with col2:

            release_owner = st.text_input(
                "Release Owner",
                placeholder="e.g. Application Support"
            )

            # -------------------------------------------------
            # DEPLOYMENT DATE & TIME
            # -------------------------------------------------

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
                placeholder=(
                    "Describe the application change or fix "
                    "included in this release..."
                )
            )

        rollback_plan = st.text_area(
            "Rollback Plan",
            placeholder=(
                "Describe what should be done if the release fails..."
            )
        )

        release_outcome = st.text_area(
            "Release Outcome",
            placeholder=(
                "Describe the final result after deployment..."
            )
        )

        create_release = st.form_submit_button(
            "🚀 Save Release"
        )


        # =====================================================
        # VALIDATION & SAVE
        # =====================================================

        if create_release:

            if not release_id.strip():

                st.error(
                    "Please enter a Release ID."
                )

            elif not version.strip():

                st.error(
                    "Please enter the Version."
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

            elif not change_summary.strip():

                st.error(
                    "Please provide the Change Summary."
                )

            elif not rollback_plan.strip():

                st.error(
                    "Please provide the Rollback Plan."
                )

            elif not release_outcome.strip():

                st.error(
                    "Please provide the Release Outcome."
                )

            else:

                # Combine selected date and time
                deployment_datetime = datetime.combine(
                    deployment_date,
                    deployment_time
                ).strftime("%Y-%m-%d %H:%M:%S")


                try:

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
                            release_outcome
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                            release_outcome.strip()
                        )
                    )

                    conn.commit()

                    st.success(
                        f"Release {release_id.strip()} "
                        "created successfully and saved to the database."
                    )

                except sqlite3.IntegrityError:

                    st.error(
                        f"Release ID {release_id.strip()} "
                        "already exists."
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
        deployment_datetime AS "Deployment Date/Time",
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
# FOOTER
# =========================================================

st.divider()

st.success(
    "MOL CargoFlow Application Support Environment Ready ✅"
)

conn.close()