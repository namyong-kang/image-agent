# tools.py (요지: product_image_path 지원 + SCENE/PRODUCT 함께 전달)
import os
from dotenv import load_dotenv

from google import genai
from google.genai import types
from google.adk.tools import ToolContext

from pathlib import Path
import logging

logger = logging.getLogger(__name__)

GENERATE_CONTENT_CONFIG = types.GenerateContentConfig(
    temperature=0.6, top_p=0.9, max_output_tokens=8192,
    response_modalities=["IMAGE"],
    safety_settings=[
        types.SafetySetting(category=c, threshold="BLOCK_NONE") for c in
        ["HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_DANGEROUS_CONTENT", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_HARASSMENT"]
    ],
    system_instruction=[types.Part.from_text(text=(
        "You are a visual compositor. Use the provided SCENE image as background "
        "and the PRODUCT image as the refrigerator reference. "
        "Place/scale the product naturally in the scene; keep realistic lighting/shadows. "
        "Only return an image."
    ))],
)

load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
CLIENT = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

def _part_from_local_image(path_str: str) -> types.Part:
    p = Path(path_str)
    if not p.exists():
        raise FileNotFoundError(f"Local product image not found: {p}")
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return types.Part.from_bytes(data=p.read_bytes(), mime_type=mime)

def process_stream_response(contents: list):
    image_found=False
    model_response_text=""
    received_image_part=None

    for chunk in CLIENT.models.generate_content_stream(
        model="gemini-2.5-flash-image", contents=contents, config=GENERATE_CONTENT_CONFIG,
    ):
        for part in chunk.candidates[0].content.parts:
            if getattr(part, "text", None):
                model_response_text += part.text
            if getattr(part, "inline_data", None):
                image_found = True
                received_image_part = part
                logger.info("✅ Image Created")

    return image_found, model_response_text, received_image_part

async def generate_edit_image(
     prompt: str,
     tool_context: ToolContext,
     product_image_path: str = "",
     color_hint: str = ""
):                # <-- was: dict[str, any]
    """
    주방 SCENE(사용자 업로드) + 로컬 PRODUCT 이미지를 합성해 미리보기 생성.
    결과 이미지는 ADK artifact 'last_image.png'로 저장.
    """
    filename = "last_image.png"

    # 1) 사용자 텍스트 지시 (color_hint가 있으면 간단히 첨언)
    base_text = (
        "SCENE=the following photo. PRODUCT=the following reference image. "
        "Composite PRODUCT into SCENE with natural scale, perspective, and soft shadow."
    )
    if color_hint:
        base_text += f" Keep product color coherence to '{color_hint}'."
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=base_text)])]

    # 2) SCENE 붙이기 (사용자 업로드에서)
    user_content = tool_context.user_content
    added_scene = False
    for part in getattr(user_content, "parts", []):
        if getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
            contents[0].parts.append(part)
            added_scene = True
            break

    if not added_scene:
        # 마지막 아티팩트 로딩(옵션)
        prev = await tool_context.load_artifact(filename=filename)
        if prev and getattr(prev, "inline_data", None):
            contents[0].parts.append(prev)
            added_scene = True

    # 3) PRODUCT 붙이기 (로컬 경로)
    if product_image_path:
        try:
            contents[0].parts.append(_part_from_local_image(product_image_path))
        except Exception as e:
            logger.exception(f"Failed to attach product image: {e}")

    # 4) 호출
    image_found, model_response_text, received_image_part = process_stream_response(contents)
    if not image_found:
        image_found, model_response_text, received_image_part = process_stream_response(contents)
    if not image_found:
        return {"status": "fail", "message": model_response_text}

    await tool_context.save_artifact(filename, received_image_part)
    return {"status": "success", "message": model_response_text, "artifact_name": filename}
