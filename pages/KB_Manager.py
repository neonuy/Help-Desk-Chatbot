import streamlit as st
import json
import os
import datetime
import shutil


# --- Ensure user session exists ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Please log in from the main Help Desk app before accessing this page.")
    st.stop()

if "user_name" not in st.session_state:
    st.session_state.user_name = "Guest"  # Fallback if missing

# --- Admin Check ---
ADMIN_USERS = {"neonuy"}

def is_admin():
    user = st.session_state.get("user_name", "")
    return user in ADMIN_USERS

if not is_admin():
    st.error("🔒 You must be an admin to access the Knowledge Base Manager.")
    st.stop()

# --- Page Setup ---
st.set_page_config(page_title="Knowledge Base Manager", page_icon="🧠", layout="wide")
st.title("🧠 Knowledge Base Manager")
st.caption(f"Logged in as: **{st.session_state.user_name}**")

# --- Load Knowledge Base ---
base_dir = os.path.dirname(os.path.abspath(__file__))
kb_path = os.path.join(base_dir, "../knowledge.json")
kb_path = os.path.abspath(kb_path)

if not os.path.exists(kb_path):
    st.error("❌ Knowledge base file not found.")
    st.stop()

with open(kb_path, "r", encoding="utf-8") as f:
    kb = json.load(f)

# --- Backup before editing ---
def backup_kb():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = kb_path.replace(".json", f"_backup_{timestamp}.json")
    shutil.copy(kb_path, backup_path)
    st.info(f"💾 Backup created: `{os.path.basename(backup_path)}`")

# --- Search Bar ---
st.text_input("🔍 Search entries", key="kb_search")
filtered_kb = [k for k in kb.keys() if st.session_state.kb_search.lower() in k.lower()] if st.session_state.kb_search else list(kb.keys())

# --- Selection Dropdown ---
selected_kb = st.selectbox("Select an entry to edit or choose 'Add new entry'", ["➕ Add new entry"] + filtered_kb)

# --- Add New Entry ---
if selected_kb == "➕ Add new entry":
    st.subheader("Add New Knowledge Base Entry")
    new_q = st.text_input("Question")
    new_a = st.text_area("Answer")
    if st.button("Save Entry"):
        if new_q.strip() and new_a.strip():
            backup_kb()
            kb[new_q] = {"answer": new_a}
            with open(kb_path, "w", encoding="utf-8") as f:
                json.dump(kb, f, indent=2)
            st.success("✅ New entry added successfully!")
            st.rerun()
        else:
            st.warning("Please fill out both fields.")
else:
    st.subheader(f"Edit Entry: {selected_kb}")
    edited_q = st.text_input("Edit Question", selected_kb)
    edited_a = st.text_area("Edit Answer", kb[selected_kb]["answer"])

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save Changes"):
            backup_kb()
            kb.pop(selected_kb)
            kb[edited_q] = {"answer": edited_a}
            with open(kb_path, "w", encoding="utf-8") as f:
                json.dump(kb, f, indent=2)
            st.success("✅ Entry updated!")
            st.rerun()
    with col2:
        if st.button("🗑 Delete Entry"):
            backup_kb()
            kb.pop(selected_kb)
            with open(kb_path, "w", encoding="utf-8") as f:
                json.dump(kb, f, indent=2)
            st.warning("🚮 Entry deleted.")
            st.rerun()
    with col3:
        if st.button("🔙 Cancel"):
            st.rerun()