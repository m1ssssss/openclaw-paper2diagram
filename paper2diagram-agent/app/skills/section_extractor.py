import re
from typing import Any, Dict, List, Tuple
from app.skills.base import BaseSkill
from app.schemas.common import SkillResult


KEYWORDS = [
    "method",
    "methods",
    "methodology",
    "approach",
    "architecture",
    "proposed network",
    "model",
    "framework",
    "backbone",
    "our method",
    "our approach",
    "implementation details",
    "network",
    "design",
]


class SectionExtractorSkill(BaseSkill):
    name = "section_extractor"

    def _normalize_text(self, text: str) -> str:
        # Handle PDF line-break artifacts that often split headings/words.
        text = text.replace("-\n", "")
        text = text.replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _get_candidate_spans(self, text: str) -> List[Tuple[int, int, str]]:
        spans: List[Tuple[int, int, str]] = []
        pattern = r"(?i)\\b(" + "|".join(re.escape(k) for k in KEYWORDS) + r")\\b"
        for m in re.finditer(pattern, text):
            start = max(0, m.start() - 500)
            end = min(len(text), m.start() + 8000)
            spans.append((start, end, m.group(0)))
        return spans

    def _fallback_spans(self, text: str) -> List[Tuple[int, int, str]]:
        # Robust fallback when no explicit Method/Architecture heading is found.
        n = len(text)
        if n == 0:
            return []
        early_end = min(n, 12000)
        mid_start = min(n, max(0, n // 3))
        mid_end = min(n, mid_start + 12000)
        return [
            (0, early_end, "fallback_early_body"),
            (mid_start, mid_end, "fallback_middle_body"),
        ]

    def run(self, payload: Dict[str, Any]) -> SkillResult:
        try:
            text = self._normalize_text(payload["raw_text"])
            spans = self._get_candidate_spans(text)
            if not spans:
                spans = self._fallback_spans(text)
            if not spans:
                return SkillResult(status="error", error="No usable text found for section extraction")

            unique_sections = []
            seen = set()
            for start, end, hit in spans[:6]:
                chunk = text[start:end].strip()
                key = (start, end)
                if key in seen:
                    continue
                seen.add(key)
                unique_sections.append({
                    "name": "method_or_architecture_candidate",
                    "keyword_hit": hit,
                    "start": start,
                    "end": end,
                    "text": chunk,
                })

            return SkillResult(status="ok", data={"sections": unique_sections})
        except Exception as e:
            return SkillResult(status="error", error=str(e))
