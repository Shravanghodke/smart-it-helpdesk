
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

DB_NAME = "helpdesk.db"

st.set_page_config(
    page_title="Smart IT Helpdesk",
    page_icon="🎫",
    layout="wide"
)

# ---------- DATABASE ----------
def get_connection():
    return sqlite3.connect(DB_NAME)

def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id INTEGER PRIMARY KEY,
                employee_name TEXT NOT NULL,
                issue TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open'
            )
        """)

def load_tickets():
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM tickets ORDER BY ticket_id DESC",
            conn
        )

initialize_database()

# ---------- PAGE HEADER ----------
st.title("🎫 Smart IT Helpdesk")
st.caption("IT support ticket management and analytics")

# ---------- SIDEBAR: CREATE TICKET ----------
st.sidebar.header("Create a ticket")

with st.sidebar.form("create_ticket_form"):
    ticket_id = st.number_input(
        "Ticket ID", min_value=1, step=1
    )
    employee_name = st.text_input("Employee name")
    issue = st.text_area("Describe the issue")
    priority = st.selectbox(
        "Priority", ["Low", "Medium", "High"]
    )
    submitted = st.form_submit_button(
        "Create ticket", use_container_width=True
    )

    if submitted:
        if not employee_name.strip() or not issue.strip():
            st.sidebar.error(
                "Employee name and issue are required."
            )
        else:
            try:
                with get_connection() as conn:
                    conn.execute("""
                        INSERT INTO tickets
                        (ticket_id, employee_name, issue, priority)
                        VALUES (?, ?, ?, ?)
                    """, (
                        int(ticket_id),
                        employee_name.strip(),
                        issue.strip(),
                        priority
                    ))
                st.sidebar.success("Ticket created!")
                st.rerun()

            except sqlite3.IntegrityError:
                st.sidebar.error(
                    "That ticket ID already exists."
                )

# ---------- LOAD DATA ----------
df = load_tickets()

# ---------- METRICS ----------
total = len(df)
open_count = int((df["status"] == "Open").sum())
progress_count = int(
    (df["status"] == "In Progress").sum()
)
resolved_count = int(
    (df["status"] == "Resolved").sum()
)
high_count = int((df["priority"] == "High").sum())

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Tickets", total)
c2.metric("Open", open_count)
c3.metric("In Progress", progress_count)
c4.metric("Resolved", resolved_count)
c5.metric("High Priority", high_count)

st.divider()

# ---------- ANALYTICS ----------
left, right = st.columns(2)

with left:
    st.subheader("Tickets by status")
    if not df.empty:
        status_data = (
            df["status"].value_counts()
            .rename_axis("Status")
            .reset_index(name="Count")
        )
        fig = px.pie(
            status_data,
            names="Status",
            values="Count",
            hole=0.45
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Create a ticket to see analytics.")

with right:
    st.subheader("Tickets by priority")
    if not df.empty:
        priority_data = (
            df["priority"].value_counts()
            .rename_axis("Priority")
            .reset_index(name="Count")
        )
        fig = px.bar(
            priority_data,
            x="Priority",
            y="Count",
            color="Priority",
            text="Count"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No ticket data available yet.")

st.divider()

# ---------- SEARCH AND FILTERS ----------
st.subheader("Manage tickets")

f1, f2, f3 = st.columns(3)

search_text = f1.text_input(
    "Search by ID, employee or issue"
)
status_filter = f2.selectbox(
    "Filter by status",
    ["All", "Open", "In Progress", "Resolved"]
)
priority_filter = f3.selectbox(
    "Filter by priority",
    ["All", "Low", "Medium", "High"]
)

filtered = df.copy()

if search_text.strip():
    query = search_text.strip()
    filtered = filtered[
        filtered.astype(str).apply(
            lambda col: col.str.contains(
                query, case=False, regex=False
            )
        ).any(axis=1)
    ]

if status_filter != "All":
    filtered = filtered[
        filtered["status"] == status_filter
    ]

if priority_filter != "All":
    filtered = filtered[
        filtered["priority"] == priority_filter
    ]

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True
)

# ---------- UPDATE STATUS ----------
st.subheader("Update ticket status")

if not df.empty:
    selected_id = st.selectbox(
        "Select ticket ID",
        df["ticket_id"].tolist()
    )

    current_status = df.loc[
        df["ticket_id"] == selected_id, "status"
    ].iloc[0]

    new_status = st.selectbox(
        "New status",
        ["Open", "In Progress", "Resolved"],
        index=["Open", "In Progress", "Resolved"].index(
            current_status
        )
    )

    if st.button("Save status"):
        with get_connection() as conn:
            conn.execute("""
                UPDATE tickets
                SET status = ?
                WHERE ticket_id = ?
            """, (new_status, int(selected_id)))

        st.success("Ticket status updated.")
        st.rerun()
else:
    st.info("There are no tickets to update.")

# ---------- CSV EXPORT ----------
st.subheader("Export data")

st.download_button(
    "Download tickets as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="helpdesk_tickets.csv",
    mime="text/csv",
    disabled=filtered.empty
)
