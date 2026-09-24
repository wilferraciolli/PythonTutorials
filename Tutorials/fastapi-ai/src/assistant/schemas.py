from typing import Any, Dict, Literal

from pydantic import BaseModel, Field


class AssistantAsk(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    provider: Literal["groq", "cloudflare"] = "groq"


class ToolCallTrace(BaseModel):
    """One tool the assistant ran to answer, kept so the UI can show its working."""
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Any = None


class AssistantAnswer(BaseModel):
    question: str
    answer: str
    provider: str
    model: str
    toolCalls: list[ToolCallTrace] = Field(default_factory=list)
