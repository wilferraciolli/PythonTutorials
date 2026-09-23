from typing import Any, Dict, List, Optional, Protocol

import httpx

TIMEOUT_SECONDS = 60


class ToolLlm(Protocol):
    """
    A chat model that can ask for tools to be run.

    `complete` returns the assistant turn as {"content": str | None,
    "tool_calls": [{"id", "name", "arguments" (a JSON string)}]}.
    """

    async def complete(
        self, model: str, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]: ...


async def chat_completion(
    api_key: str,
    base_url: str,
    payload: Dict[str, Any],
    transport: Optional[httpx.AsyncBaseTransport] = None,
) -> Dict[str, Any]:
    """
    POST {base_url}/chat/completions: the OpenAI-compatible API that Groq and
    Workers AI (/ai/v1) both speak. Plain httpx instead of the `openai`
    package, which is heavy to load in a Python Worker (about 1.4 s of CPU on
    a cold start) for what is one JSON request. Returns the first choice's
    message.
    """
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, transport=transport) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
    if response.status_code >= 400:
        raise RuntimeError(f"chat completion failed ({response.status_code}): {response.text[:300]}")
    choices = response.json().get("choices") or []
    if not choices:
        raise RuntimeError(f"chat completion returned no choices: {response.text[:300]}")
    return choices[0].get("message") or {}


class OpenAICompatibleLlm:
    """
    Chat-completions with tool calling against any OpenAI-compatible endpoint:
    Groq (https://api.groq.com/openai/v1) and Workers AI
    (https://api.cloudflare.com/client/v4/accounts/{id}/ai/v1) both speak it,
    so one client serves both providers.
    """

    def __init__(self, api_key: str, base_url: str, transport: Optional[httpx.AsyncBaseTransport] = None) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._transport = transport  # tests pass an httpx.MockTransport

    async def complete(
        self, model: str, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        message = await chat_completion(
            self._api_key,
            self._base_url,
            {"model": model, "messages": messages, "tools": tools, "tool_choice": "auto"},
            self._transport,
        )
        return {
            "content": message.get("content"),
            "tool_calls": [
                {
                    "id": call.get("id"),
                    "name": (call.get("function") or {}).get("name"),
                    "arguments": (call.get("function") or {}).get("arguments") or "{}",
                }
                for call in (message.get("tool_calls") or [])
            ],
        }
