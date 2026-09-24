from typing import Any, Dict, Literal

from pydantic import BaseModel, Field

from core.common.api_response import ApiResponse
from core.common.base_dto import NoMetadata


# --- Request: what the client sends -----------------------------------------

class AssistantAskRequest(BaseModel):
    """Body of `POST /users/{user_id}/assistant/ask`."""
    question: str = Field(min_length=1, max_length=1000)
    provider: Literal["groq", "cloudflare"] = "groq"


# --- DTO: what the application service returns ------------------------------

class ToolCallDTO(BaseModel):
    """One tool the assistant ran to answer, kept so the UI can show its working."""
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Any = None


class AssistantAnswerDTO(BaseModel):
    """The assistant's answer, and the tools it used to get there."""
    question: str
    answer: str
    provider: str
    model: str
    toolCalls: list[ToolCallDTO] = Field(default_factory=list)


# --- Response: the envelope the service builds ------------------------------

AssistantAnswerResponse = ApiResponse[AssistantAnswerDTO, NoMetadata]
