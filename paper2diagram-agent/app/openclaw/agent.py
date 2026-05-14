import json
from typing import Any, Dict

from app.openclaw.skill_registry import SkillRegistry


class OpenClawAdapter:
    """
    Adapter that wires local skills into OpenClaw runtime if available.

    This avoids locking to a single OpenClaw SDK API shape.
    You can keep this file and only adjust `_attach_to_openclaw_runtime` based on
    your installed OpenClaw version.
    """

    def __init__(self) -> None:
        self.registry = SkillRegistry()

    def run_local(self, request: Dict[str, Any]) -> Dict[str, Any]:
        skill_name = request.get("skill", "paper_to_diagram")
        payload = request.get("payload", {})
        return self.registry.call(skill_name, payload)

    def _attach_to_openclaw_runtime(self) -> Any:
        try:
            import openclaw  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "OpenClaw SDK is not installed. Install your OpenClaw package first, "
                "then map this adapter to your SDK runtime API."
            ) from exc

        # Generic runtime object placeholder. Replace with actual OpenClaw runtime
        # registration API based on your installed version.
        return openclaw

    def serve_with_openclaw(self) -> None:
        runtime = self._attach_to_openclaw_runtime()
        print("OpenClaw runtime imported:", runtime.__name__)
        print("Registered skills:", json.dumps(sorted(self.registry.handlers.keys()), ensure_ascii=False))
        print("Next step: bind `self.registry.call` to your OpenClaw tool registration API.")
