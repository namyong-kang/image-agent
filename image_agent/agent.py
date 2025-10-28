from google.adk.agents import Agent
from .prompt import (image_agent_instruction, architecture_agent_instruction, root_agent_instruction)

#from google.adk.tools import google_search
from .tools import generate_edit_image


# image_agent = Agent(
#     name="image_agent",
#     model="gemini-2.5-flash",
#     description="너는 인테리어 전문가야. 사용자가 업로드 한, 이미지를 분석해서 너가 가지고 있는 냉장고 리스트를 가지고, 어떤 냉장고가 해당 집의 인테리어에 어울리지 선택해야돼. ",
#     instruction=image_agent_instruction,
#     tools=[generate_edit_image],
# )

# agent.py
# 핵심 아이디어: 카탈로그 JSON을 프롬프트에 직접 포함하고, 출력 형식을 강제
# 기존 프로젝트의 Agent 클래스를 그대로 쓰되, run_image_selection 같은 오케스트레이션은 제거
from typing import List, Dict, Any
import json

# (선택) 이미지 합성 도구가 필요하면 tools.py의 generate_edit_image를 가져오세요.
# from tools import generate_edit_image

# 1) 샘플 카탈로그 (운영 시 실제 데이터로 교체)
BESPOKE_CATALOG: List[Dict[str, Any]] = [
    {
        "name": "Bespoke 4-Door Flex™ 875L",
        "url": "https://images.example.com/bespoke/4df-875/hero.jpg",
        "colors": ["Clean White", "Satin Sky Blue", "Cotta Charcoal", "Satin Beige", "Matt Black"]
    },
    {
        "name": "Bespoke Bottom Freezer 390L",
        "url": "https://images.example.com/bespoke/bmf-390/hero.jpg",
        "colors": ["Morning Blue", "Clean Pink", "Clean White", "Cotta White", "Satin Navy"]
    },
    {
        "name": "Bespoke Family Hub™ 875L",
        "url": "https://images.example.com/bespoke/fhub-875/hero.jpg",
        "colors": ["Glam Peach", "Glam Navy", "Glam White", "Cotta Charcoal", "Clean White"]
    },
    {
        "name": "Bespoke AI Convertible 700L",
        "url": "https://images.example.com/bespoke/aiconv-700/hero.jpg",
        "colors": ["Satin Sky Blue", "Satin Beige", "Clean White", "Cotta Charcoal"]
    }
]

# 2) 출력 형식 강제 (추가 텍스트 금지)
OUTPUT_SCHEMA = """
반드시 아래 JSON 배열 하나만 출력하라. 다른 말/코드블록/마크다운/설명 금지.

[
  {
    "query": "<사용자의 원래 쿼리>",
    "product": {
      "name": "<선택한 냉장고 모델명(카탈로그 name 중 하나)>",
      "url": "<해당 냉장고 대표이미지 url(카탈로그 url 중 해당 모델의 것)>",
      "color": "<선택한 비스포크 컬러(카탈로그 colors 중 하나)>"
    },
    "mood": "<인테리어 분석 + 왜 이 모델/컬러가 어울리는지 근거>"
  }
]
"""

# 3) 메인 에이전트 프롬프트: 모델이 이미지(비전) + JSON을 보고 직접 선택
image_agent_instruction_new = f"""
너는 인테리어 전문가다. 사용자가 올린 실내 사진(주방/거실)을 비전으로 분석해
아래 카탈로그 JSON 리스트 중 **정확히 하나**의 냉장고와 **그 모델이 지원하는 컬러 중 하나**를 선택하라.

선정 기준:
- 컬러/톤 매칭: 사진의 주요 색상 팔레트, 조도(밝음/어두움), 재질(무광/유광/우드/메탈)과 조화롭게.
- 공간 현실성: 과도한 대비/이질감은 피하고, 주변 가구 톤과 질감 일관성 고려.
- 컬러 제약: 반드시 해당 모델의 colors 배열에서만 선택.

카탈로그(JSON):
{json.dumps(BESPOKE_CATALOG, ensure_ascii=False, indent=2)}

출력 형식:
{OUTPUT_SCHEMA}

주의:
- 출력은 오직 위 JSON 배열 한 개.
- 모델명/URL/컬러는 반드시 카탈로그의 값과 정확히 일치해야 함.
- 내부 추론/메모는 숨기고, 최종 출력만 JSON으로.
"""


image_agent = Agent(
    name="image_agent",
    model="gemini-2.5-flash",
    description="사용자 업로드 이미지를 분석해 카탈로그 JSON에서 최적의 비스포크 냉장고/컬러를 하나 선택하고 JSON으로만 출력한다.",
    instruction=image_agent_instruction_new,  # 새 프롬프트
    tools=[generate_edit_image],         # 필요 없으면 제거 가능
)


architecture_agent = Agent(
    name="architecture_agent",
    model="gemini-2.5-flash",
    description="This agent provides a detailed breakdown and comprehensive explanation of system architecture diagrams",
    instruction=architecture_agent_instruction,
)


root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    description="An AI agent designed for image-related tasks, including content analysis, generation, and modification",
    instruction=root_agent_instruction,
    sub_agents=[image_agent,architecture_agent]
    # sub_agents=[image_agent]
)
