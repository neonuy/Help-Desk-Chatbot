import streamlit as st
import pandas as pd
import os
import plotly.express as px
import datetime

# --- Page Setup ---
st.set_page_config(page_title="Ticket Analytics Dashboard", page_icon="📊", layout="wide")
st.title("📊 Ticket Analytics Dashboard")

# --- Session & Access Check ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Please log in from the main Help Desk app first.")
    st.stop()

if st.session_state.user_name == "Guest":
    st.error("🔒 Guest accounts cannot access analytics.")
    st.stop()

st.caption(f"👤 Logged in as: **{st.session_state.user_name}**")

# --- Load Ticket Data ---
ticket_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tickets.csv")

if not os.path.exists(ticket_file):
    st.info("ℹ️ No tickets have been submitted yet.")
    st.stop()

df = pd.read_csv(ticket_file, names=["Timestamp", "Name", "Issue", "Priority", "Status"])

# --- Data Cleanup ---
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
df["Priority"] = df["Priority"].fillna("Medium")
df["Status"] = df["Status"].fillna("Open")

st.divider()

# --- Key Metrics ---
col1, col2, col3 = st.columns(3)
with col1:
    total_tickets = len(df)
    st.metric("Total Tickets", total_tickets)
with col2:
    open_tickets = len(df[df["Status"].str.lower() == "open"])
    st.metric("Open Tickets", open_tickets)
with col3:
    closed_tickets = len(df[df["Status"].str.lower() == "closed"])
    st.metric("Closed Tickets", closed_tickets)

st.divider()

# --- Charts Section ---
col1, col2 = st.columns(2)

# Pie Chart - Tickets by Status
with col1:
    st.subheader("Tickets by Status")
    fig_status = px.pie(df, names="Status", title="Status Breakdown", hole=0.3, color="Status",
                        color_discrete_map={"Open": "#FFA500", "Closed": "#00CC96"})
    st.plotly_chart(fig_status, use_container_width=True)

# Bar Chart - Tickets by Priority
with col2:
    st.subheader("Tickets by Priority")
    fig_priority = px.bar(df, x="Priority", color="Priority", title="Priority Levels",
                          color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_priority, use_container_width=True)

st.divider()

# --- Trend Over Time ---
st.subheader("📅 Tickets Over Time")

df_daily = df.groupby(df["Timestamp"].dt.date).size().reset_index(name="Tickets")
if not df_daily.empty:
    fig_trend = px.line(df_daily, x="Timestamp", y="Tickets", markers=True, title="Tickets Created Per Day")
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("No date information available to plot trends.")

st.divider()

# --- Table of Open Tickets ---
st.subheader("🧾 Current Open Tickets")
open_df = df[df["Status"].str.lower() == "open"]
if not open_df.empty:
    st.dataframe(open_df, use_container_width=True)
else:
    st.info("All tickets are closed. 🎉")

st_autorefresh(interval=60000, key="data_refresh")