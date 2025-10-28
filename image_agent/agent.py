# agent.py
from google.adk.agents import Agent 
from .prompt import (root_agent_instruction)  # 다른 프롬프트 쓰면 유지
from .tools import generate_edit_image

from typing import List, Dict, Any
from pathlib import Path
import json

# 로컬 제품 이미지 경로
BASE_DIR = Path(__file__).resolve().parent
PRODUCT_DIR = BASE_DIR / "assets"

BESPOKE_CATALOG: List[Dict[str, Any]] = [
    {
        "name": "Bespoke AI 하이브리드 4도어 키친핏 Max+김치플러스 3도어 키친핏 623/313L",
        "url": str(PRODUCT_DIR / "hybrid_4door_kitchenfit.png"),
        "colors": ["코타 화이트"]
    },
    {
        "name": "Bespoke AI 냉장고 4도어 902L",
        "url": str(PRODUCT_DIR / "ai_4door_902l.png"),
        "colors": ["에센셜 화이트", "에센셜 베이지", "에센셜 다크 메탈"]
    }
]

# 최종 출력 스키마(단일 객체)
IMAGE_COMPOSE_OUTPUT = """
출력은 아래 JSON '한 개(배열 아님)'만. 다른 텍스트/마크다운/코드블록 금지.
{
  "query": "<사용자 원문>",
  "product": {
    "name": "<선택 모델명>",
    "url": "<선택 모델 이미지 로컬 경로>",
    "color": "<선택 컬러>"
  },
  "result": {
    "artifact_name": "<ADK artifact 파일명: last_image.png>",
    "notes": "<합성에 대한 짧은 설명>"
  }
}
"""

# 에이전트 인스트럭션: 선택 + 툴 호출 + 최종 JSON
image_agent_instruction = f"""
너는 인테리어/이미지 합성 전문가다.
입력: (1) 사용자 주방 이미지, (2) 아래 카탈로그 JSON

해야 할 일:
1) 사용자의 이미지를 분석하여 카탈로그(JSON) 중 **정확히 하나**의 냉장고와 **그 모델의 colors 중 하나**를 선택한다.
2) 반드시 툴 'generate_edit_image'를 호출하라.
   - 인자: product_image_path = 선택한 product.url (로컬 경로 문자열)
           color_hint        = 선택한 color (옵셔널)
   - 툴은 주방 이미지(SCENE)와 제품 이미지(PRODUCT)를 합성하여 ADK artifact 'last_image.png'를 저장한다.
3) 최종 출력은 생성한 이미지와, 왜 이 냉장고가 지금 주방 인테리어에 어울리는지 소비자에게 어필을 할 수 있게 설명한다.

카탈로그(JSON):
{json.dumps(BESPOKE_CATALOG, ensure_ascii=False, indent=2)}

제약:
- 모델명/URL/컬러는 반드시 카탈로그 값과 일치해야 한다.
- 툴 호출 없이 이미지를 만들어서는 안 된다(반드시 툴 사용).
- 내부 추론/메모는 숨기고, 최종 JSON만 출력한다.

"""

# 에이전트 정의 (설명 갱신)
Interior_architecture = Agent(
    name="Interior_architecture",
    model="gemini-2.5-flash",
    description="사용자 업로드 이미지를 분석해 카탈로그 JSON에서 최적의 비스포크 냉장고/컬러를 하나 선택하고 이를 gemini-2.5-flash-image 모델로 주방이미지와 합성한다.",
    instruction=image_agent_instruction,
    tools=[generate_edit_image],
)

root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    description="An AI agent designed for image-related tasks, including content analysis, generation, and modification",
    instruction=root_agent_instruction,
    sub_agents=[Interior_architecture]
)
