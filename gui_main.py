import tkinter as tk
from tkinter import scrolledtext
import json
from fuzzywuzzy import process
import os
import sys

# Load knowledge base safely
try:
    kb_path = os.path.join(os.path.dirname(__file__), "knowledge.json")
    with open(kb_path, "r") as f:
        kb = json.load(f)
except Exception as e:
    print(f"Error loading knowledge.json: {e}")
    input("Press Enter to exit...")
    sys.exit()

from fuzzywuzzy import process

pending_suggestions = []  # Store suggestions awaiting user selection

def display_answer(answer):
    """Insert the answer into the output box."""
    output.insert(tk.END, f"Bot: {answer}\n\n")
    output.see(tk.END)

def get_answer(query, max_suggestions=3, min_confidence=20):
    global pending_suggestions, suggestion_frame
    query = query.lower()
    suggestions = process.extract(query, kb.keys(), limit=max_suggestions)
    suggestions = [s for s in suggestions if s[1] >= min_confidence]

    # Clear any old suggestion buttons
    for widget in suggestion_frame.winfo_children():
        widget.destroy()
    pending_suggestions = []

    if not suggestions:
        display_answer("Sorry, I don't know the answer to that question.")
        return

    # High confidence → answer directly
    if suggestions[0][1] > 70:
        answer = kb[suggestions[0][0]]["answer"]
        display_answer("\n".join(answer) if isinstance(answer, list) else answer)
        return

    # Medium confidence → show clickable buttons
    pending_suggestions = suggestions
    display_answer("I'm not sure which one you mean. Please choose:")
    
    for i, (topic, score) in enumerate(suggestions, 1):
        btn = tk.Button(suggestion_frame, text=f"{topic} (confidence: {score})",
                        command=lambda t=topic: choose_topic(t))
        btn.pack(fill='x', pady=2)

    # Add a "None of these" button
    btn_none = tk.Button(suggestion_frame, text="None of these", command=choose_none)
    btn_none.pack(fill='x', pady=2)

def choose_topic(topic):
    """Handle user clicking a suggestion."""
    global pending_suggestions, suggestion_frame
    answer = kb[topic]["answer"]
    display_answer("\n".join(answer) if isinstance(answer, list) else answer)
    pending_suggestions = []
    # Remove suggestion buttons
    for widget in suggestion_frame.winfo_children():
        widget.destroy()

def choose_none():
    global pending_suggestions, suggestion_frame
    display_answer("Sorry, I don't know the answer to that question.")
    pending_suggestions = []
    for widget in suggestion_frame.winfo_children():
        widget.destroy()

def handle_user_input():
    query = entry.get().strip()
    if not query:
        return
    output.insert(tk.END, f"You: {query}\n")
    entry.delete(0, tk.END)
    get_answer(query)

# --- GUI setup ---
root = tk.Tk()
root.title("AI Help Desk")
root.geometry("800x800")

entry = tk.Entry(root, width=50)
entry.pack(padx=10, pady=10)
entry.focus()

btn = tk.Button(root, text="Ask", command=handle_user_input)
btn.pack(pady=5)

output = scrolledtext.ScrolledText(root, width=70, height=20)
output.pack(padx=10, pady=10)

# Frame to hold clickable suggestion buttons
suggestion_frame = tk.Frame(root)
suggestion_frame.pack(padx=10, pady=5, fill='x')

entry.bind("<Return>", lambda event: handle_user_input())

root.mainloop()