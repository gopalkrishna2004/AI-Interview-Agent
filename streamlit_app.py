import streamlit as st
import os
import json
import tempfile
from typing import Dict, List, Optional
import traceback

# Import your existing modules
from graph import build_initial_analysis_graph
from tools.interview_conversational_agent import (
    call_llm, 
    get_next_question, 
    analyze_response_depth,
    InterviewConversationState
)
from llm import GeminiLLM

# Page config
st.set_page_config(
    page_title="AI Interview Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force light theme using custom CSS
st.markdown("""
<style>
    /* Force light theme */
    .stApp {
        background-color: white;
        color: black;
    }
    
    /* Ensure all containers use light theme */
    .main .block-container {
        background-color: white;
        color: black;
    }
    
    /* Sidebar light theme */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Input fields light theme */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background-color: white;
        color: black;
        border: 1px solid #ddd;
    }
    
    /* Button light theme */
    .stButton > button {
        background-color: #007bff;
        color: white;
        border: none;
    }
    
    .stButton > button:hover {
        background-color: #0056b3;
    }
    
    /* Metrics light theme */
    .metric-container {
        background-color: white;
        border: 1px solid #e0e0e0;
    }
    
    /* Progress bar light theme */
    .stProgress .st-bo {
        background-color: #e9ecef;
    }
    
    /* Expander light theme */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        color: black;
    }
    
    /* File uploader light theme */
    .stFileUploader {
        background-color: white;
    }
    
    /* Form light theme */
    .stForm {
        background-color: white;
        border: 1px solid #e0e0e0;
    }
    
    /* Alert boxes light theme */
    .stAlert {
        background-color: white;
        color: black;
    }
    
    /* Info boxes */
    .stInfo {
        background-color: #d1ecf1;
        color: #0c5460;
    }
    
    /* Success boxes */
    .stSuccess {
        background-color: #d4edda;
        color: #155724;
    }
    
    /* Warning boxes */
    .stWarning {
        background-color: #fff3cd;
        color: #856404;
    }
    
    /* Error boxes */
    .stError {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .interviewer-message {
        background-color: #f0f2f6;
        border-left: 4px solid #1f77b4;
    }
    .candidate-message {
        background-color: #e8f4fd;
        border-left: 4px solid #28a745;
    }
    .analysis-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'stage': 'upload',  # upload, analysis, interview, results
        'interview_state': None,
        'analysis_complete': False,
        'interview_started': False,
        'interview_ended': False,
        'interview_phase': 'intro',  # intro, technical, behavioral, situational
        'expecting_followup_response': False,  # Flag for follow-up questions
        'chat_history': [],
        'current_question': None,
        'question_count': 0,
        'evaluation_results': [],
        'analysis_results': {},
        'resume_text': '',
        'jd_text': '',
        'total_questions': 0,
        'current_question_type': 'technical',
        'question_indices': {'technical': 0, 'behavioral': 0, 'situational': 0}
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def save_uploaded_file(uploaded_file) -> str:
    """Save uploaded file and return path"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        return None

def run_analysis(resume_path: str, jd_path: str) -> Dict:
    """Run the initial analysis workflow"""
    try:
        initial_graph = build_initial_analysis_graph()
        
        initial_state = {
            "resume_pdf": resume_path,
            "jd_pdf": jd_path,
            "resume": "",
            "job_description": "",
            "resume_jd_analysis": {},
            "context_split": {},
            "questions": {},
            "current_question": None,
            "user_response": None,
            "chat_history": [],
            "evaluation": [],
            "question_index": 0,
            "question_type_order": ["technical", "behavioral", "situational"],
            "conversation_context": {},
            "follow_up_needed": False,
            "current_topic_depth": 0,
            "current_question_type": "technical",
            "interview_phase": "intro",
            "question_indices": {
                "technical": 0,
                "behavioral": 0,
                "situational": 0
            }
        }
        
        result = initial_graph.invoke(initial_state)
        return result
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return {"error": str(e)}

def display_analysis_results(analysis: Dict):
    """Display analysis results in a structured format"""
    st.markdown("### 📊 Resume-Job Description Analysis")
    
    if "error" in analysis.get("resume_jd_analysis", {}):
        st.error("Analysis failed: " + analysis["resume_jd_analysis"]["error"])
        return False, 0.0
    
    # Display resume and JD content
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📄 Resume Content")
        if analysis.get("resume"):
            st.text_area("Resume", analysis["resume"][:1000] + "...", height=200, disabled=True)
        
    with col2:
        st.markdown("#### 💼 Job Description")
        if analysis.get("job_description"):
            st.text_area("Job Description", analysis["job_description"][:1000] + "...", height=200, disabled=True)
    
    # Extract final score for qualification check
    final_score = 0.0
    analysis_data = analysis.get("resume_jd_analysis", {})
    
    if "overall_assessment" in analysis_data:
        overall_assessment = analysis_data["overall_assessment"]
        if "final_score" in overall_assessment:
            score_str = overall_assessment["final_score"]
            try:
                # Extract numeric value from "4.7/5" format
                final_score = float(score_str.split("/")[0])
            except (ValueError, IndexError):
                final_score = 0.0
    
    # Display overall assessment
    if "overall_assessment" in analysis_data:
        overall_assessment = analysis_data["overall_assessment"]
        st.markdown("#### 🎯 Overall Assessment")
        
        # Create metrics for overall assessment
        col1, col2, col3 = st.columns(3)
        with col1:
            fit_level = overall_assessment.get("fit", "Unknown")
            st.metric("Fit Level", fit_level)
        with col2:
            score_display = overall_assessment.get("final_score", "N/A")
            st.metric("Final Score", score_display)
        with col3:
            # Color code based on score
            if final_score >= 4.0:
                st.success("🌟 Excellent Candidate")
            elif final_score >= 3.0:
                st.info("👍 Good Candidate")
            elif final_score >= 2.0:
                st.warning("⚠️ Meets Minimum")
            else:
                st.error("❌ Below Threshold")
        
        # Show qualification threshold
        st.markdown("---")
        threshold_col1, threshold_col2 = st.columns([1, 3])
        with threshold_col1:
            st.metric("Qualification Threshold", "≥ 2.0/5.0")
        with threshold_col2:
            if final_score >= 2.0:
                st.success("✅ **QUALIFIED** - Candidate meets the minimum requirements for interview")
            else:
                st.error("❌ **NOT QUALIFIED** - Candidate does not meet minimum requirements")
        
        # Display recommendation
        recommendation = overall_assessment.get("recommendation", "No recommendation available")
        st.info(f"**Recommendation:** {recommendation}")
    
    
    
    # Display question counts
    if analysis.get("questions"):
        questions = analysis["questions"]
        st.markdown("#### 🎯 Generated Questions")
        
        metrics_cols = st.columns(3)
        question_types = ["technical", "behavioral", "situational"]
        
        total_questions = 0
        for i, q_type in enumerate(question_types):
            count = len(questions.get(q_type, []))
            total_questions += count
            with metrics_cols[i]:
                st.metric(f"{q_type.title()}", count)
        
        st.session_state.total_questions = total_questions
        return True, final_score
    
    return False, final_score

def get_next_question_streamlit(state: Dict) -> Optional[str]:
    """Get next question for Streamlit interface"""
    try:
        # Check if we need a follow-up question
        if state.get("follow_up_needed", False):
            last_qa = state["chat_history"][-1] if state["chat_history"] else {}
            prompt = f"""
            You are a friendly interviewer. Based on the candidate's response, ask a follow-up question.
            
            Previous Question: {last_qa.get('question', 'N/A')}
            Candidate's Answer: {last_qa.get('answer', 'N/A')}
            
            Generate a conversational follow-up that asks for more specific details.
            Keep it conversational. Return ONLY the question.
            """
            return call_llm(prompt)
        
        # Get current question type and index
        current_type = state.get("current_question_type", "technical")
        type_questions = state["questions"].get(current_type, [])
        type_index = state.get("question_indices", {}).get(current_type, 0)
        
        # Check if we have more questions in current type
        if type_index < len(type_questions):
            return type_questions[type_index]["question"]
        
        # Move to next question type
        order = state["question_type_order"]
        try:
            current_idx = order.index(current_type)
            if current_idx + 1 < len(order):
                next_type = order[current_idx + 1]
                state["current_question_type"] = next_type
                
                # Get first question of next type
                next_questions = state["questions"].get(next_type, [])
                if next_questions:
                    return next_questions[0]["question"]
        except (ValueError, IndexError):
            pass
        
        return None
    except Exception as e:
        st.error(f"Error getting next question: {str(e)}")
        return None

def process_user_response(user_input: str):
    """Process user response and update interview state"""
    try:
        state = st.session_state.interview_state
        
        # Check if this is the intro phase
        if st.session_state.get('interview_phase') == 'intro':
            return process_intro_response(user_input)
        
        # Check if this is a follow-up response
        is_follow_up_response = st.session_state.get('expecting_followup_response', False)
        
        if is_follow_up_response:
            return process_followup_response(user_input)
        
        # Add to chat history for regular interview questions
        chat_entry = {
            "question": st.session_state.current_question,
            "answer": user_input,
            "timestamp": "now"
        }
        
        state["chat_history"].append(chat_entry)
        st.session_state.chat_history.append({
            "type": "candidate",
            "content": user_input
        })
        
        # Analyze response depth
        state["user_response"] = user_input
        state["current_question"] = st.session_state.current_question
        
        try:
            depth_analysis = analyze_response_depth(state)
            should_follow_up = (
                depth_analysis.get("needs_followup", False) and 
                state.get("current_topic_depth", 0) < 1 and
                depth_analysis.get("depth_score", 3) < 3
            )
        except:
            should_follow_up = False
            depth_analysis = {"needs_followup": False, "depth_score": 3}
        
        # Evaluate response
        question = st.session_state.current_question
        jd = state["job_description"][:300]
        
        # Get expected answer
        current_type = state.get("current_question_type", "technical")
        current_index = state["question_indices"][current_type]
        questions_list = state["questions"].get(current_type, [])
        expected_answer = ""
        if current_index < len(questions_list):
            expected_answer = questions_list[current_index].get("answer", "")
        
        eval_prompt = f"""
        Evaluate this interview response:
        
        Question: {question}
        Answer: {user_input}
        Expected Answer: {expected_answer}
        Job Requirements: {jd}...
        
        JSON Response:
        {{
            "Question": "{question}", 
            "User_Answer": "{user_input}",
            "Score": 1-5,
            "Reasoning": "explain why you gave this score"
        }}
        """
        
        try:
            eval_result = call_llm(eval_prompt)
            # Clean up JSON response
            import re
            cleaned_response = re.sub(r"^```json|```$", "", eval_result.strip(), flags=re.MULTILINE).strip("` \n")
            evaluation = json.loads(cleaned_response)
        except:
            evaluation = {
                "Question": question,
                "User_Answer": user_input,
                "Score": 3,
                "Reasoning": "Could not parse evaluation"
            }
        
        # Store evaluation
        evaluation["depth_analysis"] = depth_analysis
        evaluation["is_main_question"] = True  # Mark as main question
        st.session_state.evaluation_results.append(evaluation)
        
        # Update state based on follow-up decision
        if should_follow_up:
            state["follow_up_needed"] = True
            state["current_topic_depth"] = state.get("current_topic_depth", 0) + 1
            st.session_state.expecting_followup_response = True  # Flag for next response
            # Don't increment question count or move to next question yet
        else:
            # Move to next question
            current_type = state.get("current_question_type", "technical")
            state["question_indices"][current_type] += 1
            state["current_topic_depth"] = 0
            state["follow_up_needed"] = False
            st.session_state.question_indices[current_type] += 1
            st.session_state.question_count += 1  # Only increment for main questions
        
        # Update session state
        st.session_state.interview_state = state
        
        return True
        
    except Exception as e:
        st.error(f"Error processing response: {str(e)}")
        return False

def process_followup_response(user_input: str):
    """Handle follow-up response separately"""
    try:
        state = st.session_state.interview_state
        
        # Add follow-up response to chat history (with different marking)
        st.session_state.chat_history.append({
            "type": "candidate",
            "content": user_input
        })
        
        # Update the last evaluation with follow-up info
        if st.session_state.evaluation_results:
            last_eval = st.session_state.evaluation_results[-1]
            last_eval["follow_up_answer"] = user_input
            last_eval["has_followup"] = True
            
            # Optionally re-evaluate with both answers
            main_answer = last_eval.get("User_Answer", "")
            combined_eval_prompt = f"""
            Re-evaluate this interview response considering both the main answer and follow-up:
            
            Question: {last_eval.get("Question", "")}
            Main Answer: {main_answer}
            Follow-up Answer: {user_input}
            
            JSON Response:
            {{
                "Score": 1-5,
                "Reasoning": "explain the updated score considering both responses"
            }}
            """
            
            try:
                eval_result = call_llm(combined_eval_prompt)
                import re
                cleaned_response = re.sub(r"^```json|```$", "", eval_result.strip(), flags=re.MULTILINE).strip("` \n")
                updated_eval = json.loads(cleaned_response)
                last_eval["Score"] = updated_eval.get("Score", last_eval["Score"])
                last_eval["Reasoning"] = f"Updated after follow-up: {updated_eval.get('Reasoning', last_eval['Reasoning'])}"
            except:
                last_eval["Reasoning"] += f" [Follow-up provided: {user_input[:50]}...]"
        
        # Now move to next question
        current_type = state.get("current_question_type", "technical")
        state["question_indices"][current_type] += 1
        state["current_topic_depth"] = 0
        state["follow_up_needed"] = False
        st.session_state.question_indices[current_type] += 1
        st.session_state.question_count += 1  # Now increment for completed question
        st.session_state.expecting_followup_response = False  # Reset flag
        
        # Update session state
        st.session_state.interview_state = state
        
        return True
        
    except Exception as e:
        st.error(f"Error processing follow-up response: {str(e)}")
        return False

def process_intro_response(user_input: str):
    """Handle the introduction response separately"""
    try:
        # Add intro response to chat history (but not to formal evaluation)
        st.session_state.chat_history.append({
            "type": "candidate", 
            "content": user_input
        })
        
        # Generate a personalized response
        response_prompt = f"""
        You are a friendly interviewer. The candidate just introduced themselves with: "{user_input}"
        
        Respond warmly and naturally in 1-2 sentences, then transition to mention that you'll now start with technical questions. Keep it conversational and encouraging.
        
        Example: "Thank you for that introduction, [name/background mention]. Now let's dive into some technical questions to better understand your expertise."
        """
        
        try:
            interviewer_response = call_llm(response_prompt)
        except:
            interviewer_response = "Thank you for that introduction! Now let's dive into some technical questions to better understand your expertise."
        
        # Add interviewer response
        st.session_state.chat_history.append({
            "type": "interviewer",
            "content": interviewer_response
        })
        
        # Add transition message
        transition_message = "🔧 Let's start with some technical questions to assess your expertise:"
        st.session_state.chat_history.append({
            "type": "interviewer",
            "content": transition_message
        })
        
        # Transition to technical questions
        st.session_state.interview_phase = 'technical'
        st.session_state.interview_state["interview_phase"] = 'technical'
        st.session_state.interview_state["current_question_type"] = 'technical'
        
        return True
        
    except Exception as e:
        st.error(f"Error processing intro response: {str(e)}")
        return False

def render_chat_interface():
    """Render the chat interface"""
    st.markdown("### 💬 Interview Chat")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message["type"] == "interviewer":
                st.markdown(f"""
                <div class="chat-message interviewer-message">
                    <strong>🤖 Interviewer:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message candidate-message">
                    <strong>👤 You:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Progress indicator (only for actual interview questions, not intro)
    if st.session_state.get('interview_phase') != 'intro':
        progress_col1, progress_col2 = st.columns([3, 1])
        with progress_col1:
            progress = st.session_state.question_count / max(st.session_state.total_questions, 1)
            st.progress(progress)
        with progress_col2:
            # Adjust question count to not include intro
            current_q_num = st.session_state.question_count
            if st.session_state.get('interview_phase') == 'technical' and st.session_state.question_count == 0:
                current_q_num = 1
            
            # Show if this is a follow-up question
            if st.session_state.get('expecting_followup_response', False):
                st.write(f"Question {current_q_num}/{st.session_state.total_questions}")
                st.caption("🔄 Follow-up question")
            else:
                st.write(f"Question {current_q_num}/{st.session_state.total_questions}")
    else:
        # Show intro phase indicator
        st.info("🎯 Introduction Phase - Let's get to know you!")
    
    return chat_container

def start_interview():
    """Initialize and start the interview"""
    if not st.session_state.interview_started:
        st.session_state.interview_started = True
        
        # Introduction
        intro_message = "👋 Hello! Welcome to your interview today. I'm excited to learn more about you and your background. Let's start with a quick introduction. Could you tell me a bit about yourself?"
        
        st.session_state.chat_history.append({
            "type": "interviewer",
            "content": intro_message
        })
        
        st.session_state.current_question = "Tell me about yourself"
        st.session_state.stage = 'interview'
        st.session_state.interview_phase = 'intro'  # Set to intro phase

def display_final_evaluation():
    """Display final evaluation results"""
    st.markdown("### 📊 Interview Evaluation Summary")
    
    if not st.session_state.evaluation_results:
        st.warning("No evaluation results available.")
        return
    
    # Calculate overall statistics
    scores = [eval_result.get("Score", 3) for eval_result in st.session_state.evaluation_results]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Average Score", f"{avg_score:.1f}/5")
    with col2:
        st.metric("Questions Answered", len(st.session_state.evaluation_results))
    with col3:
        st.metric("Highest Score", max(scores) if scores else 0)
    with col4:
        st.metric("Lowest Score", min(scores) if scores else 0)
    
    # Detailed evaluation
    st.markdown("#### Detailed Question-by-Question Analysis")
    
    for i, result in enumerate(st.session_state.evaluation_results, 1):
        score = result.get('Score', 'N/A')
        has_followup = result.get('has_followup', False)
        title_suffix = " (with follow-up)" if has_followup else ""
        
        with st.expander(f"Question {i}: Score {score}/5{title_suffix}"):
            st.write(f"**Question:** {result.get('Question', 'N/A')}")
            st.write(f"**Your Main Answer:** {result.get('User_Answer', 'N/A')}")
            
            # Show follow-up answer if available
            if has_followup and 'follow_up_answer' in result:
                st.write(f"**Follow-up Answer:** {result.get('follow_up_answer', 'N/A')}")
            
            st.write(f"**Score:** {score}/5")
            st.write(f"**Evaluation:** {result.get('Reasoning', 'N/A')}")
            
            # Depth analysis if available
            if 'depth_analysis' in result:
                depth = result['depth_analysis']
                st.write(f"**Response Depth:** {depth.get('depth_score', 'N/A')}/5")
                if has_followup:
                    st.info("📝 This question included a follow-up for additional details")

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🤖 AI Interview Agent</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📋 Interview Progress")
        
        if st.session_state.stage == 'upload':
            st.info("📤 Upload files to start")
        elif st.session_state.stage == 'analysis':
            st.info("🔍 Analyzing documents...")
        elif st.session_state.stage == 'interview':
            if st.session_state.get('interview_phase') == 'intro':
                st.info("🎯 Introduction Phase")
                st.write("Getting to know you...")
            else:
                st.success(f"💬 Interview in progress\nQuestion {st.session_state.question_count}")
                
                # Question type breakdown
                st.markdown("#### Question Types")
                for q_type in ['technical', 'behavioral', 'situational']:
                    completed = st.session_state.question_indices.get(q_type, 0)
                    total = len(st.session_state.interview_state.get("questions", {}).get(q_type, []))
                    progress_val = completed / max(total, 1)
                    st.progress(progress_val)
                    st.write(f"{q_type.title()}: {completed}/{total}")
                    
                    # Highlight current question type
                    if st.session_state.interview_state.get("current_question_type") == q_type:
                        st.write("👉 *Current*")
                
        elif st.session_state.stage == 'results':
            st.success("✅ Interview completed!")
        
        # Reset button
        if st.button("🔄 Start New Interview"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content based on stage
    if st.session_state.stage == 'upload':
        st.markdown("### 📤 Upload Documents")
        st.info("Please upload both your resume and the job description as PDF files to begin the AI interview process.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📄 Resume")
            resume_file = st.file_uploader("Upload Resume (PDF)", type=['pdf'], key="resume")
        
        with col2:
            st.markdown("#### 💼 Job Description")
            jd_file = st.file_uploader("Upload Job Description (PDF)", type=['pdf'], key="jd")
        
        if resume_file and jd_file:
            if st.button("🚀 Start Analysis", type="primary"):
                with st.spinner("Analyzing documents..."):
                    # Save uploaded files
                    resume_path = save_uploaded_file(resume_file)
                    jd_path = save_uploaded_file(jd_file)
                    
                    if resume_path and jd_path:
                        # Run analysis
                        analysis_result = run_analysis(resume_path, jd_path)
                        
                        if "error" not in analysis_result:
                            st.session_state.analysis_results = analysis_result
                            st.session_state.interview_state = analysis_result
                            st.session_state.analysis_complete = True
                            st.session_state.stage = 'analysis'
                            st.rerun()
                        else:
                            st.error(f"Analysis failed: {analysis_result.get('error', 'Unknown error')}")
    
    elif st.session_state.stage == 'analysis':
        # Display analysis results
        success, final_score = display_analysis_results(st.session_state.analysis_results)
        
        if success:
            st.markdown("---")
            
            # Check if candidate meets minimum score requirement
            if final_score >= 2.0:
                st.success(f"🎉 **Qualification Status: PASSED** (Score: {final_score:.1f}/5.0)")
                st.info("✅ You meet the minimum requirements to proceed to the interview round!")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🎤 Start Interview", type="primary", use_container_width=True):
                        start_interview()
                        st.rerun()
            else:
                st.error(f"❌ **Qualification Status: NOT QUALIFIED** (Score: {final_score:.1f}/5.0)")
                st.warning("⚠️ Unfortunately, your profile does not meet the minimum requirements (Score ≥ 2.0) for this position.")
                
                # Show what they can do
                st.markdown("#### 💡 What you can do:")
                st.markdown("- **Improve your resume** by adding missing skills and experiences")
                st.markdown("- **Gain more relevant experience** in the required technologies")
                st.markdown("- **Upload a different resume** if you have an updated version")
                st.markdown("- **Try applying for a different position** that better matches your profile")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("📤 Upload New Documents", type="secondary", use_container_width=True):
                        # Reset to upload stage
                        st.session_state.stage = 'upload'
                        st.session_state.analysis_complete = False
                        st.session_state.analysis_results = {}
                        st.rerun()
    
    elif st.session_state.stage == 'interview':
        # Chat interface
        render_chat_interface()
        
        # Get next question if needed
        if not st.session_state.interview_ended:
            if st.session_state.current_question:
                # User input
                with st.form("response_form", clear_on_submit=True):
                    # Different placeholder for follow-up questions
                    if st.session_state.get('expecting_followup_response', False):
                        placeholder_text = "Please provide more details or examples..."
                        button_text = "Submit Follow-up"
                    else:
                        placeholder_text = "Type your answer here..."
                        button_text = "Submit Response"
                    
                    user_input = st.text_area("Your Response:", height=100, placeholder=placeholder_text)
                    submitted = st.form_submit_button(button_text, type="primary")
                
                if submitted and user_input.strip():
                    # Process response
                    if process_user_response(user_input.strip()):
                        # Check if we just finished the intro
                        if st.session_state.get('interview_phase') == 'technical' and st.session_state.current_question == "Tell me about yourself":
                            # Get first technical question
                            next_question = get_next_question_streamlit(st.session_state.interview_state)
                            if next_question:
                                st.session_state.current_question = next_question
                                st.session_state.chat_history.append({
                                    "type": "interviewer",
                                    "content": next_question
                                })
                        else:
                            # Handle both follow-up and regular questions
                            next_question = get_next_question_streamlit(st.session_state.interview_state)
                            
                            if next_question:
                                st.session_state.current_question = next_question
                                st.session_state.chat_history.append({
                                    "type": "interviewer",
                                    "content": next_question
                                })
                            else:
                                # Interview ended
                                st.session_state.interview_ended = True
                                st.session_state.stage = 'results'
                                final_message = "🎉 Thank you for completing the interview! Here are your results."
                                st.session_state.chat_history.append({
                                    "type": "interviewer",
                                    "content": final_message
                                })
                        
                        st.rerun()
            else:
                st.error("No current question available. Please restart the interview.")
    
    elif st.session_state.stage == 'results':
        display_final_evaluation()
        
        # Option to download results
        if st.session_state.evaluation_results:
            results_json = json.dumps({
                "evaluation": st.session_state.evaluation_results,
                "analysis": st.session_state.analysis_results.get("resume_jd_analysis", {})
            }, indent=2)
            
            st.download_button(
                "📥 Download Results (JSON)",
                results_json,
                file_name="interview_results.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main() 