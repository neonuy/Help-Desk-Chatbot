import json
import os
from fuzzywuzzy import process
import streamlit as st

# Load knowledge base
kb_path = os.path.join(os.path.dirname(__file__), "knowledge.json")
with open(kb_path, "r") as f:
    kb = json.load(f)

st.set_page_config(page_title="AI Help Desk", page_icon="💡", layout="wide")
st.title("💡 AI Help Desk")

# Session state to remember suggestions
if "pending_suggestions" not in st.session_state:
    st.session_state.pending_suggestions = []

# Function to find answer or ask clarification
def get_answer(query, max_suggestions=3, min_confidence=20):
    query = query.lower()
    suggestions = process.extract(query, kb.keys(), limit=max_suggestions)
    suggestions = [s for s in suggestions if s[1] >= min_confidence]

    if not suggestions:
        return "Sorry, I don't know the answer to that question."

    # High confidence
    if suggestions[0][1] > 70:
        answer = kb[suggestions[0][0]]["answer"]
        return "\n".join(answer) if isinstance(answer, list) else answer

    # Medium confidence → ask for clarification
    st.session_state.pending_suggestions = suggestions
    msg = "I'm not sure which one you mean. Please choose one below 👇"
    return msg

# --- UI ---
query = st.text_input("Ask me a question:")

if query:
    answer = get_answer(query)
    st.write(f"**You:** {query}")
    st.write(f"**Bot:** {answer}")

# Show clickable suggestions
if st.session_state.pending_suggestions:
    for topic, score in st.session_state.pending_suggestions:
        if st.button(f"{topic} (confidence: {score})"):
            ans = kb[topic]["answer"]
            st.session_state.pending_suggestions = []
            st.write(f"**Bot:** {' '.join(ans) if isinstance(ans, list) else ans}")
            st.stop()

    if st.button("None of these ❌"):
        st.session_state.pending_suggestions = []
        st.write("**Bot:** Sorry, I don't know the answer to that question.")