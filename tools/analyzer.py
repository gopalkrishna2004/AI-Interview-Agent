# tools/analyzer.py
import json
import re
import pymupdf4llm
import os

class ResumeJDAnalyzer:
    def __init__(self, llm, resume_pdf_path, jd_pdf_path):
        self.llm = llm
        self.resume_pdf_path = resume_pdf_path
        self.jd_pdf_path = jd_pdf_path
        
    def _pdf_to_markdown(self, pdf_path):
        """Convert PDF to markdown using pymupdf4llm"""
        try:
            print(f"📄 Converting PDF: {pdf_path}")
            if not os.path.exists(pdf_path):
                return f"Error: PDF file not found at {pdf_path}"
            
            markdown_content = pymupdf4llm.to_markdown(pdf_path)
            print(f"✅ Successfully converted PDF. Content length: {len(markdown_content)} characters")
            return markdown_content
        except Exception as e:
            error_msg = f"Error converting PDF to markdown: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg

    def analyze_resume_and_jd(self):
        print("🔍 Starting Resume-JD Analysis...")
        
        # Convert PDFs to markdown
        resume_text = self._pdf_to_markdown(self.resume_pdf_path)
        jd_text = self._pdf_to_markdown(self.jd_pdf_path)
        
        # Check if PDF conversion was successful
        if "Error" in resume_text or "Error" in jd_text:
            return {
                "error": "PDF conversion failed",
                "resume_conversion": resume_text[:200] + "..." if len(resume_text) > 200 else resume_text,
                "jd_conversion": jd_text[:200] + "..." if len(jd_text) > 200 else jd_text
            }
        
        prompt = f"""
You are an expert AI hiring assistant.

Given the candidate's resume and the job description below, do the following in a step-by-step and return a structured JSON object:

---
### 🧠 STEP 1: Reasoning — Does Resume Match the JD?
1. Matching Skills
2. Aligned Experience
3. Research Alignment
4. Gaps or Missing Elements
5. Exceeds Expectations
6. Final Summary

Resume:
{resume_text}

Job Description:
{jd_text}

Return only the JSON object.

{{
  "matching_skills": [...],
  "aligned_experience": [...],
  "research_alignment": [...],
  "missing_elements": [...],
  "extra_strengths": [...],
  "overall_assessment": {{
    "fit": "Excellent | Good | Average | Weak",
    "final_score": "4.5/5",
    "recommendation": "Should this candidate be interviewed?"
  }}
}}
"""
        try:
            print("🤖 Calling LLM for analysis...")
            analysis = self.llm.invoke(prompt)
            print(f"✅ LLM response received. Length: {len(analysis)} characters")
            
            cleaned = re.sub(r"^```json|```$", "", analysis.strip(), flags=re.MULTILINE).strip("` \n")
            print("🧹 Cleaned LLM response for JSON parsing")
            
            parsed_result = json.loads(cleaned)
            print("✅ Successfully parsed JSON response")
            return parsed_result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {str(e)}")
            return {
                "error": "Invalid JSON returned by LLM.",
                "raw_output": analysis,
                "json_error": str(e)
            }
        except Exception as e:
            print(f"❌ LLM call failed: {str(e)}")
            return {
                "error": "LLM call failed",
                "exception": str(e)
            }

# LangGraph tool wrapper
def analyze_resume_jd_tool(state: dict) -> dict:
    from llm import GeminiLLM  # lazy import
    
    print("🚀 Starting analyze_resume_jd_tool...")
    
    try:
        # Get PDF paths from state
        resume_pdf = state["resume_pdf"]
        jd_pdf = state["jd_pdf"]

        
        # Create analyzer and get analysis
        analyzer = ResumeJDAnalyzer(GeminiLLM(), resume_pdf, jd_pdf)
        analysis_result = analyzer.analyze_resume_and_jd()
        print(analysis_result)
        
        state["resume_jd_analysis"] = analysis_result
        
        # Convert PDFs to text and store in expected keys for other tools
        try:
            print("📝 Converting PDFs to text for other tools...")
            import pymupdf4llm
            state["resume"] = pymupdf4llm.to_markdown(resume_pdf)
            state["job_description"] = pymupdf4llm.to_markdown(jd_pdf)
            print("✅ PDF to text conversion successful")
        except Exception as e:
            print(f"❌ PDF to text conversion failed: {str(e)}")
            state["resume"] = f"Error converting resume PDF: {str(e)}"
            state["job_description"] = f"Error converting JD PDF: {str(e)}"
        
        return state
        
    except Exception as e:
        print(f"❌ Critical error in analyze_resume_jd_tool: {str(e)}")
        state["resume_jd_analysis"] = {
            "error": "Critical error in analysis tool",
            "exception": str(e)
        }
        return state

