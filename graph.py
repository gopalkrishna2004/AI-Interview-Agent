
# graph.py
from langgraph.graph import StateGraph
from typing import TypedDict, Dict, List, Optional

from tools.analyzer import analyze_resume_jd_tool
from tools.context_splitter import context_split_tool
from tools.question_generator import generate_questions_tool
from tools.interview_conversational_agent import build_interview_conversational_graph


class InterviewState(TypedDict):
    resume_pdf: str  # PDF file path
    jd_pdf: str  # PDF file path
    resume: str  # Text content (converted from PDF)
    job_description: str  # Text content (converted from PDF)
    resume_jd_analysis: Dict
    context_split: dict
    questions: dict
    current_question: Optional[str]
    user_response: Optional[str]
    chat_history: List[Dict[str, str]]
    evaluation: List[Dict[str, str]]
    question_index: int
    question_type_order: List[str]
    conversation_context: Dict[str, str]
    follow_up_needed: bool
    current_topic_depth: int
    current_question_type: str
    interview_phase: str
    question_indices: Dict[str, int]


# ✅ Phase 1: Resume/Job/Question Graph
def build_initial_analysis_graph():
    graph = StateGraph(InterviewState)
    
    graph.add_node("Start", lambda state: {"next": "Analyze"})
    graph.add_node("Analyze", analyze_resume_jd_tool)
    graph.add_node("ContextSplit", context_split_tool)
    graph.add_node("GenerateQuestions", generate_questions_tool)

    graph.add_edge("Start", "Analyze")
    graph.add_edge("Analyze", "ContextSplit")
    graph.add_edge("ContextSplit", "GenerateQuestions")

    graph.set_entry_point("Start")
    graph.set_finish_point("GenerateQuestions")

    return graph.compile()


# ✅ Orchestrate full pipeline: Phase 1 ➝ Phase 2
def run_full_interview_pipeline(resume: str, job_description: str):
    # Initialize base state
    state: InterviewState = {
        "resume": resume,
        "job_description": job_description,
        "resume_jd_analysis": {},
        "context_split": {},
        "questions": {},
        "current_question": None,
        "user_response": None,
        "chat_history": [],
        "evaluation": [],
        "question_index": 0,
        "question_type_order": ["technical", "behavioral", "situational"],
    }

    # Run phase 1: Resume → JD Analysis → Context → Questions
    initial_graph = build_initial_analysis_graph()
    state = initial_graph.invoke(state)

    if "error" in state:
        print("🚨 Error during initial analysis:", state["error"])
        return state
    # return state

    # Run phase 2: Conversational Interview
    print("\n🧠 Starting Interview...\n")
    conversation_graph = build_interview_conversational_graph()
    final_state = conversation_graph.invoke(state)

    # Final summary
    print("\n📝 Interview Evaluation Summary:\n")
    from pprint import pprint
    pprint(final_state["evaluation"])
    return final_state
