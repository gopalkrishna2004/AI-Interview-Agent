# tools/context_splitter.py
import re
import json
from typing import Dict


class ContextSplitter:
    def __init__(self, llm, resume, job_description):
        self.llm = llm
        self.resume = resume
        self.job_description = job_description
    
    def context_split(self):
        """Split resume into technical, behavioral, and situational contexts"""
        prompt = f"""
        You are an expert AI hiring assistant.

        Given the candidate's resume and the job description below, split the resume into three distinct contexts:

        1. Technical Context: which are relevant or slightly relevant to the job description.
        - Technical skills, tools, frameworks
        - Projects demonstrating technical abilities
        - Research or implementations relevant to the job
        - Code or system architecture experience

        2. Behavioral Context:
        - Leadership experiences
        - Team collaboration examples
        - Project management instances
        - Communication achievements
        - Initiative examples

        3. Situational Context:
        - Problem-solving scenarios
        - Challenge resolution examples
        - Ambiguous situation handling
        - Fast-paced environment experience
        - Critical decision-making instances

        Resume:
        {self.resume}
        
        Job Description:
        {self.job_description}
        
        Return a JSON object with these contexts structured as follows:
        
        {{
            "technical_context": {{
                "skills": [],
                "projects": [],
                "relevant_experience": []
            }},
            "behavioral_context": {{
                "leadership": [],
                "teamwork": [],
                "communication": []
            }},
            "situational_context": {{
                "problem_solving": [],
                "challenges": [],
                "decision_making": []
            }}
        }}
        """
        try:
            context = self.llm.invoke(prompt)
            cleaned_context = re.sub(r"^```json|```$", "", context.strip(), flags=re.MULTILINE).strip("` \n")
            return json.loads(cleaned_context)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse context split response",
                "raw_output": context
            }

def context_split_tool(state: dict) -> dict:
    from llm import GeminiLLM  # lazy import
    resume = state["resume"]  # Fixed: use text content, not PDF path
    jd = state["job_description"]  # Fixed: use text content, not PDF path
    
    
    # Create splitter instance
    splitter = ContextSplitter(GeminiLLM(), resume, jd)
    
    # Get context split
    context_split = splitter.context_split()
    state["context_split"] = context_split
    
    return state    
