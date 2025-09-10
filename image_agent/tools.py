import os
from dotenv import load_dotenv

from google import genai
from google.genai import types
from google.adk.tools import ToolContext

import logging

logger = logging.getLogger(__name__)

GENERATE_CONTENT_CONFIG = types.GenerateContentConfig(
        temperature=1, top_p=0.95, max_output_tokens=32768,
        response_modalities=["TEXT", "IMAGE"],
        safety_settings=[
            types.SafetySetting(category=c, threshold="BLOCK_NONE") for c in
            ["HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_DANGEROUS_CONTENT", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_HARASSMENT"]
        ],
        system_instruction=[types.Part.from_text(text="""Always respond with an image""")],
    )

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")

if not PROJECT_ID:
    logger.error("PROJECT_ID is not set")

CLIENT = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

def process_stream_response(contents: list): 

    image_found=False
    model_response_text=""
    received_image_part= None 

    for chunk in CLIENT.models.generate_content_stream(
        model="gemini-2.5-flash-image-preview", contents=contents, config=GENERATE_CONTENT_CONFIG,
    ):


        for part in chunk.candidates[0].content.parts:
            if part.text:
                model_response_text += part.text
                print(part.text, end="")
            
            if part.inline_data:
                image_found = True
                received_image_part = part
                logger.info("\n\n--- ✅ Image Created ---")
                
    return image_found, model_response_text, received_image_part
    
async def generate_edit_image(
    prompt: str,  tool_context: ToolContext) -> dict[str, any]:
    """Generating and editing images to support text/prompt.

    Args:
        prompt (str): the prompt to edit given images

    Returns:
        dict[str, str]: {"status": "STATUS", "message" : "RESPONSE"}
    """

    filename = "last_image.png"
    
    contents = [
        types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt)
                ]
            )
    ]

            
    user_content = tool_context.user_content

    uploaded_image = False

    # Iterate through parts of the user_content
    for i, part in enumerate(user_content.parts):
        if hasattr(part, 'inline_data') and getattr(part.inline_data, 'data', None):
            mime_type = part.inline_data.mime_type
            logger.info(f"tool: Found image part {i} with mime_type: {mime_type}")
            contents[0].parts.append(part)
            uploaded_image = True

    logger.info(f"contents : {contents[0]}")

    if not uploaded_image:
        load_image = await tool_context.load_artifact(filename=filename)

        if load_image and load_image.inline_data:
            logger.info(f"1) Successfully loaded latest Python artifact {load_image.inline_data.mime_type}.")
            contents[0].parts.append(load_image)

    image_found, model_response_text, received_image_part = process_stream_response(contents)

    if not image_found:
        logger.error("Generate image [1st try ]===========> no image data.")
        image_found, model_response_text, received_image_part = process_stream_response(contents)

    if not image_found:
        logger.error("Generate image [2nd try ]===========> no image data.")
        return {
            "status": "fail",
            "message": model_response_text,
        }

    await tool_context.save_artifact(filename, received_image_part)
    print(f"Image also saved as ADK artifact: {filename}")

    return {
        "status": "success",
        "message": model_response_text,
        "artifact_name": filename,
    }
