from typing import Any, Dict
from app.clients.banana_client import BananaClient
from app.skills.base import BaseSkill
from app.schemas.common import SkillResult


class BananaRendererSkill(BaseSkill):
    name = "banana_renderer"

    def __init__(self, banana_client: BananaClient) -> None:
        self.banana_client = banana_client

    def run(self, payload: Dict[str, Any]) -> SkillResult:
        try:
            result = self.banana_client.generate_image(
                prompt=payload["prompt_en"],
                negative_prompt=payload.get("negative_prompt"),
                size=payload.get("render_params", {}).get("size", "1536x1024"),
            )
            return SkillResult(status="ok", data=result)
        except Exception as e:
            return SkillResult(status="error", error=str(e))
