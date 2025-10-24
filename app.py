import json
import os
import logging
import datetime
import csv
from rapidfuzz import process, fuzz
import streamlit as st

# ==============================
# 🔧 CONFIGURATION
# ==============================
st.set_page_config(page_title="💡 AI Help Desk", page_icon="💬", layout="wide")
st.title("💬 AI Help Desk Assistant")

# Logging setup
logging.basicConfig(filename="helpdesk.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# ==============================
# 🧠 HELPER FUNCTIONS
# ==============================
def clean_answer(ans):
    """Return a clean text answer (handles lists and dicts)."""
    if isinstance(ans, dict) and "answer" in ans:
        ans = ans["answer"]
    if isinstance(ans, list):
        ans = " ".join(str(x) for x in ans)
    return str(ans)

def get_answer(query, max_suggestions=3, min_confidence=20):
    """Return best-matching answer or suggestions."""
    query = query.lower()
    questions = list(kb.keys())
    
    suggestions = process.extract(query, questions, scorer=fuzz.ratio, limit=max_suggestions)
    suggestions = [(m, s, i) for m, s, i in suggestions if s >= min_confidence]

    if not suggestions:
        logging.info(f"No answer found for query: {query}")
        return "❌ Sorry, I don't know the answer to that question."

    top_match, score, _ = suggestions[0]

    if score > 70:
        return clean_answer(kb[top_match]["answer"])

    st.session_state.pending_suggestions = suggestions
    return "🤔 I’m not sure what you mean. Did you mean one of these?"

# ==============================
# 📚 LOAD KNOWLEDGE BASE
# ==============================
kb_path = os.path.join(os.path.dirname(__file__), "knowledge.json")

@st.cache_data
def load_kb(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    flat = {k: v for k, v in data.items() if isinstance(v, dict) and "answer" in v}
    return flat

kb = load_kb(kb_path)

# ==============================
# 💾 SESSION STATE
# ==============================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_suggestions" not in st.session_state:
    st.session_state.pending_suggestions = []

# ==============================
# 🗨️ CHAT INTERFACE
# ==============================
for role, text in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(text)

user_input = st.chat_input("Ask me a question...")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    answer = get_answer(user_input)
    st.session_state.chat_history.append(("assistant", answer))

    with st.chat_message("assistant"):
        st.markdown(answer)

# --- Suggestion Buttons ---
if st.session_state.pending_suggestions:
    for topic, score, _ in st.session_state.pending_suggestions:
        clean_topic = topic.split(":")[-1].strip().replace("_", " ").capitalize()
        if st.button(f"✅ {clean_topic} ({score:.0f}%)", key=f"suggestion_{topic}"):
            ans_text = clean_answer(kb[topic]["answer"])
            st.session_state.chat_history.append(("assistant", ans_text))
            st.session_state.pending_suggestions = []
            break

    if st.button("❌ None of these", key="none_of_these"):
        st.session_state.chat_history.append(("assistant", "Sorry, I don’t know the answer to that question."))
        st.session_state.pending_suggestions = []

# ==============================
# 🧰 SIDEBAR UTILITIES
# ==============================
with st.sidebar:
    st.header("📚 Quick Help Topics")
    for i, key in enumerate(list(kb.keys())[:8]):
        clean_key = key.split(":")[-1].strip().replace("_", " ").capitalize()
        if st.button(f"{clean_key}", key=f"sidebar_{i}"):
            ans = kb[key]["answer"]
            st.session_state.chat_history.append(("assistant", clean_answer(ans)))

    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.pending_suggestions = []

    st.divider()
    st.subheader("🆘 Escalate to IT")
    with st.form("ticket_form"):
        name = st.text_input("Your Name")
        issue = st.text_area("Describe your issue")
        submit_ticket = st.form_submit_button("Submit Ticket")
        if submit_ticket:
            if name.strip() and issue.strip():
                ticket_file = os.path.join(os.path.dirname(__file__), "tickets.csv")
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(ticket_file, "a", newline="", encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([timestamp, name.strip(), issue.strip(), "Medium", "Open"])
                st.success("✅ Your issue has been submitted!")
            else:
                st.warning("Please fill in both fields before submitting.")

    st.divider()
    st.subheader("📝 Manage Open Tickets")
    ticket_file = os.path.join(os.path.dirname(__file__), "tickets.csv")
    tickets = []

    # Load tickets if CSV exists
    if os.path.exists(ticket_file):
        with open(ticket_file, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            tickets = list(reader)

    if tickets:
        # Pad rows to ensure 5 columns
        for row in tickets:
            while len(row) < 5:
                if len(row) == 3:
                    row.append("Medium")  # default Priority
                    row.append("Open")    # default Status
                elif len(row) == 4:
                    row.append("Open")

        # Filter only open tickets
        open_tickets = [row for row in tickets if row[4].lower() != "closed"]

        if open_tickets:
            ticket_display = [f"{i+1}. {row[0]} | {row[1]} | {row[4]}" for i, row in enumerate(open_tickets)]

            selected_display = st.selectbox("Select a ticket to manage", ticket_display)
            selected_index = ticket_display.index(selected_display)
            ts, name, issue, priority, status = open_tickets[selected_index]

            st.markdown(f"**Timestamp:** {ts}")
            st.markdown(f"**Name:** {name}")
            st.markdown(f"**Issue:** {issue}")
            st.markdown(f"**Status:** {status}")

            # Change priority
            new_priority = st.selectbox("Set Priority", ["High", "Medium", "Low"], index=["High","Medium","Low"].index(priority))

            # Close ticket
            close_ticket = st.button("✅ Close Ticket")

            # Save changes
            if close_ticket or new_priority != priority:
                # Find the original index in full tickets list
                for i, row in enumerate(tickets):
                    if row[0] == ts and row[1] == name and row[2] == issue:
                        tickets[i][3] = new_priority
                        if close_ticket:
                            tickets[i][4] = "Closed"
                        break

                # Write all tickets back to CSV
                with open(ticket_file, "w", newline="", encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(tickets)
                st.success("Ticket updated!")

        else:
            st.info("No open tickets.")
    else:
        st.info("No tickets submitted yet.")
