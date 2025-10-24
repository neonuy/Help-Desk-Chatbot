from fastapi import FastAPI
from pydantic import BaseModel
import json
from fuzzywuzzy import process

# Load knowledge base from JSON
with open("knowledge.json", "r") as f:
    knowledge_base = json.load(f)

# Fuzzy search function
def get_fuzzy_answer(query):
    query = query.lower()
    keys = knowledge_base.keys()
    best_match = process.extractOne(query, keys)
    if best_match and best_match[1] > 60:  # threshold 60%
        return knowledge_base[best_match[0]]
    return "Sorry, I don't know the answer to that yet."

# FastAPI setup
app = FastAPI(title="AI Help Desk Knowledge Base")

class Question(BaseModel):
    query: str

@app.post("/ask")
def ask_question(q: Question):
    answer = get_fuzzy_answer(q.query)
    return {"answer": answer}

@app.get("/")
def home():
    return {"message": "Welcome to the AI Help Desk Knowledge Base API!"}
