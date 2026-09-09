import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================================================
# MOL CARGOFLOW - APPLICATION SUPPORT OPERATIONS PORTAL
# =========================================================

SLA_TARGETS = {
    "P1 - Critical": 60,
    "P2 - High": 120,
    "P3 - Medium": 240,
    "P4 - Low": 480
}

IST = ZoneInfo("Asia/Kolkata")
DB_NAME = "mol_cargoflow.db"

st.set_page_config(
    page_title="MOL CargoFlow",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- STYLE --------------------
st.markdown("""
<style>
.block-container{padding-top:1.2rem;padding-bottom:2rem}
[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.25);padding:12px;border-radius:12px}
.support-card{padding:16px;border:1px solid rgba(128,128,128,.25);border-radius:14px;margin-bottom:10px}
.small-muted{color:#777;font-size:.85rem}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


conn = get_connection()
cursor = conn.cursor()


def now():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def esc(s):
    return (s or "").strip()


def count(sql, params=()):
    return int(pd.read_sql_query(sql, conn, params=params).iloc[0, 0] or 0)


def audit(kind, ref, action, details):
    cursor.execute(
        """
        INSERT INTO audit_logs(
            activity_type,
            reference_id,
            action,
            details,
            activity_time
        )
        VALUES(?,?,?,?,?)
        """,
        (kind, ref, action, details, now())
    )


def incident_options():
    df = pd.read_sql_query(
        "SELECT incident_id FROM incidents ORDER BY rowid DESC",
        conn
    )
    return ["Select Incident"] + df["incident_id"].tolist()


def service_request_options():
    df = pd.read_sql_query(
        "SELECT request_id FROM service_requests ORDER BY rowid DESC",
        conn
    )
    return ["Select Request"] + df["request_id"].tolist()


def get_escalation_level(p):
    return (
        "Level 3"
        if p == "P1 - Critical"
        else "Level 2"
        if p == "P2 - High"
        else "Level 1"
    )


def ensure_sla(incident_id, priority, created_time=None):
    if count(
        "SELECT COUNT(*) FROM incident_sla WHERE incident_id=?",
        (incident_id,)
    ):
        return

    created_time = created_time or now()

    cursor.execute(
        """
        INSERT INTO incident_sla(
            incident_id,
            priority,
            sla_target_minutes,
            incident_created_time,
            first_response_time,
            resolution_time,
            sla_status,
            escalation_required,
            escalation_level,
            last_updated
        )
        VALUES(?,?,?,?,?,?,?,?,?,?)
        """,
        (
            incident_id,
            priority,
            SLA_TARGETS.get(priority, 240),
            created_time,
            None,
            None,
            "Within SLA",
            "No",
            "None",
            created_time
        )
    )


def sla_status(created, resolved, target):
    try:
        start = datetime.strptime(
            created,
            "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=IST)

        end = (
            datetime.strptime(
                resolved,
                "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=IST)
            if resolved
            else datetime.now(IST)
        )

        return (
            "Within SLA"
            if (end - start).total_seconds() / 60 <= target
            else "SLA Breached"
        )

    except Exception:
        return "Within SLA"


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    tables = {

        "incidents": """
        CREATE TABLE IF NOT EXISTS incidents(
            incident_id TEXT PRIMARY KEY,
            severity TEXT,
            application TEXT,
            status TEXT,
            assigned_team TEXT,
            description TEXT,
            business_impact TEXT
        )
        """,

        "service_requests": """
        CREATE TABLE IF NOT EXISTS service_requests(
            request_id TEXT PRIMARY KEY,
            request_type TEXT,
            priority TEXT,
            requested_by TEXT,
            status TEXT,
            assigned_team TEXT,
            description TEXT
        )
        """,

        "rca_records": """
        CREATE TABLE IF NOT EXISTS rca_records(
            rca_id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT,
            observed_symptom TEXT,
            investigation TEXT,
            root_cause TEXT,
            resolution TEXT,
            prevention TEXT
        )
        """,

        "alert_investigations": """
        CREATE TABLE IF NOT EXISTS alert_investigations(
            investigation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT,
            service TEXT,
            severity TEXT,
            alert TEXT,
            investigation_notes TEXT,
            recommended_action TEXT,
            incident_id TEXT
        )
        """,

        "shipments": """
        CREATE TABLE IF NOT EXISTS shipments(
            shipment_id TEXT PRIMARY KEY,
            customer_name TEXT,
            origin TEXT,
            destination TEXT,
            status TEXT,
            payment_status TEXT,
            amount REAL
        )
        """,

        "releases": """
        CREATE TABLE IF NOT EXISTS releases(
            release_id TEXT PRIMARY KEY,
            version TEXT,
            environment TEXT,
            status TEXT,
            release_owner TEXT,
            deployment_datetime TEXT,
            change_summary TEXT,
            rollback_plan TEXT,
            release_outcome TEXT,
            incident_id TEXT
        )
        """,

        "audit_logs": """
        CREATE TABLE IF NOT EXISTS audit_logs(
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_type TEXT,
            reference_id TEXT,
            action TEXT,
            details TEXT,
            activity_time TEXT
        )
        """,

        "incident_status_history": """
        CREATE TABLE IF NOT EXISTS incident_status_history(
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT,
            previous_status TEXT,
            new_status TEXT,
            updated_by TEXT,
            resolution_notes TEXT,
            status_change_time TEXT
        )
        """,

        "incident_sla": """
        CREATE TABLE IF NOT EXISTS incident_sla(
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
        """,

        "support_tasks": """
        CREATE TABLE IF NOT EXISTS support_tasks(
            task_id TEXT PRIMARY KEY,
            task_type TEXT,
            priority TEXT,
            requested_by TEXT,
            status TEXT,
            assigned_team TEXT,
            description TEXT,
            due_datetime TEXT,
            completed_datetime TEXT,
            related_incident TEXT,
            created_at TEXT
        )
        """,

        "communications": """
        CREATE TABLE IF NOT EXISTS communications(
            comm_id TEXT PRIMARY KEY,
            incident_id TEXT,
            contact_type TEXT,
            contact_name TEXT,
            communication_type TEXT,
            subject TEXT,
            notes TEXT,
            next_action TEXT,
            communication_time TEXT
        )
        """,

        "daily_logs": """
        CREATE TABLE IF NOT EXISTS daily_logs(
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT,
            shift TEXT,
            owner TEXT,
            summary TEXT,
            pending_items TEXT,
            created_at TEXT
        )
        """,

        "handover_logs": """
        CREATE TABLE IF NOT EXISTS handover_logs(
            handover_id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT,
            from_shift TEXT,
            to_shift TEXT,
            handed_over_by TEXT,
            received_by TEXT,
            open_items TEXT,
            critical_watch TEXT,
            next_actions TEXT,
            created_at TEXT
        )
        """,

        "knowledge_base": """
        CREATE TABLE IF NOT EXISTS knowledge_base(
            kb_id TEXT PRIMARY KEY,
            category TEXT,
            title TEXT,
            procedure TEXT,
            owner TEXT,
            version TEXT,
            status TEXT,
            updated_at TEXT
        )
        """,

        "uat_training": """
        CREATE TABLE IF NOT EXISTS uat_training(
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_type TEXT,
            reference_id TEXT,
            application TEXT,
            owner TEXT,
            status TEXT,
            details TEXT,
            outcome TEXT,
            record_date TEXT
        )
        """,

        "announcements": """
        CREATE TABLE IF NOT EXISTS announcements(
            announcement_id TEXT PRIMARY KEY,
            release_id TEXT,
            application TEXT,
            announcement_type TEXT,
            subject TEXT,
            message TEXT,
            audience TEXT,
            status TEXT,
            sent_at TEXT
        )
        """
    }

    for sql in tables.values():
        cursor.execute(sql)

    # Migration safety for existing DB
    for table, col in [
        ("alert_investigations", "incident_id"),
        ("releases", "incident_id")
    ]:
        cols = [
            r[1]
            for r in cursor.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()
        ]

        if col not in cols:
            cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN {col} TEXT"
            )

    conn.commit()


init_db()


# =========================================================
# SEED DATA
# =========================================================

if count("SELECT COUNT(*) FROM incidents") == 0:

    cursor.executemany(
        "INSERT INTO incidents VALUES(?,?,?,?,?,?,?)",
        [
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
    )


if count("SELECT COUNT(*) FROM service_requests") == 0:

    cursor.executemany(
        "INSERT INTO service_requests VALUES(?,?,?,?,?,?,?)",
        [
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
    )


if count("SELECT COUNT(*) FROM shipments") == 0:

    cursor.executemany(
        "INSERT INTO shipments VALUES(?,?,?,?,?,?,?)",
        [
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
    )


for r in pd.read_sql_query(
    "SELECT incident_id,severity FROM incidents",
    conn
).itertuples(index=False):

    ensure_sla(
        r.incident_id,
        r.severity
    )


conn.commit()


# =========================================================
# STATIC ALERT DATA
# =========================================================

alerts_df = pd.DataFrame(
    {
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
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🚢 MOL CargoFlow")
st.sidebar.caption(
    "Application Support Operations Portal"
)

menu = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Operations Dashboard",
        "🚨 Incident Management",
        "🔔 Alert Monitoring",
        "🗄️ SQL & DB Troubleshooting",
        "🔍 RCA & Investigation",
        "🎫 Support Requests",
        "🤝 Communication & Coordination",
        "🚀 Release & Announcements",
        "📝 Daily Log & Handover",
        "📚 SOP / UAT / Training",
        "🔄 Incident 360 View",
        "📜 Audit Trail",
        "📈 Reports"
    ],
    index=0
)

st.sidebar.divider()

st.sidebar.caption(
    f"IST: {now()}"
)

st.sidebar.caption(
    "SQLite • Persistent Data • Audit Enabled"
)

st.title("🚢 MOL CargoFlow")

st.caption(
    "Shipping & Logistics Application Support Simulation • Global Support Team"
)


# =========================================================
# DASHBOARD
# =========================================================

def dashboard():

    active = count(
        "SELECT COUNT(*) FROM incidents "
        "WHERE status NOT IN ('Resolved','Closed')"
    )

    open_sr = count(
        "SELECT COUNT(*) FROM service_requests "
        "WHERE status NOT IN ('Resolved','Closed')"
    )

    open_tasks = count(
        "SELECT COUNT(*) FROM support_tasks "
        "WHERE status NOT IN ('Completed','Closed')"
    )

    alerts = int(
        (alerts_df.Status != "Resolved").sum()
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Application",
        "🟢 UP"
    )

    c2.metric(
        "Active Incidents",
        active
    )

    c3.metric(
        "Open Requests",
        open_sr
    )

    c4.metric(
        "Active Alerts",
        alerts
    )

    c5.metric(
        "Open Tasks",
        open_tasks
    )

    st.divider()

    st.subheader("🔧 Core Services")

    a, b, c = st.columns(3)

    a.success(
        "🟢 Booking Service\n\nOperational"
    )

    b.success(
        "🟢 Tracking Service\n\nOperational"
    )

    c.warning(
        "🟡 Payment Service\n\nDegraded Performance"
    )

    st.subheader("🚨 Current Support Queue")

    q = pd.read_sql_query(
        """
        SELECT
            incident_id AS 'Incident ID',
            severity AS Severity,
            application AS Application,
            status AS Status,
            assigned_team AS 'Assigned Team'
        FROM incidents
        WHERE status NOT IN ('Resolved','Closed')
        ORDER BY rowid DESC
        """,
        conn
    )

    st.dataframe(
        q,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("🔔 Alert Watchlist")

    st.dataframe(
        alerts_df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("📋 Recent Activity")

    act = pd.read_sql_query(
        """
        SELECT
            activity_type AS 'Type',
            reference_id AS 'Reference',
            action AS Action,
            activity_time AS 'Time'
        FROM audit_logs
        ORDER BY activity_id DESC
        LIMIT 8
        """,
        conn
    )

    st.dataframe(
        act,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# INCIDENT MANAGEMENT
# =========================================================

def incidents():

    st.header("🚨 Incident Management")

    with st.form(
        "incident_form",
        clear_on_submit=True
    ):

        c1, c2 = st.columns(2)

        with c1:

            iid = st.text_input(
                "Incident ID",
                placeholder="Example: INC-1006"
            )

            iid_e = st.empty()

            sev = st.selectbox(
                "Severity",
                ["Select Severity"] + list(SLA_TARGETS)
            )

            sev_e = st.empty()

            app = st.selectbox(
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

            app_e = st.empty()

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

            status_e = st.empty()

        with c2:

            team = st.selectbox(
                "Assigned Team",
                [
                    "Select Team",
                    "Application Support",
                    "Development Team",
                    "Database Support",
                    "Infrastructure Team",
                    "System Support"
                ]
            )

            team_e = st.empty()

            desc = st.text_area(
                "Incident Description",
                placeholder="Describe the production issue..."
            )

            desc_e = st.empty()

            impact = st.text_area(
                "Business Impact",
                placeholder="Describe operational/user impact..."
            )

            impact_e = st.empty()

        submit = st.form_submit_button(
            "🚨 Create Incident"
        )

    if submit:

        errs = False

        for val, ph in [
            (iid, iid_e),
            (desc, desc_e),
            (impact, impact_e)
        ]:

            if not esc(val):

                ph.error(
                    "⚠ This field is required."
                )

                errs = True

        for val, ph, msg in [
            (sev, sev_e, "Severity"),
            (app, app_e, "Application / Service"),
            (status, status_e, "Status"),
            (team, team_e, "Assigned Team")
        ]:

            if val.startswith("Select"):

                ph.error(
                    f"⚠ Please select {msg}."
                )

                errs = True

        if not errs:

            try:

                t = now()

                cursor.execute(
                    "INSERT INTO incidents VALUES(?,?,?,?,?,?,?)",
                    (
                        esc(iid),
                        sev,
                        app,
                        status,
                        team,
                        esc(desc),
                        esc(impact)
                    )
                )

                ensure_sla(
                    esc(iid),
                    sev,
                    t
                )

                audit(
                    "Incident",
                    esc(iid),
                    "Incident Created",
                    f"{sev} incident created for {app}."
                )

                conn.commit()

                st.success(
                    f"{esc(iid)} created successfully."
                )

                st.rerun()

            except sqlite3.IntegrityError:

                conn.rollback()

                iid_e.error(
                    f"⚠ Incident ID '{esc(iid)}' already exists."
                )

            except Exception as e:

                conn.rollback()

                st.error(str(e))

    st.subheader(
        "🔄 Status Update / Resolution"
    )

    opts = incident_options()

    selected = st.selectbox(
        "Select Incident",
        opts,
        key="inc_update"
    )

    if selected != "Select Incident":

        r = pd.read_sql_query(
            "SELECT * FROM incidents "
            "WHERE incident_id=?",
            conn,
            params=(selected,)
        ).iloc[0]

        with st.container(border=True):

            st.write(
                f"**{r.incident_id}** • "
                f"{r.severity} • "
                f"{r.application} • "
                f"**{r.status}** • "
                f"{r.assigned_team}"
            )

            st.write(
                f"**Description:** {r.description}"
            )

            st.write(
                f"**Business Impact:** "
                f"{r.business_impact}"
            )

        with st.form(
            "status_form",
            clear_on_submit=True
        ):

            ns = st.selectbox(
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

            ns_e = st.empty()

            by = st.text_input(
                "Updated By",
                placeholder="Application Support"
            )

            by_e = st.empty()

            notes = st.text_area(
                "Status Update / Resolution Notes",
                placeholder="Document action, investigation or resolution..."
            )

            notes_e = st.empty()

            go = st.form_submit_button(
                "🔄 Update Incident Status"
            )

        if go:

            bad = False

            if ns.startswith("Select"):

                ns_e.error(
                    "⚠ Please select a new status."
                )

                bad = True

            if not esc(by):

                by_e.error(
                    "⚠ Updated By is required."
                )

                bad = True

            if not esc(notes):

                notes_e.error(
                    "⚠ Status Update / Resolution Notes are required."
                )

                bad = True

            if ns == r.status:

                ns_e.error(
                    f"⚠ Incident is already '{r.status}'."
                )

                bad = True

            if not bad:

                try:

                    t = now()

                    cursor.execute(
                        "UPDATE incidents SET status=? "
                        "WHERE incident_id=?",
                        (ns, selected)
                    )

                    cursor.execute(
                        """
                        INSERT INTO incident_status_history(
                            incident_id,
                            previous_status,
                            new_status,
                            updated_by,
                            resolution_notes,
                            status_change_time
                        )
                        VALUES(?,?,?,?,?,?)
                        """,
                        (
                            selected,
                            r.status,
                            ns,
                            esc(by),
                            esc(notes),
                            t
                        )
                    )

                    ensure_sla(
                        selected,
                        r.severity
                    )

                    cursor.execute(
                        """
                        UPDATE incident_sla
                        SET
                            first_response_time=
                                COALESCE(first_response_time,?),
                            resolution_time=
                                CASE
                                    WHEN ? IN ('Resolved','Closed')
                                    THEN COALESCE(resolution_time,?)
                                    ELSE resolution_time
                                END,
                            last_updated=?
                        WHERE incident_id=?
                        """,
                        (
                            t,
                            ns,
                            t,
                            t,
                            selected
                        )
                    )

                    s = pd.read_sql_query(
                        "SELECT * FROM incident_sla "
                        "WHERE incident_id=?",
                        conn,
                        params=(selected,)
                    ).iloc[0]

                    ss = sla_status(
                        s.incident_created_time,
                        s.resolution_time,
                        int(s.sla_target_minutes)
                    )

                    er = (
                        "Yes"
                        if ss == "SLA Breached"
                        else "No"
                    )

                    lvl = (
                        get_escalation_level(r.severity)
                        if er == "Yes"
                        else "None"
                    )

                    cursor.execute(
                        """
                        UPDATE incident_sla
                        SET
                            sla_status=?,
                            escalation_required=?,
                            escalation_level=?,
                            last_updated=?
                        WHERE incident_id=?
                        """,
                        (
                            ss,
                            er,
                            lvl,
                            t,
                            selected
                        )
                    )

                    audit(
                        "Incident",
                        selected,
                        "Incident Status Updated",
                        f"{r.status} → {ns}. "
                        f"Updated by {esc(by)}. "
                        f"Notes: {esc(notes)}"
                    )

                    conn.commit()

                    st.success(
                        f"{selected} updated successfully."
                    )

                    st.rerun()

                except Exception as e:

                    conn.rollback()

                    st.error(str(e))

    st.subheader("📋 Incident History")

    df = pd.read_sql_query(
        """
        SELECT
            incident_id AS 'Incident ID',
            severity AS Severity,
            application AS Application,
            status AS Status,
            assigned_team AS 'Assigned Team',
            description AS Description,
            business_impact AS 'Business Impact'
        FROM incidents
        ORDER BY rowid DESC
        """,
        conn
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("📜 Status History")

    h = pd.read_sql_query(
        """
        SELECT
            incident_id AS 'Incident ID',
            previous_status AS 'Previous Status',
            new_status AS 'New Status',
            updated_by AS 'Updated By',
            resolution_notes AS Notes,
            status_change_time AS 'Changed At'
        FROM incident_status_history
        ORDER BY history_id DESC
        """,
        conn
    )

    st.dataframe(
        h,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# ALERTS
# =========================================================

def alerts():

    st.header(
        "🔔 Alert Monitoring & Investigation"
    )

    st.write(
        "Monitor production alerts, document investigation "
        "and take corrective/escalation action."
    )

    st.dataframe(
        alerts_df,
        use_container_width=True,
        hide_index=True
    )

    with st.form(
        "alert_form",
        clear_on_submit=True
    ):

        aid = st.selectbox(
            "Select Alert",
            ["Select Alert"] + alerts_df["Alert ID"].tolist()
        )

        aid_e = st.empty()

        inc = st.selectbox(
            "Related Incident",
            incident_options()
        )

        inc_e = st.empty()

        notes = st.text_area(
            "Investigation Notes",
            placeholder="Check logs, API metrics, DB connections, error patterns..."
        )

        notes_e = st.empty()

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

        action_e = st.empty()

        save = st.form_submit_button(
            "🔧 Investigate & Save Alert"
        )

    if save:

        bad = False

        for val, ph, msg in [
            (aid, aid_e, "Alert"),
            (inc, inc_e, "Related Incident"),
            (action, action_e, "Recommended Action")
        ]:

            if val.startswith("Select"):

                ph.error(
                    f"⚠ Please select {msg}."
                )

                bad = True

        if not esc(notes):

            notes_e.error(
                "⚠ Investigation Notes are required."
            )

            bad = True

        if not bad:

            try:

                r = alerts_df[
                    alerts_df["Alert ID"] == aid
                ].iloc[0]

                cursor.execute(
                    """
                    INSERT INTO alert_investigations(
                        alert_id,
                        service,
                        severity,
                        alert,
                        investigation_notes,
                        recommended_action,
                        incident_id
                    )
                    VALUES(?,?,?,?,?,?,?)
                    """,
                    (
                        aid,
                        r.Service,
                        r.Severity,
                        r.Alert,
                        esc(notes),
                        action,
                        inc
                    )
                )

                audit(
                    "Alert Investigation",
                    aid,
                    "Alert Investigated",
                    f"{r.Service} investigated and linked to {inc}."
                )

                conn.commit()

                st.success(
                    f"{aid} investigation saved."
                )

                st.rerun()

            except Exception as e:

                conn.rollback()

                st.error(str(e))

    st.subheader("📋 Investigation History")

    df = pd.read_sql_query(
        """
        SELECT
            investigation_id AS 'Investigation ID',
            alert_id AS 'Alert ID',
            incident_id AS 'Related Incident',
            service AS Service,
            severity AS Severity,
            investigation_notes AS Notes,
            recommended_action AS 'Recommended Action'
        FROM alert_investigations
        ORDER BY investigation_id DESC
        """,
        conn
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# SQL & DATABASE TROUBLESHOOTING
# =========================================================

def sql_tool():

    st.header(
        "🗄️ SQL & Database Troubleshooting"
    )

    st.caption(
        "Read-only SQL console for primary analysis of shipment, booking and payment issues."
    )

    df = pd.read_sql_query(
        """
        SELECT
            shipment_id AS 'Shipment ID',
            customer_name AS 'Customer Name',
            origin AS Origin,
            destination AS Destination,
            status AS Status,
            payment_status AS 'Payment Status',
            amount AS Amount
        FROM shipments
        """,
        conn
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    inc = st.selectbox(
        "Related Incident",
        incident_options(),
        key="sql_inc"
    )

    inc_e = st.empty()

    q = st.text_area(
        "SQL Query",
        value="SELECT * FROM shipments;",
        height=120
    )

    q_e = st.empty()

    if st.button(
        "▶️ Execute Read-only Query"
    ):

        bad = False

        if inc == "Select Incident":

            inc_e.error(
                "⚠ Please select a Related Incident."
            )

            bad = True

        clean = esc(q)

        if not clean:

            q_e.error(
                "⚠ SQL Query is required."
            )

            bad = True

        elif not clean.upper().startswith(
            ("SELECT", "WITH", "PRAGMA")
        ):

            q_e.error(
                "⚠ Only SELECT, WITH and PRAGMA queries are allowed."
            )

            bad = True

        if not bad:

            try:

                out = pd.read_sql_query(
                    clean,
                    conn
                )

                st.success(
                    "Query executed successfully."
                )

                st.dataframe(
                    out,
                    use_container_width=True
                )

                audit(
                    "SQL Investigation",
                    inc,
                    "SQL Query Executed",
                    f"Read-only query: {clean}"
                )

                conn.commit()

            except Exception as e:

                conn.rollback()

                q_e.error(
                    f"SQL Error: {e}"
                )


# =========================================================
# RCA
# =========================================================

def rca():

    st.header(
        "🔍 Root Cause Analysis & Investigation"
    )

    with st.form(
        "rca_form",
        clear_on_submit=True
    ):

        inc = st.selectbox(
            "Incident ID",
            incident_options(),
            key="rca_inc"
        )

        inc_e = st.empty()

        labels = [
            (
                "Observed Symptom",
                "Describe what users/operations observed..."
            ),
            (
                "Investigation Performed",
                "Logs, SQL, API checks, monitoring..."
            ),
            (
                "Root Cause",
                "Document evidence-based root cause..."
            ),
            (
                "Resolution",
                "Document corrective action..."
            ),
            (
                "Preventive Action",
                "Document how recurrence will be prevented..."
            )
        ]

        vals = []
        errs = []

        for label, ph in labels:

            v = st.text_area(
                label,
                placeholder=ph
            )

            vals.append(v)

            errs.append(
                st.empty()
            )

        save = st.form_submit_button(
            "🔍 Save RCA"
        )

    if save:

        bad = inc.startswith("Select")

        if bad:

            inc_e.error(
                "⚠ Please select an Incident."
            )

        for v, e, (label, _) in zip(
            vals,
            errs,
            labels
        ):

            if not esc(v):

                e.error(
                    f"⚠ {label} is required."
                )

                bad = True

        if not bad:

            try:

                cursor.execute(
                    """
                    INSERT INTO rca_records(
                        incident_id,
                        observed_symptom,
                        investigation,
                        root_cause,
                        resolution,
                        prevention
                    )
                    VALUES(?,?,?,?,?,?)
                    """,
                    (
                        inc,
                        *map(esc, vals)
                    )
                )

                rid = cursor.lastrowid

                audit(
                    "RCA",
                    inc,
                    "RCA Recorded",
                    f"RCA-{rid} documented for {inc}."
                )

                conn.commit()

                st.success(
                    f"RCA-{rid} recorded."
                )

                st.rerun()

            except Exception as e:

                conn.rollback()

                st.error(str(e))

    st.subheader("📋 RCA History")

    df = pd.read_sql_query(
        """
        SELECT
            rca_id AS 'RCA ID',
            incident_id AS 'Incident ID',
            observed_symptom AS Symptom,
            investigation AS Investigation,
            root_cause AS 'Root Cause',
            resolution AS Resolution,
            prevention AS 'Preventive Action'
        FROM rca_records
        ORDER BY rca_id DESC
        """,
        conn
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# SUPPORT REQUESTS
# =========================================================

def requests():

    st.header(
        "🎫 Support Requests"
    )

    st.write(
        "Manage functional support requests, Code Registration, "
        "Data Provision and user service tasks."
    )

    with st.form(
        "support_form",
        clear_on_submit=True
    ):

        c1, c2 = st.columns(2)

        with c1:

            rid = st.text_input(
                "Request / Task ID",
                placeholder="SR-3006 / CR-2026-001"
            )

            rid_e = st.empty()

            typ = st.selectbox(
                "Request Type",
                [
                    "Select Type",
                    "Code Registration",
                    "Data Provision",
                    "Access Request",
                    "Password Reset",
                    "Report Request",
                    "Data Correction",
                    "Application Configuration",
                    "General User Query"
                ]
            )

            typ_e = st.empty()

            pri = st.selectbox(
                "Priority",
                [
                    "Select Priority",
                    "High",
                    "Medium",
                    "Low"
                ]
            )

            pri_e = st.empty()

            by = st.text_input(
                "Requested By",
                placeholder="MOL User / Operations Team"
            )

            by_e = st.empty()

        with c2:

            team = st.selectbox(
                "Assigned Team",
                [
                    "Select Team",
                    "Application Support",
                    "Development Team",
                    "Database Support",
                    "Infrastructure Team",
                    "Security Team",
                    "System Support"
                ]
            )

            team_e = st.empty()

            status = st.selectbox(
                "Status",
                [
                    "Select Status",
                    "New",
                    "In Progress",
                    "Pending Approval",
                    "Completed",
                    "Resolved",
                    "Closed"
                ]
            )

            status_e = st.empty()

            due_default = datetime.now(
                IST
            ).replace(
                second=0,
                microsecond=0
            )

            due_date = st.date_input(
                "Due Date (IST)",
                value=due_default.date()
            )

            due_date_e = st.empty()

            due_time = st.time_input(
                "Due Time (IST)",
                value=due_default.time()
            )

            due_time_e = st.empty()

        inc = st.selectbox(
            "Related Incident (Optional)",
            incident_options()
        )

        inc_e = st.empty()

        detail_label = (
            "Code Registration / Data Provision Details"
            if typ in [
                "Code Registration",
                "Data Provision"
            ]
            else
            "Task / Request Details"
        )

        desc = st.text_area(
            detail_label,
            placeholder=(
                "Code Registration: application/code name, "
                "business purpose, validation needed...\n"
                "Data Provision: data required, source, "
                "business purpose, required date..."
            )
        )

        desc_e = st.empty()

        submit = st.form_submit_button(
            "🎫 Create Support Task"
        )

    if submit:

        bad = False

        for v, e, msg in [
            (rid, rid_e, "Request / Task ID"),
            (by, by_e, "Requested By"),
            (desc, desc_e, detail_label)
        ]:

            if not esc(v):

                e.error(
                    f"⚠ {msg} is required."
                )

                bad = True

        for v, e, msg in [
            (typ, typ_e, "Request Type"),
            (pri, pri_e, "Priority"),
            (team, team_e, "Assigned Team"),
            (status, status_e, "Status")
        ]:

            if v.startswith("Select"):

                e.error(
                    f"⚠ Please select {msg}."
                )

                bad = True

        due_dt = datetime.combine(
            due_date,
            due_time
        ).replace(
            tzinfo=IST
        )

        if due_dt < datetime.now(IST).replace(
            second=0,
            microsecond=0
        ):

            due_date_e.error(
                "⚠ Due Date/Time cannot be in the past."
            )

            bad = True

        if not bad:

            try:

                t = now()

                related = (
                    None
                    if inc == "Select Incident"
                    else inc
                )

                due_value = due_dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                cursor.execute(
                    "INSERT INTO support_tasks VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        esc(rid),
                        typ,
                        pri,
                        esc(by),
                        status,
                        team,
                        esc(desc),
                        due_value,
                        None,
                        related,
                        t
                    )
                )

                audit(
                    "Support Request",
                    esc(rid),
                    "Support Task Created",
                    f"{typ} created for {esc(by)}"
                    + (
                        f" and linked to {related}."
                        if related
                        else "."
                    )
                )

                conn.commit()

                st.success(
                    f"{esc(rid)} created successfully."
                )

                st.rerun()

            except sqlite3.IntegrityError:

                conn.rollback()

                rid_e.error(
                    f"⚠ ID '{esc(rid)}' already exists."
                )

            except Exception as e:

                conn.rollback()

                st.error(str(e))

    st.subheader(
        "📋 Support Queue"
    )

    df = pd.read_sql_query(
        """
        SELECT
            task_id AS 'Task ID',
            task_type AS 'Type',
            priority AS Priority,
            requested_by AS 'Requested By',
            status AS Status,
            assigned_team AS 'Assigned Team',
            due_datetime AS 'Due (IST)',
            related_incident AS 'Related Incident',
            created_at AS 'Created At'
        FROM support_tasks
        ORDER BY rowid DESC
        """,
        conn
    )

    if not df.empty:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No support requests or tasks recorded yet."
        )


# =========================================================
# COMMUNICATION
# =========================================================

def communication():

    st.header(
        "🤝 Communication & Stakeholder Coordination"
    )

    st.caption(
        "Document direct contact with MOL Users, Development "
        "and System Support teams."
    )

    with st.form(
        "comm_form",
        clear_on_submit=True
    ):

        cid = st.text_input(
            "Communication ID",
            placeholder="COM-2026-001"
        )

        cid_e = st.empty()

        inc = st.selectbox(
            "Related Incident",
            incident_options()
        )

        inc_e = st.empty()

        c1, c2 = st.columns(2)

        with c1:

            ct = st.selectbox(
                "Contact Type",
                [
                    "Select Contact",
                    "MOL User",
                    "Development Team",
                    "System Support",
                    "Database Support",
                    "Infrastructure Team",
                    "Other"
                ]
            )

            ct_e = st.empty()

            name = st.text_input(
                "Contact / Stakeholder Name",
                placeholder="Team or user name"
            )

            name_e = st.empty()

        with c2:

            mt = st.selectbox(
                "Communication Type",
                [
                    "Select Type",
                    "Email",
                    "Phone",
                    "Teams / Chat",
                    "Meeting",
                    "Ticket Update"
                ]
            )

            mt_e = st.empty()

            subject = st.text_input(
                "Subject",
                placeholder="Payment API investigation update"
            )

            subject_e = st.empty()

        notes = st.text_area(
            "Communication / Findings",
            placeholder="What was communicated, requested or confirmed?"
        )

        notes_e = st.empty()

        nxt = st.text_area(
            "Next Action / Follow-up",
            placeholder="Development to check API logs by 16:00 IST..."
        )

        nxt_e = st.empty()

        go = st.form_submit_button(
            "🤝 Log Communication"
        )

    if go:

        bad = False

        for v, e, msg in [
            (cid, cid_e, "Communication ID"),
            (name, name_e, "Contact / Stakeholder Name"),
            (subject, subject_e, "Subject"),
            (notes, notes_e, "Communication / Findings"),
            (nxt, nxt_e, "Next Action / Follow-up")
        ]:

            if not esc(v):

                e.error(
                    f"⚠ {msg} is required."
                )

                bad = True

        for v, e, msg in [
            (inc, inc_e, "Related Incident"),
            (ct, ct_e, "Contact Type"),
            (mt, mt_e, "Communication Type")
        ]:

            if v.startswith("Select"):

                e.error(
                    f"⚠ Please select {msg}."
                )

                bad = True

        if not bad:

            try:

                t = now()

                cursor.execute(
                    "INSERT INTO communications VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        esc(cid),
                        inc,
                        ct,
                        esc(name),
                        mt,
                        esc(subject),
                        esc(notes),
                        esc(nxt),
                        t
                    )
                )

                audit(
                    "Communication",
                    inc,
                    "Stakeholder Contact Logged",
                    f"{ct} contacted regarding {esc(subject)}."
                )

                conn.commit()

                st.success(
                    "Communication logged."
                )

                st.rerun()

            except sqlite3.IntegrityError:

                conn.rollback()

                cid_e.error(
                    "⚠ Communication ID already exists."
                )

            except Exception as e:

                conn.rollback()

                st.error(str(e))

    st.subheader(
        "📋 Communication History"
    )

    df = pd.read_sql_query(
        """
        SELECT
            comm_id AS 'Communication ID',
            incident_id AS 'Incident ID',
            contact_type AS 'Contact Type',
            contact_name AS Stakeholder,
            communication_type AS Channel,
            subject AS Subject,
            next_action AS 'Next Action',
            communication_time AS 'Time'
        FROM communications
        ORDER BY communication_time DESC
        """,
        conn
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# RELEASE & ANNOUNCEMENTS
# =========================================================

def releases():

    st.header(
        "🚀 Release, Data Patch & User Announcement"
    )

    with st.form(
        "release_form",
        clear_on_submit=True
    ):

        c1, c2 = st.columns(2)

        with c1:

            rid = st.text_input(
                "Release / Patch ID",
                placeholder="REL-2026-002"
            )

            rid_e = st.empty()

            ver = st.text_input(
                "Version / Patch",
                placeholder="v2.4.2 / DP-2026-07"
            )

            ver_e = st.empty()

            env = st.selectbox(
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

            env_e = st.empty()

            stat = st.selectbox(
                "Status",
                [
                    "Select Status",
                    "Planned",
                    "In Progress",
                    "Successful",
                    "Failed",
                    "Rolled Back"
                ]
            )

            stat_e = st.empty()

            owner = st.text_input(
                "Release Owner",
                placeholder="Application Support / Development"
            )

            owner_e = st.empty()

            inc = st.selectbox(
                "Related Incident",
                incident_options()
            )

            inc_e = st.empty()

        with c2:

            d = st.date_input(
                "Deployment Date",
                value=datetime.now(IST).date()
            )

            tm = st.time_input(
                "Deployment Time",
                value=datetime.now(IST).time().replace(
                    second=0,
                    microsecond=0
                )
            )

            summary = st.text_area(
                "Change Summary",
                placeholder="Functional fix / data patch / program release..."
            )

            summary_e = st.empty()

            rollback = st.text_area(
                "Rollback Plan",
                placeholder="Rollback steps and validation..."
            )

            rollback_e = st.empty()

            outcome = st.text_area(
                "Release Outcome",
                placeholder="Deployment result and validation..."
            )

            outcome_e = st.empty()

        go = st.form_submit_button(
            "🚀 Save Release"
        )

    if go:

        bad = False

        for v, e, msg in [
            (rid, rid_e, "Release / Patch ID"),
            (ver, ver_e, "Version / Patch"),
            (owner, owner_e, "Release Owner"),
            (summary, summary_e, "Change Summary"),
            (rollback, rollback_e, "Rollback Plan"),
            (outcome, outcome_e, "Release Outcome")
        ]:

            if not esc(v):

                e.error(
                    f"⚠ {msg} is required."
                )

                bad = True

        for v, e, msg in [
            (env, env_e, "Environment"),
            (stat, stat_e, "Release Status"),
            (inc, inc_e, "Related Incident")
        ]:

            if v.startswith("Select"):

                e.error(
                    f"⚠ Please select {msg}."
                )

                bad = True

        if not bad:

            try:

                dt = datetime.combine(
                    d,
                    tm
                ).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                cursor.execute(
                    "INSERT INTO releases VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        esc(rid),
                        esc(ver),
                        env,
                        stat,
                        esc(owner),
                        dt,
                        esc(summary),
                        esc(rollback),
                        esc(outcome),
                        inc
                    )
                )

                audit(
                    "Release",
                    esc(rid),
                    "Release Created",
                    f"{esc(ver)} deployed to {env}; linked to {inc}."
                )

                conn.commit()

                st.success(
                    "Release recorded."
                )

                st.rerun()

            except sqlite3.IntegrityError:

                conn.rollback()

                rid_e.error(
                    "⚠ Release ID already exists."
                )

            except Exception as e:

                conn.rollback()

                st.error(str(e))

    st.subheader(
        "📋 Release History"
    )

    df = pd.read_sql_query(
        """
        SELECT
            release_id AS 'Release ID',
            version AS Version,
            environment AS Environment,
            status AS Status,
            release_owner AS Owner,
            incident_id AS 'Related Incident',
            deployment_datetime AS 'Deployment IST',
            release_outcome AS Outcome
        FROM releases
        ORDER BY rowid DESC
        """,
        conn
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader(
        "📣 User Announcement"
    )

    with st.form(
        "announcement_form",
        clear_on_submit=True
    ):

        aid = st.text_input(
            "Announcement ID",
            placeholder="ANN-2026-001"
        )

        aid_e = st.empty()

        rel = st.text_input(
            "Related Release / Patch ID",
            placeholder="REL-2026-002"
        )

        rel_e = st.empty()

        app = st.text_input(
            "Application",
            placeholder="CargoFlow Tracking"
        )

        app_e = st.empty()

        typ = st.selectbox(
            "Announcement Type",
            [
                "Select Type",
                "Maintenance",
                "System Update",
                "Program Release",
                "Usage Restriction",
                "Data Patch"
            ]
        )

        typ_e = st.empty()

        sub = st.text_input(
            "Subject",
            placeholder="Planned maintenance - Tracking unavailable"
        )

        sub_e = st.empty()

        msg = st.text_area(
            "Announcement Message",
            placeholder="Inform users about timing, impact and restrictions..."
        )

        msg_e = st.empty()

        aud = st.text_input(
            "Audience",
            placeholder="MOL Operations Users"
        )

        aud_e = st.empty()

        stt = st.selectbox(
            "Status",
            [
                "Select Status",
                "Draft",
                "Approved",
                "Sent"
            ]
        )

        stt_e = st.empty()

        save = st.form_submit_button(
            "📣 Save Announcement"
        )

    if save:

        bad = False

        for v, e, msgx in [
            (aid, aid_e, "Announcement ID"),
            (rel, rel_e, "Related Release / Patch ID"),
            (app, app_e, "Application"),
            (sub, sub_e, "Subject"),
            (msg, msg_e, "Announcement Message"),
            (aud, aud_e, "Audience")
        ]:

            if not esc(v):

                e.error(
                    f"⚠ {msgx} is required."
                )

                bad = True

        for v, e, msgx in [
            (typ, typ_e, "Announcement Type"),
            (stt, stt_e, "Status")
        ]:

            if v.startswith("Select"):

                e.error(
                    f"⚠ Please select {msgx}."
                )

                bad = True

        if not bad:

            try:

                cursor.execute(
                    "INSERT INTO announcements VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        esc(aid),
                        esc(rel),
                        esc(app),
                        typ,
                        esc(sub),
                        esc(msg),
                        esc(aud),
                        stt,
                        now()
                    )
                )

                audit(
                    "Announcement",
                    esc(aid),
                    "User Announcement Recorded",
                    f"{typ}: {esc(sub)}"
                )

                conn.commit()

                st.success(
                    "Announcement recorded."
                )

                st.rerun()

            except sqlite3.IntegrityError:

                conn.rollback()

                aid_e.error(
                    "⚠ Announcement ID already exists."
                )

            except Exception as e:

                conn.rollback()

                st.error(str(e))

    ad = pd.read_sql_query(
        """
        SELECT
            announcement_id AS 'Announcement ID',
            release_id AS 'Release/Patch',
            application AS Application,
            announcement_type AS Type,
            subject AS Subject,
            audience AS Audience,
            status AS Status,
            sent_at AS 'Recorded At'
        FROM announcements
        ORDER BY rowid DESC
        """,
        conn
    )

    st.dataframe(
        ad,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# DAILY LOG & HANDOVER
# =========================================================

def daily():

    st.header(
        "📝 Daily Log & Shift Handover"
    )

    st.caption(
        "Operational log sheet and formal shift hand-over evidence."
    )

    with st.form(
        "daily_form",
        clear_on_submit=True
    ):

        d = st.date_input(
            "Log Date",
            value=datetime.now(IST).date()
        )

        shift = st.selectbox(
            "Shift",
            [
                "Select Shift",
                "Morning",
                "General",
                "Evening",
                "Night"
            ]
        )

        shift_e = st.empty()

        owner = st.text_input(
            "Support Engineer / Owner"
        )

        owner_e = st.empty()

        summary = st.text_area(
            "Daily Support Summary",
            placeholder="Incidents, requests, alerts, releases, monitoring..."
        )

        summary_e = st.empty()

        pending = st.text_area(
            "Pending Items",
            placeholder="Open issues and follow-ups for next shift..."
        )

        pending_e = st.empty()

        go = st.form_submit_button(
            "📝 Save Daily Log"
        )

    if go:

        bad = (
            shift.startswith("Select")
            or not esc(owner)
            or not esc(summary)
            or not esc(pending)
        )

        if shift.startswith("Select"):

            shift_e.error(
                "⚠ Please select a Shift."
            )

        if not esc(owner):

            owner_e.error(
                "⚠ Owner is required."
            )

        if not esc(summary):

            summary_e.error(
                "⚠ Daily Support Summary is required."
            )

        if not esc(pending):

            pending_e.error(
                "⚠ Pending Items are required."
            )

        if not bad:

            cursor.execute(
                """
                INSERT INTO daily_logs(
                    log_date,
                    shift,
                    owner,
                    summary,
                    pending_items,
                    created_at
                )
                VALUES(?,?,?,?,?,?)
                """,
                (
                    str(d),
                    shift,
                    esc(owner),
                    esc(summary),
                    esc(pending),
                    now()
                )
            )

            audit(
                "Daily Log",
                str(d),
                "Daily Log Updated",
                f"{shift} shift log by {esc(owner)}."
            )

            conn.commit()

            st.success(
                "Daily log saved."
            )

            st.rerun()

    with st.form(
        "handover_form",
        clear_on_submit=True
    ):

        d = st.date_input(
            "Handover Date",
            value=datetime.now(IST).date(),
            key="hd"
        )

        fs = st.selectbox(
            "From Shift",
            [
                "Select Shift",
                "Morning",
                "General",
                "Evening",
                "Night"
            ],
            key="fs"
        )

        fs_e = st.empty()

        ts = st.selectbox(
            "To Shift",
            [
                "Select Shift",
                "Morning",
                "General",
                "Evening",
                "Night"
            ],
            key="ts"
        )

        ts_e = st.empty()

        hb = st.text_input(
            "Handed Over By"
        )

        hb_e = st.empty()

        rb = st.text_input(
            "Received By"
        )

        rb_e = st.empty()

        oi = st.text_area(
            "Open Items"
        )

        oi_e = st.empty()

        cw = st.text_area(
            "Critical Watch / Alerts"
        )

        cw_e = st.empty()

        na = st.text_area(
            "Next Actions"
        )

        na_e = st.empty()

        go = st.form_submit_button(
            "🔄 Save Shift Handover"
        )

    if go:

        vals = [
            (fs, fs_e, "From Shift"),
            (ts, ts_e, "To Shift"),
            (hb, hb_e, "Handed Over By"),
            (rb, rb_e, "Received By"),
            (oi, oi_e, "Open Items"),
            (cw, cw_e, "Critical Watch / Alerts"),
            (na, na_e, "Next Actions")
        ]

        bad = False

        for v, e, msg in vals:

            if (
                isinstance(v, str)
                and (
                    v.startswith("Select")
                    or not esc(v)
                )
            ):

                e.error(
                    f"⚠ {msg} is required."
                )

                bad = True

        if not bad:

            cursor.execute(
                """
                INSERT INTO handover_logs(
                    log_date,
                    from_shift,
                    to_shift,
                    handed_over_by,
                    received_by,
                    open_items,
                    critical_watch,
                    next_actions,
                    created_at
                )
                VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    str(d),
                    fs,
                    ts,
                    esc(hb),
                    esc(rb),
                    esc(oi),
                    esc(cw),
                    esc(na),
                    now()
                )
            )

            audit(
                "Shift Handover",
                str(d),
                "Shift Handover Recorded",
                f"{fs} → {ts}; "
                f"{esc(hb)} to {esc(rb)}."
            )

            conn.commit()

            st.success(
                "Shift handover recorded."
            )

            st.rerun()

    st.subheader(
        "📋 Daily Logs"
    )

    st.dataframe(
        pd.read_sql_query(
            """
            SELECT
                log_date AS Date,
                shift AS Shift,
                owner AS Owner,
                summary AS Summary,
                pending_items AS 'Pending Items',
                created_at AS 'Created At'
            FROM daily_logs
            ORDER BY log_id DESC
            """,
            conn
        ),
        use_container_width=True,
        hide_index=True
    )

    st.subheader(
        "🔄 Handover History"
    )

    st.dataframe(
        pd.read_sql_query(
            """
            SELECT
                log_date AS Date,
                from_shift AS 'From Shift',
                to_shift AS 'To Shift',
                handed_over_by AS 'From Engineer',
                received_by AS 'To Engineer',
                critical_watch AS 'Critical Watch',
                next_actions AS 'Next Actions',
                created_at AS 'Created At'
            FROM handover_logs
            ORDER BY handover_id DESC
            """,
            conn
        ),
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# KNOWLEDGE BASE / UAT / TRAINING
# =========================================================

def knowledge():

    st.header(
        "📚 SOP / Knowledge Base / UAT / Training"
    )

    tab1, tab2 = st.tabs(
        [
            "📚 SOP / Knowledge Base",
            "🧪 UAT & Training"
        ]
    )

    # -----------------------------------------------------
    # SOP / KNOWLEDGE BASE
    # -----------------------------------------------------

    with tab1:

        with st.form(
            "kb_form",
            clear_on_submit=True
        ):

            kid = st.text_input(
                "SOP / KB ID",
                placeholder="SOP-TRK-001"
            )

            kid_e = st.empty()

            cat = st.selectbox(
                "Category",
                [
                    "Select Category",
                    "Incident Procedure",
                    "SQL Troubleshooting",
                    "Release Procedure",
                    "Data Provision",
                    "Code Registration",
                    "User Support",
                    "Shift Handover"
                ]
            )

            cat_e = st.empty()

            title = st.text_input(
                "Title"
            )

            title_e = st.empty()

            proc = st.text_area(
                "Standard Procedure",
                placeholder="Document step-by-step standard process...",
                height=220
            )

            proc_e = st.empty()

            owner = st.text_input(
                "Owner"
            )

            owner_e = st.empty()

            ver = st.text_input(
                "Version",
                placeholder="1.0"
            )

            ver_e = st.empty()

            status = st.selectbox(
                "Status",
                [
                    "Select Status",
                    "Draft",
                    "Approved",
                    "Active",
                    "Retired"
                ]
            )

            status_e = st.empty()

            go = st.form_submit_button(
                "📚 Save SOP / KB"
            )

        if go:

            bad = False

            for v, e, msg in [
                (kid, kid_e, "SOP / KB ID"),
                (title, title_e, "Title"),
                (proc, proc_e, "Standard Procedure"),
                (owner, owner_e, "Owner"),
                (ver, ver_e, "Version")
            ]:

                if not esc(v):

                    e.error(
                        f"⚠ {msg} is required."
                    )

                    bad = True

            for v, e, msg in [
                (cat, cat_e, "Category"),
                (status, status_e, "Status")
            ]:

                if v.startswith("Select"):

                    e.error(
                        f"⚠ Please select {msg}."
                    )

                    bad = True

            if not bad:

                try:

                    cursor.execute(
                        """
                        INSERT INTO knowledge_base(
                            kb_id,
                            category,
                            title,
                            procedure,
                            owner,
                            version,
                            status,
                            updated_at
                        )
                        VALUES(?,?,?,?,?,?,?,?)
                        """,
                        (
                            esc(kid),
                            cat,
                            esc(title),
                            esc(proc),
                            esc(owner),
                            esc(ver),
                            status,
                            now()
                        )
                    )

                    audit(
                        "Knowledge Base",
                        esc(kid),
                        "SOP Recorded",
                        esc(title)
                    )

                    conn.commit()

                    st.success(
                        "SOP / KB saved."
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    conn.rollback()

                    kid_e.error(
                        "⚠ ID already exists."
                    )

                except Exception as e:

                    conn.rollback()

                    st.error(str(e))

        # =================================================
        # UPDATED SOP TABLE
        # =================================================

        st.subheader(
            "📋 SOP / Knowledge Base Records"
        )

        kb_df = pd.read_sql_query(
            """
            SELECT
                kb_id AS 'SOP / KB ID',
                category AS Category,
                title AS Title,
                procedure AS 'Standard Procedure',
                owner AS Owner,
                version AS Version,
                status AS Status,
                updated_at AS 'Updated At'
            FROM knowledge_base
            ORDER BY updated_at DESC
            """,
            conn
        )

        if not kb_df.empty:

            st.dataframe(
                kb_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No SOP / KB records available yet."
            )

    # -----------------------------------------------------
    # UAT & TRAINING
    # -----------------------------------------------------

    with tab2:

        with st.form(
            "uat_form",
            clear_on_submit=True
        ):

            rt = st.selectbox(
                "Record Type",
                [
                    "Select Type",
                    "UAT Support",
                    "Training Support"
                ]
            )

            rt_e = st.empty()

            ref = st.text_input(
                "Reference ID",
                placeholder="UAT-2026-001"
            )

            ref_e = st.empty()

            app = st.text_input(
                "Application / Module"
            )

            app_e = st.empty()

            owner = st.text_input(
                "Owner / Coordinator"
            )

            owner_e = st.empty()

            status = st.selectbox(
                "Status",
                [
                    "Select Status",
                    "Planned",
                    "In Progress",
                    "Completed",
                    "Blocked"
                ]
            )

            status_e = st.empty()

            details = st.text_area(
                "Activity Details",
                placeholder="UAT scenario, user training topic, support provided..."
            )

            details_e = st.empty()

            outcome = st.text_area(
                "Outcome / Findings",
                placeholder="Result, defects, user feedback or completion..."
            )

            outcome_e = st.empty()

            go = st.form_submit_button(
                "🧪 Save UAT / Training Record"
            )

        if go:

            bad = False

            for v, e, msg in [
                (ref, ref_e, "Reference ID"),
                (app, app_e, "Application / Module"),
                (owner, owner_e, "Owner / Coordinator"),
                (details, details_e, "Activity Details"),
                (outcome, outcome_e, "Outcome / Findings")
            ]:

                if not esc(v):

                    e.error(
                        f"⚠ {msg} is required."
                    )

                    bad = True

            for v, e, msg in [
                (rt, rt_e, "Record Type"),
                (status, status_e, "Status")
            ]:

                if v.startswith("Select"):

                    e.error(
                        f"⚠ Please select {msg}."
                    )

                    bad = True

            if not bad:

                cursor.execute(
                    """
                    INSERT INTO uat_training(
                        record_type,
                        reference_id,
                        application,
                        owner,
                        status,
                        details,
                        outcome,
                        record_date
                    )
                    VALUES(?,?,?,?,?,?,?,?)
                    """,
                    (
                        rt,
                        esc(ref),
                        esc(app),
                        esc(owner),
                        status,
                        esc(details),
                        esc(outcome),
                        now()
                    )
                )

                audit(
                    rt,
                    esc(ref),
                    f"{rt} Recorded",
                    esc(outcome)
                )

                conn.commit()

                st.success(
                    "Record saved."
                )

                st.rerun()

        st.subheader(
            "📋 UAT / Training History"
        )

        st.dataframe(
            pd.read_sql_query(
                """
                SELECT
    record_id AS ID,
    record_type AS 'Record Type',
    reference_id AS 'Reference ID',
    application AS 'Application / Module',
    owner AS 'Owner / Coordinator',
    status AS Status,
    details AS 'Activity Details',
    outcome AS 'Outcome / Findings',
    record_date AS 'Record Date'
FROM uat_training
ORDER BY record_date DESC
                """,
                conn
            ),
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# INCIDENT 360
# =========================================================

def incident360():

    st.header(
        "🔄 Incident 360 View"
    )

    inc = st.selectbox(
        "Select Incident",
        incident_options(),
        key="i360"
    )

    if inc == "Select Incident":

        st.info(
            "Select an incident to trace its complete lifecycle."
        )

        return

    r = pd.read_sql_query(
        "SELECT * FROM incidents "
        "WHERE incident_id=?",
        conn,
        params=(inc,)
    ).iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Incident",
        r.incident_id
    )

    c2.metric(
        "Severity",
        r.severity
    )

    c3.metric(
        "Status",
        r.status
    )

    c4.metric(
        "Team",
        r.assigned_team
    )

    st.info(
        f"**Application:** {r.application}\n\n"
        f"**Description:** {r.description}\n\n"
        f"**Business Impact:** {r.business_impact}"
    )

    sections = [

        (
            "🔔 Alert Investigations",
            """
            SELECT
                alert_id AS 'Alert ID',
                service AS Service,
                severity AS Severity,
                investigation_notes AS Notes,
                recommended_action AS 'Recommended Action'
            FROM alert_investigations
            WHERE incident_id=?
            """
        ),

        (
            "🗄️ SQL Investigations",
            """
            SELECT
                activity_id AS ID,
                action AS Action,
                details AS Details,
                activity_time AS Time
            FROM audit_logs
            WHERE activity_type='SQL Investigation'
            AND reference_id=?
            """
        ),

        (
            "🔍 RCA",
            """
            SELECT
                rca_id AS ID,
                root_cause AS 'Root Cause',
                resolution AS Resolution,
                prevention AS 'Preventive Action'
            FROM rca_records
            WHERE incident_id=?
            """
        ),

        (
            "🚀 Releases",
            """
            SELECT
                release_id AS ID,
                version AS Version,
                environment AS Environment,
                status AS Status,
                deployment_datetime AS 'Deployment IST',
                release_outcome AS Outcome
            FROM releases
            WHERE incident_id=?
            """
        ),

        (
            "🤝 Communications",
            """
            SELECT
                comm_id AS ID,
                contact_type AS 'Contact Type',
                contact_name AS Stakeholder,
                subject AS Subject,
                next_action AS 'Next Action',
                communication_time AS Time
            FROM communications
            WHERE incident_id=?
            """
        )
    ]

    for title, sql in sections:

        st.subheader(title)

        d = pd.read_sql_query(
            sql,
            conn,
            params=(inc,)
        )

        if not d.empty:

            st.dataframe(
                d,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No linked records yet."
            )

    st.subheader(
        "📜 Related Audit"
    )

    d = pd.read_sql_query(
        """
        SELECT
            activity_type AS Type,
            action AS Action,
            details AS Details,
            activity_time AS Time
        FROM audit_logs
        WHERE reference_id=?
        ORDER BY activity_id DESC
        """,
        conn,
        params=(inc,)
    )

    if not d.empty:

        st.dataframe(
            d,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No related audit activity yet."
        )


# =========================================================
# AUDIT
# =========================================================

def audit_page():

    st.header(
        "📜 Audit Trail"
    )

    d = pd.read_sql_query(
        """
        SELECT
            activity_type AS 'Activity Type',
            reference_id AS 'Reference ID',
            action AS Action,
            details AS Details,
            activity_time AS 'Activity Time'
        FROM audit_logs
        ORDER BY activity_id DESC
        """,
        conn
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total",
        len(d)
    )

    c2.metric(
        "Incidents",
        count(
            "SELECT COUNT(*) FROM audit_logs "
            "WHERE activity_type='Incident'"
        )
    )

    c3.metric(
        "Investigations",
        count(
            """
            SELECT COUNT(*)
            FROM audit_logs
            WHERE activity_type IN (
                'SQL Investigation',
                'Alert Investigation',
                'RCA'
            )
            """
        )
    )

    c4.metric(
        "Operations",
        count(
            """
            SELECT COUNT(*)
            FROM audit_logs
            WHERE activity_type IN (
                'Release',
                'Support Request',
                'Communication',
                'Daily Log',
                'Shift Handover'
            )
            """
        )
    )

    if not d.empty:

        typ = st.selectbox(
            "Filter",
            ["All"] + sorted(
                d["Activity Type"].unique().tolist()
            )
        )

    else:

        typ = "All"

    if typ != "All":

        d = d[
            d["Activity Type"] == typ
        ]

    st.dataframe(
        d,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# REPORTS
# =========================================================

def reports():

    st.header(
        "📈 Support Metrics & Reports"
    )

    metrics = [
        (
            "Total Incidents",
            "SELECT COUNT(*) FROM incidents"
        ),
        (
            "Open Incidents",
            """
            SELECT COUNT(*)
            FROM incidents
            WHERE status NOT IN ('Resolved','Closed')
            """
        ),
        (
            "Service Requests",
            "SELECT COUNT(*) FROM service_requests"
        ),
        (
            "Support Tasks",
            "SELECT COUNT(*) FROM support_tasks"
        ),
        (
            "RCA Records",
            "SELECT COUNT(*) FROM rca_records"
        ),
        (
            "Releases/Patches",
            "SELECT COUNT(*) FROM releases"
        ),
        (
            "Communications",
            "SELECT COUNT(*) FROM communications"
        ),
        (
            "SOPs",
            "SELECT COUNT(*) FROM knowledge_base"
        ),
        (
            "UAT/Training",
            "SELECT COUNT(*) FROM uat_training"
        )
    ]

    cols = st.columns(5)

    for i, (label, sql) in enumerate(metrics):

        cols[i % 5].metric(
            label,
            count(sql)
        )

    st.subheader(
        "🚨 Incident Severity"
    )

    d = pd.read_sql_query(
        """
        SELECT
            severity AS Severity,
            COUNT(*) AS Count
        FROM incidents
        GROUP BY severity
        ORDER BY CASE severity
            WHEN 'P1 - Critical' THEN 1
            WHEN 'P2 - High' THEN 2
            WHEN 'P3 - Medium' THEN 3
            ELSE 4
        END
        """,
        conn
    )

    if not d.empty:

        st.bar_chart(
            d.set_index("Severity")
        )

    else:

        st.info(
            "No incident severity data available."
        )

    st.subheader(
        "📊 Incident Status"
    )

    d = pd.read_sql_query(
        """
        SELECT
            status AS Status,
            COUNT(*) AS Count
        FROM incidents
        GROUP BY status
        """,
        conn
    )

    if not d.empty:

        st.bar_chart(
            d.set_index("Status")
        )

    else:

        st.info(
            "No incident status data available."
        )

    st.subheader(
        "⏱️ SLA Performance"
    )

    s = pd.read_sql_query(
        """
        SELECT
            sla_status AS Status,
            COUNT(*) AS Count
        FROM incident_sla
        GROUP BY sla_status
        """,
        conn
    )

    if not s.empty:

        st.bar_chart(
            s.set_index("Status")
        )

    else:

        st.info(
            "No SLA data available."
        )

    st.subheader(
        "🚀 Release Performance"
    )

    d = pd.read_sql_query(
        """
        SELECT
            status AS Status,
            COUNT(*) AS Count
        FROM releases
        GROUP BY status
        """,
        conn
    )

    if not d.empty:

        st.bar_chart(
            d.set_index("Status")
        )

    else:

        st.info(
            "No release data available."
        )

    st.subheader(
        "💳 Payment Health"
    )

    d = pd.read_sql_query(
        """
        SELECT
            payment_status AS Status,
            COUNT(*) AS Count
        FROM shipments
        GROUP BY payment_status
        """,
        conn
    )

    if not d.empty:

        st.bar_chart(
            d.set_index("Status")
        )

    else:

        st.info(
            "No payment data available."
        )

    s = pd.read_sql_query(
        """
        SELECT
            COUNT(*) total,
            SUM(
                CASE
                    WHEN sla_status='Within SLA'
                    THEN 1
                    ELSE 0
                END
            ) within_sla,
            SUM(
                CASE
                    WHEN sla_status='SLA Breached'
                    THEN 1
                    ELSE 0
                END
            ) breached,
            SUM(
                CASE
                    WHEN escalation_required='Yes'
                    THEN 1
                    ELSE 0
                END
            ) escalations
        FROM incident_sla
        """,
        conn
    ).iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "SLA Records",
        int(s.total or 0)
    )

    c2.metric(
        "Within SLA",
        int(s.within_sla or 0)
    )

    c3.metric(
        "Breaches",
        int(s.breached or 0)
    )

    c4.metric(
        "Escalations",
        int(s.escalations or 0)
    )


# =========================================================
# ROUTER
# =========================================================

if menu == "🏠 Operations Dashboard":

    dashboard()

elif menu == "🚨 Incident Management":

    incidents()

elif menu == "🔔 Alert Monitoring":

    alerts()

elif menu == "🗄️ SQL & DB Troubleshooting":

    sql_tool()

elif menu == "🔍 RCA & Investigation":

    rca()

elif menu == "🎫 Support Requests":

    requests()

elif menu == "🤝 Communication & Coordination":

    communication()

elif menu == "🚀 Release & Announcements":

    releases()

elif menu == "📝 Daily Log & Handover":

    daily()

elif menu == "📚 SOP / UAT / Training":

    knowledge()

elif menu == "🔄 Incident 360 View":

    incident360()

elif menu == "📜 Audit Trail":

    audit_page()

elif menu == "📈 Reports":

    reports()


st.divider()

st.caption(
    "MOL CargoFlow • Production-like Application Support workflow • "
    "Incident → Alert → Primary Analysis → RCA → Release/Patch → "
    "Communication → Handover → Audit"
)