from google.adk.agents import Agent
from .prompt import (image_agent_instruction, architecture_agent_instruction, root_agent_instruction)

#from google.adk.tools import google_search
from .tools import generate_edit_image


image_agent = Agent(
    name="image_agent",
    model="gemini-2.5-flash",
    description="An agent responsible for generating and modifying images",
    instruction=image_agent_instruction,
    tools=[generate_edit_image],
)

"""
architecture_agent = Agent(
    name="architecture_agent",
    model="gemini-2.5-flash",
    description="This agent provides a detailed breakdown and comprehensive explanation of system architecture diagrams",
    instruction=architecture_agent_instruction,
)
"""
root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    description="An AI agent designed for image-related tasks, including content analysis, generation, and modification",
    instruction=root_agent_instruction,
    #sub_agents=[image_agent,architecture_agent]
    sub_agents=[image_agent]
)
