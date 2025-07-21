


from graph import build_initial_analysis_graph
from tools.interview_conversational_agent import build_interview_conversational_graph
from pprint import pprint
import json
import os

if __name__ == "__main__":
    # ✅ Define PDF file paths (don't try to read them as text)
    resume_pdf_path = "add resume path here"
    jd_pdf_path = "add jd path here"

    # ✅ Phase 1: Run analysis graph (Resume → JD → Context → Questions)
    initial_graph = build_initial_analysis_graph()

    initial_state = {
        "resume_pdf": resume_pdf_path,  # ✅ Pass PDF path, not content
        "jd_pdf": jd_pdf_path,         # ✅ Pass PDF path, not content
        "resume": "",  # Will be populated by analyzer from PDF
        "job_description": "",  # Will be populated by analyzer from PDF
        "resume_jd_analysis": {},
        "context_split": {},
        "questions": {},
        "current_question": None,
        "user_response": None,
        "chat_history": [],
        "evaluation": [],
        "question_index": 0,
        "question_type_order": ["technical", "behavioral", "situational"],
        "conversation_context": {},  # NEW
        "follow_up_needed": False,   # NEW
        "current_topic_depth": 0,    # NEW
        "current_question_type": "technical",  # NEW
        "interview_phase": "intro",  # NEW
        "question_indices": {        # NEW: Track progress per type
            "technical": 0,
            "behavioral": 0,
            "situational": 0
        }
    }

    print("🔄 Running initial analysis graph...")
    analyzed_state = initial_graph.invoke(initial_state)

    # ✅ Debug: Check analysis results
    print("\n🔍 Analysis Results Debug:")
    print(f"   - Resume JD Analysis type: {type(analyzed_state.get('resume_jd_analysis', {}))}")
    print(f"   - Resume JD Analysis keys: {list(analyzed_state.get('resume_jd_analysis', {}).keys())}")
    print(f"   - Has error in analysis: {'error' in analyzed_state.get('resume_jd_analysis', {})}")
    
    if "error" in analyzed_state.get("resume_jd_analysis", {}):
        print("❌ Error in resume_jd_analysis:", analyzed_state["resume_jd_analysis"]["error"])
        print("📄 Full analysis result:")
        pprint(analyzed_state["resume_jd_analysis"])

    if "error" in analyzed_state:
        print("❌ Error in main state:", analyzed_state["error"])
        exit()

    # ✅ Phase 2: Run interactive interview graph
    print("\n🎤 Starting the interview...\n")

    conversation_graph = build_interview_conversational_graph()
    final_state = conversation_graph.invoke(analyzed_state)

    # ✅ Print Final Evaluation
    print("\n📊 Final Evaluation Summary:\n")
    pprint(final_state["evaluation"])

    # ✅ Save Evaluation and Analysis to File
    output_dir = "C:/Users/krish/OneDrive/Documents/Desktop/Interview Agent"
    output_path = os.path.join(output_dir, "interview_summary.json")

    # ✅ Debug: Show what we're about to save
    print("\n💾 Preparing to save to JSON:")
    print(f"   - Evaluation length: {len(final_state.get('evaluation', []))}")
    print(f"   - Resume JD Analysis: {final_state.get('resume_jd_analysis', {})}")

    summary_to_save = {
        "evaluation": final_state.get("evaluation", []),
        "resume_jd_analysis": final_state.get("resume_jd_analysis", {})
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary_to_save, f, ensure_ascii=False, indent=4)

    print(f"\n✅ Saved evaluation and resume_jd_analysis to {output_path}")
    
    # ✅ Verify what was actually saved
    with open(output_path, "r", encoding="utf-8") as f:
        saved_content = json.load(f)
        print(f"📋 Verification - Resume JD Analysis in saved file: {bool(saved_content.get('resume_jd_analysis'))}")
        if saved_content.get('resume_jd_analysis'):
            print(f"   - Keys in saved analysis: {list(saved_content['resume_jd_analysis'].keys())}")
