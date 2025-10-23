from google.adk.agents import LlmAgent
from .prompt import general_agent_instruction
from dotenv import load_dotenv
from google.genai import types
from config.config import get_settings


load_dotenv()


general_agent = LlmAgent(
    name="general_agent",
    model=get_settings().gemini_model,
    description="Trợ lý hỗ trợ cho việc trả lời và hỗ trợ các câu hỏi cơ bản",
    instruction=general_agent_instruction,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=1024
    )
)   