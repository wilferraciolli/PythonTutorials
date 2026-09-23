from typing import Any, Protocol

from fastapi import Request

from config import get_config
from models import ChatProvider


class AI(Protocol):
    async def run(self, model: str, inputs: dict[str, Any]) -> dict[str, Any]: ...


class AiBindingAdapter:
    """Cloudflare Worker native binding adapter for env.AI."""

    def __init__(self, ai: Any) -> None:
        self._ai = ai

    async def run(self, model: str, inputs: dict[str, Any]) -> dict[str, Any]:
        result = await self._ai.run(model, inputs)
        return result if isinstance(result, dict) else dict(result)


class AiHttpAdapter:
    """
    Cloudflare Workers AI over the REST API.

    Prefer this over AiBindingAdapter for portability: it works the same from
    local uvicorn/Docker, another host, or a Cloudflare Worker, the same way
    D1HttpDatabase lets any of those runtimes reach D1. Needs CF_ACCOUNT_ID
    and CF_AI_API_TOKEN (a Cloudflare API token scoped to Workers AI).
    """

    def __init__(self, account_id: str, api_token: str) -> None:
        self._base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run"
        self._headers = {"Authorization": f"Bearer {api_token}"}

    async def run(self, model: str, inputs: dict[str, Any]) -> dict[str, Any]:
        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self._base_url}/{model}",
                headers=self._headers,
                json=inputs,
            )
            response.raise_for_status()

        body = response.json()
        if not body.get("success"):
            raise RuntimeError(f"Workers AI request failed: {body.get('errors')}")

        return body["result"]


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


def get_ai(request: Request, provider: ChatProvider = "cloudflare") -> AI:
    """
    Select the Workers AI backend for the current runtime.

    Modes:
    - http: REST API call to Cloudflare — portable, works everywhere
    - binding: Cloudflare Workers env.AI binding — no network hop, Workers-only

    If AI_MODE is omitted and env.AI exists, binding is used (same
    "prefer the native binding inside Workers" rule database.py follows for
    D1) — otherwise http, so local uvicorn/Docker and any non-Worker host
    work without extra configuration beyond an API token.
    """
    if provider == "groq":
        api_key = get_config(request, "GROQ_API_KEY")
        base_url = get_config(request, "GROQ_BASE_URL")
        if not api_key or not base_url:
            raise RuntimeError("Groq requires GROQ_API_KEY and GROQ_BASE_URL")
        return GroqAdapter(api_key, base_url)

    env = request.scope.get("env")
    has_ai_binding = env is not None and hasattr(env, "AI")
    mode = get_config(request, "AI_MODE", "binding" if has_ai_binding else "http")

    if mode == "binding":
        if not has_ai_binding:
            raise RuntimeError("AI_MODE='binding' requires a Cloudflare Workers env.AI binding")
        return AiBindingAdapter(env.AI)

    if mode == "http":
        account_id = get_config(request, "CF_ACCOUNT_ID")
        api_token = get_config(request, "CF_AI_API_TOKEN")
        if not account_id or not api_token:
            raise RuntimeError("AI_MODE='http' requires CF_ACCOUNT_ID and CF_AI_API_TOKEN")
        return AiHttpAdapter(account_id, api_token)

    raise RuntimeError(f"unknown AI_MODE: {mode!r}")
