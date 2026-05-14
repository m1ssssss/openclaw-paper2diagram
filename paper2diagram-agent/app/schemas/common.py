from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SkillResult(BaseModel):
    status: str = Field(..., description="ok | error")
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
