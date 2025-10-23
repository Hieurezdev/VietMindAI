from google.adk.agents import Agent
from config.config import get_settings
from .prompt import root_agent_instruction
from .sub_agents.general_agent.agent import general_agent
from .sub_agents.crisis_detection_agent.agent import crisis_detection_agent
from dotenv import load_dotenv



load_dotenv()



root_agent = Agent(
    name = "root_agent",
    model = get_settings().gemini_model,
    description= "Root agent có nhiệm vụ điều phối và chuyển giao các câu hỏi đến các sub agent phù hợp",
    instruction= root_agent_instruction,
    sub_agents= [general_agent, crisis_detection_agent]
)   