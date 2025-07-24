import re
import json
from typing import Dict, List

class QuestionGenerator:
    def __init__(self, llm):
        self.llm = llm

    def generate_technical_questions(self, technical_context: dict,  difficulty_level: str = "intermediate", jd_text: str = "") -> List[Dict]:
        """Generate technical interview questions based on specific skill area"""
        prompt = f"""
        You are a technical interviewer preparing for a candidate with the following background:

        Generate 2 {difficulty_level} level technical interview questions on the basis of the candidate's background.
        
        Candidate's Technical Context:
        - Skills: {technical_context.get("skills", [])}
        - Projects: {technical_context.get("projects", [])}
        - Experience: {technical_context.get("relevant_experience", [])}
        
        The questions should:
        1. Test practical knowledge 
        2. Include both theoretical and hands-on aspects
        3. Be suitable for {difficulty_level} candidates
        4. Leverage actual project experience 
        
        Generate 1 technical interview question based on the JD's main focused topics[such as AI, ML, DevOps, etc].
        
        Job Description:
        {jd_text}
        
        Make sure the questions is with in 1-2 lines and inculde an ideal answer within a line to verify correctness.

        Return a JSON object with question and answer structured as follows
        {{
            "question": "Short technical question here?",
            "answer": "Ideal correct answer here.",
        }}

    
        """ 
        try:
            response = self.llm.invoke(prompt)
            cleaned_response = re.sub(r"^```json|```$", "", response.strip(), flags=re.MULTILINE).strip("` \n")
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse technical questions response",
                "raw_output": response  
            }


    def generate_behavioral_questions(self, behavioral_context: dict) -> List[Dict]:
        """Generate behavioral interview questions"""
        prompt = f"""
        Generate 1 behavioral interview question based on the candidate's background.
        
        Candidate's Behavioral Context:
        - Leadership: {behavioral_context.get("leadership", [])}
        - Teamwork: {behavioral_context.get("teamwork", [])}
        - Communication: {behavioral_context.get("communication", [])}
        
        Focus on:
        1. Leadership and initiative
        2. Collaboration and communication
        3. Project management and ownership
        4. Conflict resolution and adaptability
        5. Self-learning and growth mindset

        Use the STAR method. Make the questions specific to their experience.
        
        Make sure the questions is with in 1-2 lines and inculde an ideal answer within a line to verify correctness .

        Return a JSON object with question and answer structured as follows
        {{
            "question": "Short behavioral question here?",
            "answer": "Ideal correct answer here.",
        }}

        """
        try:
            response = self.llm.invoke(prompt)
            cleaned_response = re.sub(r"^```json|```$", "", response.strip(), flags=re.MULTILINE).strip("` \n")
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse behavioral questions response",
                "raw_output": response
            }

    def generate_situational_questions(self, situational_context: dict) -> List[Dict]: 
        """Generate situational interview questions"""
        prompt = f"""
        Generate 1 situational interview question based on the candidate's background.
        
        Candidate's Situational Context:
        - Problem Solving: {situational_context.get("problem_solving", [])}
        - Challenges: {situational_context.get("challenges", [])}
        - Decision Making: {situational_context.get("decision_making", [])}
        
        Include realistic scenarios that test:
        1. Strategic decision making
        2. Handling ambiguity
        3. Conflict or stakeholder management
        4. Prioritization and resource constraints
        5. Innovation under pressure

        Make sure the questions is with in 1-2 lines and inculde an ideal answer within a line to verify correctness .

        Return a JSON object with question and answer structured as follows
        {{
            "question": "Short situational question here?",
            "answer": "Ideal correct answer here.",
        }}
        """
        try:
            response = self.llm.invoke(prompt)
            cleaned_response = re.sub(r"^```json|```$", "", response.strip(), flags=re.MULTILINE).strip("` \n")
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse situational questions response",
                "raw_output": response
            }



def generate_questions_tool(state: dict) -> dict:
    from llm import GeminiLLM  # lazy import
    """
    Tool function to generate interview questions from context_split
    and append them to the state dict.
    """
    if "context_split" not in state or "error" in state["context_split"]:
        state["error"] = "⚠️ Missing or invalid context_split. Cannot generate questions."
        return state
    
    jd_text = state["job_description"]
    context = state["context_split"]
    generator = QuestionGenerator(GeminiLLM())

    technical_q = generator.generate_technical_questions(context["technical_context"], "Medium", jd_text)
    behavioral_q = generator.generate_behavioral_questions(context["behavioral_context"])
    situational_q = generator.generate_situational_questions(context["situational_context"])

    state["questions"] = {
        "technical": [technical_q] if not isinstance(technical_q, list) else technical_q,
        "behavioral": [behavioral_q] if not isinstance(behavioral_q, list) else behavioral_q,
        "situational": [situational_q] if not isinstance(situational_q, list) else situational_q,
    }

    return state
