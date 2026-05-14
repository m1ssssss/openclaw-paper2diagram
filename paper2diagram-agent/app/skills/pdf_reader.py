from typing import Any, Dict
from pypdf import PdfReader
from app.skills.base import BaseSkill
from app.schemas.common import SkillResult


class PDFReaderSkill(BaseSkill):
    name = "pdf_reader"

    def run(self, payload: Dict[str, Any]) -> SkillResult:
        try:
            source = payload["source"]
            max_pages = int(payload.get("max_pages", 30))

            reader = PdfReader(source)
            page_texts = []
            for page in reader.pages[:max_pages]:
                page_texts.append(page.extract_text() or "")

            raw_text = "\n".join(page_texts).strip()
            if not raw_text:
                return SkillResult(status="error", error="No extractable text found. OCR may be needed.")

            return SkillResult(
                status="ok",
                data={
                    "raw_text": raw_text,
                    "page_count": len(page_texts),
                },
            )
        except Exception as e:
            return SkillResult(status="error", error=str(e))
