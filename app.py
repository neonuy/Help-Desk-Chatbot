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
    # Keep only entries with an "answer" key
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
            break  # stop processing after click

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
                    writer.writerow([timestamp, name.strip(), issue.strip()])
                st.success("✅ Your issue has been submitted!")
            else:
                st.warning("Please fill in both fields before submitting.")

    st.divider()
    st.subheader("📝 Submitted Tickets")
    ticket_file = os.path.join(os.path.dirname(__file__), "tickets.csv")
    if os.path.exists(ticket_file):
        with open(ticket_file, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            tickets = list(reader)
        if tickets:
            for ts, user, msg in reversed(tickets[-10:]):  # show last 10 tickets
                st.markdown(f"**{ts} | {user}**: {msg}")
        else:
            st.info("No tickets submitted yet.")
    else:
        st.info("No tickets submitted yet.")