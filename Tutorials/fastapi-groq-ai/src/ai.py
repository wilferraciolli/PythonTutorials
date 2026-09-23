from typing import Any, Protocol

from fastapi import Request

from config import get_config
from models import ChatProvider


class AI(Protocol):
    async def run(self, model: str, inputs: dict[str, Any]) -> dict[str, Any]: ...


class GroqAdapter:
    """Groq's OpenAI-compatible Responses API adapter."""

    def __init__(self, api_key: str, base_url: str) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def run(self, model: str, inputs: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.responses.create(
            model=model,
            input=inputs["messages"],
        )
        return {"response": response.output_text}


def get_ai(request: Request, provider: ChatProvider = "groq") -> AI:
    """Groq is the only provider in this project; kept as a factory so ChatService is unchanged."""
    api_key = get_config(request, "GROQ_API_KEY")
    base_url = get_config(request, "GROQ_BASE_URL")
    if not api_key or not base_url:
        raise RuntimeError("Groq requires GROQ_API_KEY and GROQ_BASE_URL")
    return GroqAdapter(api_key, base_url)
