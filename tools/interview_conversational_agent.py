import json
from typing import TypedDict, List, Dict, Optional
from langgraph.graph import StateGraph
from llm import GeminiLLM
import re
# Enhanced State Schema
class InterviewConversationState(TypedDict):
    resume: str
    job_description: str
    questions: Dict[str, List[Dict[str, str]]]
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
    question_indices: Dict[str, int]  # 🔹 NEW: Track index per question type

# -------------------------------
# 🔹 Fixed LLM Integration
# -------------------------------
def call_llm(prompt: str) -> str:
    """Fixed LLM wrapper that handles response correctly"""
    try:
        response = GeminiLLM().invoke(prompt)
        return response
    except Exception as e:
        return f"Error calling LLM: {str(e)}"

# -------------------------------
# 🔹 Human-like Introduction
# -------------------------------
def introduce_interview(state: InterviewConversationState) -> InterviewConversationState:
    """Start with a warm, human-like introduction"""
    print("👋 Hello! Welcome to your interview today.")
    print("🤖 Interviewer: I'm excited to learn more about you and your background.")
    print("Let's start with a quick introduction. Could you tell me a bit about yourself?")
    
    user_input = input("👤 You: ")
    
    # Generate a personalized response based on their intro
    response_prompt = f"""
    You are a friendly interviewer. The candidate just introduced themselves with: "{user_input}"
    
    Respond warmly and naturally, then smoothly transition to mention that you'll be covering technical, behavioral, and situational questions. Keep it conversational and encouraging.
    
    Make it 1-2 sentences max.
    """
    
    interviewer_response = call_llm(response_prompt)
    print(f"🤖 Interviewer: {interviewer_response}")
    print("\nLet's dive into some technical questions first. 🚀")
    
    state["chat_history"].append({
        "question": "Tell me about yourself",
        "answer": user_input
    })
    state["interview_phase"] = "technical"
    state["current_question_type"] = "technical"
    
    # 🔹 Initialize question indices
    if "question_indices" not in state:
        state["question_indices"] = {
            "technical": 0,
            "behavioral": 0,
            "situational": 0
        }
    
    return state

# -------------------------------
# 🔹 FIXED Question Selection Logic
# -------------------------------
def get_next_question(state: InterviewConversationState) -> Optional[str]:
    """Fixed question selection with proper progression"""
    
    # Check if we need a follow-up question
    if state.get("follow_up_needed", False):
        return generate_follow_up_question(state)
    
    # Get current question type
    current_type = state.get("current_question_type", "technical")
    type_questions = state["questions"].get(current_type, [])
    
    # 🔹 FIX: Use proper index tracking per type
    type_index = state.get("question_indices", {}).get(current_type, 0)
    
    # Check if we have more questions in current type
    if type_index < len(type_questions):
        return type_questions[type_index]["question"]
    
    # 🔹 FIX: Move to next question type if current is exhausted
    order = state["question_type_order"]
    try:
        current_idx = order.index(current_type)
        if current_idx + 1 < len(order):
            next_type = order[current_idx + 1]
            state["current_question_type"] = next_type
            state["interview_phase"] = next_type
            
            # Add transition message
            transitions = {
                "behavioral": "\n🎯 Great! Now let's talk about some behavioral scenarios.",
                "situational": "\n🧠 Perfect! Finally, let's explore some situational questions."
            }
            if next_type in transitions:
                print(transitions[next_type])
            
            # Get first question of next type
            next_questions = state["questions"].get(next_type, [])
            if next_questions:
                return next_questions[0]["question"]
    except (ValueError, IndexError):
        pass
    
    return None

def generate_follow_up_question(state: InterviewConversationState) -> str:
    """Generate intelligent follow-up based on previous response"""
    last_qa = state["chat_history"][-1] if state["chat_history"] else {}
    
    prompt = f"""
    You are a conversational interviewer. Based on the candidate's response, ask a follow-up question.
    
    Previous Question: {last_qa.get('question', 'N/A')}
    Candidate's Answer: {last_qa.get('answer', 'N/A')}
    
    Generate a conversational follow-up that:
    1. Asks for more specific details or examples
    2. Probes deeper into their experience
    
    Keep it conversational. Return ONLY the question.
    """
    
    return call_llm(prompt)

# -------------------------------
# 🔹 Enhanced Response Analysis
# -------------------------------
def analyze_response_depth(state: InterviewConversationState) -> Dict:
    """Analyze if response needs follow-up probing"""
    question = state["current_question"]
    answer = state["user_response"]
    
    prompt = f"""
    Analyze this interview response for depth and completeness:
    
    Don't ask follow-up questions unnecessarly or if the user dont know the answer.
    
    Question: {question}
    Answer: {answer}
    
    Respond with JSON:
    {{
        "needs_followup": true/false,
        "reason": "why follow-up is needed",
        "depth_score": 1-5
    }}
    """
    
    try:
        raw = call_llm(prompt)
        cleaned_response = re.sub(r"^```json|```$", "", raw.strip(), flags=re.MULTILINE).strip("` \n")
        return json.loads(cleaned_response)
    except:
        return {
            "needs_followup": False,
            "reason": "Could not analyze response",
            "depth_score": 3
        }

# -------------------------------
# 🔹 Enhanced Steps
# -------------------------------
def ask_question(state: InterviewConversationState) -> InterviewConversationState:
    """Ask question with conversational warmth"""
    question = get_next_question(state)
    if question is None:
        print("\n🎉 That wraps up our interview! Thank you for your time.")
        print("🤖 Interviewer: It was great learning about your experience and background.")
        return state
    
    # Add conversational context
    if state.get("follow_up_needed", False):
        state["follow_up_needed"] = False

    print(f"\n🤖 Interviewer: {question}")
    state["current_question"] = question
    return state    

def receive_response(state: InterviewConversationState) -> InterviewConversationState:
    """Get and store candidate response"""
    user_input = input("👤 You: ")
    state["user_response"] = user_input
    state["chat_history"].append({
        "question": state["current_question"],
        "answer": user_input    
    })
    return state
def evaluate_and_decide_followup(state: InterviewConversationState) -> InterviewConversationState:
    """Enhanced evaluation with follow-up decision"""
    question = state["current_question"]
    answer = state["user_response"]
    jd = state["job_description"]
    
    # Get expected answer from questions dict based on current question type
    current_type = state.get("current_question_type", "technical")
    current_index = state["question_indices"][current_type]
    expected_answer = state["questions"][current_type][current_index]["answer"]
    
    # Standard evaluation
    eval_prompt = f"""
    Evaluate this interview response:
    
    Question: {question}
    Answer: {answer}
    Expected Answer: {expected_answer}
    Job Requirements: {jd[:300]}...
    
    JSON Response:
    {{
        "Question": "question", 
        "User_Answer": "answer",
        "Score": 1-5,
        "Reasoning": "explain why you gave this score"
    }}
    """
    
    try:
        eval_raw = call_llm(eval_prompt)
        cleaned_response = re.sub(r"^```json|```$", "", eval_raw.strip(), flags=re.MULTILINE).strip("` \n")
        evaluation = json.loads(cleaned_response)
    except:
        evaluation = {
            "Question": question, 
            "User_Answer": answer,
            "Score": 3,
            "Reasoning": "Could not parse evaluation"
        }
    
    # Analyze for follow-up need (less aggressive)
    depth_analysis = analyze_response_depth(state)
    
    # Decide on follow-up (be more selective)
    should_follow_up = (
        depth_analysis.get("needs_followup", False) and 
        state.get("current_topic_depth", 0) < 1 and  # Max 1 follow-up per question
        depth_analysis.get("depth_score", 3) < 3  # Only if response was shallow
    )
    
    state["evaluation"].append({
        **evaluation,
        "depth_analysis": depth_analysis,
        "follow_up_generated": should_follow_up
    })
    
    if should_follow_up:
        state["follow_up_needed"] = True
        state["current_topic_depth"] = state.get("current_topic_depth", 0) + 1
    else:
        # 🔹 FIX: Properly increment the question index for current type
        current_type = state.get("current_question_type", "technical")
        if "question_indices" not in state: 
            state["question_indices"] = {"technical": 0, "behavioral": 0, "situational": 0}
        
        state["question_indices"][current_type] += 1
        state["current_topic_depth"] = 0
        
        # Debug print to track progress
        print(f"📊 Debug: {current_type} question {state['question_indices'][current_type]} completed")
    
    return state

# -------------------------------
# 🔹 Conversation Flow Conditions
# -------------------------------
def should_continue(state: InterviewConversationState) -> str:
    """Decide conversation flow"""
    # Check if we have follow-up pending
    if state.get("follow_up_needed", False):
        return "continue_followup"
    
    # Check if we have more questions in any category
    for qtype in state["question_type_order"]:
        questions = state["questions"].get(qtype, [])
        completed = state.get("question_indices", {}).get(qtype, 0)
        if completed < len(questions):
            return "continue_structured"
    
    return "end"

# -------------------------------
# 🔹 Enhanced Graph with Introduction
# -------------------------------
def build_interview_conversational_graph():
    graph = StateGraph(InterviewConversationState)
    
    graph.add_node("Introduce", introduce_interview)
    graph.add_node("Ask", ask_question)
    graph.add_node("Respond", receive_response)
    graph.add_node("Evaluate", evaluate_and_decide_followup)
    
    graph.set_entry_point("Introduce")
    
    graph.add_edge("Introduce", "Ask")
    graph.add_edge("Ask", "Respond")
    graph.add_edge("Respond", "Evaluate")
    
    # Enhanced conditional logic
    graph.add_conditional_edges("Evaluate", should_continue, {
        "continue_followup": "Ask",
        "continue_structured": "Ask", 
        "end": "__end__"
    })
    
    return graph.compile()

