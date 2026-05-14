from abc import ABC, abstractmethod
from typing import Any, Dict
from app.schemas.common import SkillResult


class BaseSkill(ABC):
    name: str = "base_skill"

    @abstractmethod
    def run(self, payload: Dict[str, Any]) -> SkillResult:
        raise NotImplementedError
