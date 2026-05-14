from typing import Any, Callable, Dict

from app.orchestrator.pipeline import PaperToDiagramPipeline


class SkillRegistry:
    """Framework-agnostic registry for exposing local skills to OpenClaw."""

    def __init__(self) -> None:
        self.pipeline = PaperToDiagramPipeline()
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "pdf_reader": self._pdf_reader,
            "section_extractor": self._section_extractor,
            "logic_distiller": self._logic_distiller,
            "prompt_translator": self._prompt_translator,
            "banana_renderer": self._banana_renderer,
            "paper_to_diagram": self._paper_to_diagram,
        }

    def _pdf_reader(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = self.pipeline.pdf_reader.run(payload)
        return result.model_dump()

    def _section_extractor(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = self.pipeline.section_extractor.run(payload)
        return result.model_dump()

    def _logic_distiller(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = self.pipeline.logic_distiller.run(payload)
        return result.model_dump()

    def _prompt_translator(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = self.pipeline.prompt_translator.run(payload)
        return result.model_dump()

    def _banana_renderer(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = self.pipeline.renderer.run(payload)
        return result.model_dump()

    def _paper_to_diagram(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pdf_path = payload["pdf_path"]
        max_pages = int(payload.get("max_pages", 30))
        return self.pipeline.run(pdf_path=pdf_path, max_pages=max_pages)

    def call(self, skill_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if skill_name not in self.handlers:
            return {
                "status": "error",
                "error": f"Unknown skill: {skill_name}",
                "available_skills": sorted(self.handlers.keys()),
            }
        return self.handlers[skill_name](payload)
