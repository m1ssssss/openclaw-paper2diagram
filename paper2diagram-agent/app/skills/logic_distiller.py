from typing import Any, Dict
from app.clients.gemini_client import GeminiClient
from app.skills.base import BaseSkill
from app.schemas.common import SkillResult


DISTILL_PROMPT = """
You are extracting architecture facts from a paper section.
Return ONLY JSON with this schema:
{
  "input": "...",
  "encoder": "...",
  "fusion_or_attention": "...",
  "decoder": "...",
  "losses": "...",
  "training_tricks": "...",
  "pipeline_flow": ["step1", "step2", "step3"]
}
Rules:
- Do not add markdown.
- If missing, set field to "Not specified".
"""


class LogicDistillerSkill(BaseSkill):
    name = "logic_distiller"

    def __init__(self, gemini_client: GeminiClient) -> None:
        self.gemini_client = gemini_client

    def run(self, payload: Dict[str, Any]) -> SkillResult:
        try:
            section_text = payload["section_text"]
            # Keep request payload bounded to reduce LLM latency.
            section_text = section_text[:8000]
            response = self.gemini_client.generate(
                prompt=f"{DISTILL_PROMPT}\n\nPaper section:\n{section_text}",
                temperature=0.1,
            )
            return SkillResult(status="ok", data={"logic_json_raw": response})
        except Exception as e:
            return SkillResult(status="error", error=str(e))
