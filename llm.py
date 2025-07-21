# llm.py
from langchain_google_genai import ChatGoogleGenerativeAI
import os

os.environ["GOOGLE_API_KEY"] = "AIzaSyC6yS20MFgeggekm94UkWSvRLqcKsnLEOo"

class GeminiLLM:
    def __init__(self, model_name="gemini-2.5-flash"):
        self.model = ChatGoogleGenerativeAI(model=model_name)

    def invoke(self, prompt: str):
        response = self.model.invoke(prompt)
        return response.content
