from google.adk.agents import Agent
from .prompt import agent_instruction

#from google.adk.tools import google_search
from .tools import generate_edit_image

root_agent = Agent(
    name="image_agent",
    model="gemini-2.5-flash",
    description="An agent responsible for generating and modifying images",
    instruction=agent_instruction,
    tools=[generate_edit_image],
)
