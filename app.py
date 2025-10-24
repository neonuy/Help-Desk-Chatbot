import json
import os
import logging
from rapidfuzz import process
import streamlit as st

# ==============================
# 🔧 CONFIGURATION
# ==============================
st.set_page_config(page_title="💡 AI Help Desk", page_icon="💬", layout="wide")
st.title("💬 AI Help Desk Assistant")

# Logging setup
logging.basicConfig(filename="helpdesk.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# ==============================
# 📚 LOAD KNOWLEDGE BASE
# ==============================
kb_path = os.path.join(os.path.dirname(__file__), "knowledge.json")

@st.cache_data
def load_kb(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Only include entries that actually have an "answer" field
    flat = {}
    for key, value in data.items():
        if isinstance(value, dict) and "answer" in value:
            flat[key] = value  # keep the answer dict as-is
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
# 🤖 ANSWER RETRIEVAL
# ==============================
def get_answer(query, max_suggestions=3, min_confidence=20):
    """Return best-matching answer or suggestions."""
    query = query.lower()
    # Only extract actual KB keys (ignore metadata if any)
    questions = list(kb.keys())
    suggestions = process.extract(query, questions, limit=max_suggestions)
    suggestions = [(m, s, i) for m, s, i in suggestions if s >= min_confidence]

    if not suggestions:
        logging.info(f"No answer found for query: {query}")
        return "Sorry, I don't know the answer to that question."

    top_match, score, _ = suggestions[0]

    if score > 70:
        answer = kb[top_match]["answer"]
        # Return clean string (handles list or string)
        return clean_answer(answer)

    # Low confidence → store suggestions for buttons
    st.session_state.pending_suggestions = suggestions
    return "I’m not sure what you mean. Did you mean one of these?"

def clean_answer(ans):
    if isinstance(ans, dict) and "answer" in ans:
        ans = ans["answer"]
    if isinstance(ans, list):
        ans = " ".join(str(x) for x in ans)
    return str(ans)
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

    # Show suggestions as buttons if uncertain
    if st.session_state.pending_suggestions:
        for topic, score, _ in st.session_state.pending_suggestions:
            clean_topic = topic.split(":")[-1].replace("_", " ").capitalize()
            if st.button(f"✅ {clean_topic} ({score:.0f}%)", key=f"suggestion_{topic}"):
                ans_text = clean_answer(kb[topic]["answer"])
                st.session_state.chat_history.append(("assistant", ans_text))
                st.session_state.pending_suggestions = []
                st.experimental_rerun()

        if st.button("❌ None of these"):
            st.session_state.chat_history.append(("assistant", "Sorry, I don’t know the answer to that question."))
            st.session_state.pending_suggestions = []
            st.experimental_rerun()

# ==============================
# 🧰 SIDEBAR UTILITIES
# ==============================
with st.sidebar:
    st.header("📚 Quick Help Topics")
    for i, key in enumerate(list(kb.keys())[:8]):
        if st.button(f"{key}", key=f"sidebar_{i}"):
            ans = kb[key]["answer"]
            st.session_state.chat_history.append(("assistant", ans))
            st.rerun()

    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.pending_suggestions = []
        st.rerun()

    st.divider()
    st.subheader("🆘 Escalate to IT")
    with st.form("ticket_form"):
        name = st.text_input("Your Name")
        issue = st.text_area("Describe your issue")
        submit_ticket = st.form_submit_button("Submit Ticket")
        if submit_ticket:
            if name and issue:
                with open("tickets.txt", "a", encoding="utf-8") as f:
                    f.write(f"{name}: {issue}\n")
                st.success("✅ Your issue has been submitted!")
            else:
                st.warning("Please fill in both fields before submitting.")
