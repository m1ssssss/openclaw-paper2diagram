import re
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from app.clients.banana_client import BananaClient
from app.clients.gemini_client import GeminiClient
from app.config import get_settings
from app.skills.banana_renderer import BananaRendererSkill
from app.skills.logic_distiller import LogicDistillerSkill
from app.skills.pdf_reader import PDFReaderSkill
from app.skills.prompt_translator import PromptTranslatorSkill
from app.skills.section_extractor import SectionExtractorSkill


class PaperToDiagramPipeline:
    def __init__(self) -> None:
        settings = get_settings()
        self.enable_banana = settings.enable_banana and bool(settings.banana_api_key)
        self._gemini_read_timeout_s = settings.gemini_timeout_seconds
        self.pdf_reader = PDFReaderSkill()
        self.section_extractor = SectionExtractorSkill()
        self.logic_distiller = LogicDistillerSkill(
            gemini_client=GeminiClient(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                base_url=settings.gemini_base_url,
                timeout_seconds=settings.gemini_timeout_seconds,
                connect_timeout_seconds=settings.gemini_connect_timeout_seconds,
                use_query_key=settings.gemini_use_query_key,
            )
        )
        self.prompt_translator = PromptTranslatorSkill()
        self.renderer = BananaRendererSkill(
            banana_client=BananaClient(
                api_key=settings.banana_api_key,
                base_url=settings.banana_base_url,
                model=settings.banana_model,
                timeout_seconds=settings.banana_timeout_seconds,
            )
        )

    def _save_image_locally(self, image_url: str, pdf_path: str) -> Optional[str]:
        if not image_url or not image_url.startswith("http"):
            return None

        project_root = Path(__file__).resolve().parents[2]
        output_dir = project_root / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_name = Path(pdf_path).stem
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", pdf_name).strip("_") or "paper"
        target_path = output_dir / f"{safe_name}.jpg"

        with httpx.Client(timeout=60) as client:
            resp = client.get(image_url)
            resp.raise_for_status()
            target_path.write_bytes(resp.content)

        return str(target_path)

    def _save_image_locally_named(self, image_url: str, pdf_path: str, suffix: str) -> Optional[str]:
        if not image_url or not image_url.startswith("http"):
            return None
        project_root = Path(__file__).resolve().parents[2]
        output_dir = project_root / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_name = Path(pdf_path).stem
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", pdf_name).strip("_") or "paper"
        safe_suffix = re.sub(r"[^A-Za-z0-9._-]+", "_", suffix).strip("_") or "img"
        target_path = output_dir / f"{safe_name}__{safe_suffix}.jpg"

        with httpx.Client(timeout=60) as client:
            resp = client.get(image_url)
            resp.raise_for_status()
            target_path.write_bytes(resp.content)
        return str(target_path)

    def run(self, pdf_path: str, max_pages: int = 30) -> Dict[str, Any]:
        print("[pipeline] step1: pdf_reader", flush=True)
        step1 = self.pdf_reader.run({"source": pdf_path, "max_pages": max_pages})
        if step1.status != "ok":
            return {"status": "error", "stage": "pdf_reader", "error": step1.error}

        print("[pipeline] step2: section_extractor", flush=True)
        step2 = self.section_extractor.run({"raw_text": step1.data["raw_text"]})
        if step2.status != "ok":
            return {"status": "error", "stage": "section_extractor", "error": step2.error}

        first_section = step2.data["sections"][0]["text"]
        print(
            f"[pipeline] step3: logic_distiller (Gemini request, read timeout {self._gemini_read_timeout_s}s)",
            flush=True,
        )
        step3 = self.logic_distiller.run({"section_text": first_section})
        if step3.status != "ok":
            return {"status": "error", "stage": "logic_distiller", "error": step3.error}

        print("[pipeline] step4: prompt_translator", flush=True)
        step4 = self.prompt_translator.run({"logic_json_raw": step3.data["logic_json_raw"]})
        if step4.status != "ok":
            return {"status": "error", "stage": "prompt_translator", "error": step4.error}

        if not self.enable_banana:
            print("[pipeline] step5: banana_renderer skipped (ENABLE_BANANA=false or missing key)", flush=True)
            return {
                "status": "partial_ok",
                "stage": "banana_renderer",
                "error": "banana rendering skipped by config",
                "paper_analysis": {
                    "method_or_architecture_excerpt": first_section[:2000],
                    "logic_json_raw": step3.data["logic_json_raw"],
                },
                "final_prompt": step4.data,
            }

        prompts = step4.data.get("prompts", [])
        if not prompts:
            return {"status": "error", "stage": "prompt_translator", "error": "No prompts generated"}

        print(f"[pipeline] step5: banana_renderer (image requests x{len(prompts)})", flush=True)
        render_results = []
        for i, p in enumerate(prompts, start=1):
            print(f"[pipeline]  - rendering {i}/{len(prompts)}: {p.get('id', 'figure')}", flush=True)
            step5 = self.renderer.run(p)
            if step5.status != "ok":
                render_results.append(
                    {
                        "id": p.get("id"),
                        "title": p.get("title"),
                        "status": "error",
                        "error": step5.error,
                        "prompt": p,
                    }
                )
                continue

            local_image_path: Optional[str] = None
            local_save_error: Optional[str] = None
            try:
                local_image_path = self._save_image_locally_named(
                    image_url=step5.data.get("image_url", ""),
                    pdf_path=pdf_path,
                    suffix=p.get("id", f"fig{i}"),
                )
            except Exception as e:
                local_save_error = str(e)

            render_result = dict(step5.data)
            if local_image_path:
                render_result["local_image_path"] = local_image_path
            if local_save_error:
                render_result["local_save_error"] = local_save_error
            render_result["id"] = p.get("id")
            render_result["title"] = p.get("title")
            render_results.append(render_result)

        return {
            "status": "ok",
            "paper_analysis": {
                "method_or_architecture_excerpt": first_section[:2000],
                "logic_json_raw": step3.data["logic_json_raw"],
            },
            "final_prompt": step4.data,
            "render_results": render_results,
        }
