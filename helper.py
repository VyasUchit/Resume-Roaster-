"""
Resume Roaster - LangGraph pipeline
Takes raw resume text and returns a score, strengths, and blunt fixes.
"""

import os
import json
from typing import TypedDict, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

load_dotenv()  

class ResumeState(TypedDict):
    resume_text: str
    score: int
    strengths: List[str]
    fixes: List[str]
    error: str


def get_llm():
    """Creates the OpenAI chat model. Reads the API key from env var OPENAI_API_KEY."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Make sure .env exists with OPENAI_API_KEY=your_key"
        )
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=api_key)


def validate_input_node(state: ResumeState) -> ResumeState:
    """Node 1: basic cleanup and validation of the pasted resume text."""
    text = state.get("resume_text", "").strip()
    if len(text) < 30:
        state["error"] = "Resume text is too short. Paste at least a few lines."
    state["resume_text"] = text
    return state


def roast_and_score_node(state: ResumeState) -> ResumeState:
    """Node 2: sends the resume to the LLM and asks for a JSON verdict."""
    if state.get("error"):
        return state  

    llm = get_llm()

    prompt = f"""You are a blunt, no-nonsense resume reviewer for college students.
Review the resume text below and respond with ONLY valid JSON, no other text,
in exactly this format:

{{
  "score": <integer 1-10>,
  "strengths": ["<strength 1>", "<strength 2>"],
  "fixes": ["<blunt fix 1>", "<blunt fix 2>", "<blunt fix 3>"]
}}

Be honest and direct, but the fixes should be actionable, not just criticism.

RESUME TEXT:
{state['resume_text']}
"""

    response = llm.invoke(prompt)
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json", "", 1).strip()

    try:
        parsed = json.loads(raw)
        state["score"] = parsed.get("score", 0)
        state["strengths"] = parsed.get("strengths", [])
        state["fixes"] = parsed.get("fixes", [])
    except json.JSONDecodeError:
        state["error"] = "Could not parse the AI's response. Try again."

    return state


def build_graph():
    """Builds and compiles the 2-node LangGraph pipeline."""
    graph = StateGraph(ResumeState)

    graph.add_node("validate_input", validate_input_node)
    graph.add_node("roast_and_score", roast_and_score_node)

    graph.set_entry_point("validate_input")
    graph.add_edge("validate_input", "roast_and_score")
    graph.add_edge("roast_and_score", END)

    return graph.compile()


def run_resume_review(resume_text: str) -> dict:
    """
    Main entry point called by the Streamlit app.
    Returns a dict with: score, strengths, fixes, error
    """
    app = build_graph()
    initial_state: ResumeState = {
        "resume_text": resume_text,
        "score": 0,
        "strengths": [],
        "fixes": [],
        "error": "",
    }
    final_state = app.invoke(initial_state)
    return final_state
