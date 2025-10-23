from google.adk.agents import LlmAgent, Agent
from google.adk.tools import google_search
from config.config import get_settings
from agents.sub_agents.crisis_detection_agent.prompt import crisis_detection_prompt
from google.adk.tools import agent_tool

search_agent = Agent(
    name="search_agent",
    model=get_settings().gemini_model,
    instruction="Tìm kiếm thông tin sử dụng Google Search",
    tools=[google_search]
)

crisis_detection_agent = Agent(
    name="crisis_detection_agent",
    model=get_settings().gemini_model,
    instruction=crisis_detection_prompt,
    description="Trợ lý tìm kiếm thông tin chuyên nghiệp bằng Google Search về quy trình xử lí khủng hoảng khi người dùng gặp vấn đề tâm lí nặng nề và có ý định tự tử hay huỷ hoại bản thân",
    tools=[agent_tool.AgentTool(agent=search_agent)],
    disallow_transfer_to_parent = True
)
