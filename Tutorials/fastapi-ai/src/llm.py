from typing import Any, Dict, List, Protocol


class ToolLlm(Protocol):
    """
    A chat model that can ask for tools to be run.

    `complete` returns the assistant turn as {"content": str | None,
    "tool_calls": [{"id", "name", "arguments" (a JSON string)}]}.
    """

    async def complete(
        self, model: str, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]: ...


class OpenAICompatibleLlm:
    """
    Chat-completions with tool calling against any OpenAI-compatible endpoint:
    Groq (https://api.groq.com/openai/v1) and Workers AI
    (https://api.cloudflare.com/client/v4/accounts/{id}/ai/v1) both speak it,
    so one client serves both providers.
    """

    def __init__(self, api_key: str, base_url: str) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def complete(
        self, model: str, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        response = await self._client.chat.completions.create(
            model=model, messages=messages, tools=tools, tool_choice="auto"
        )
        message = response.choices[0].message
        return {
            "content": message.content,
            "tool_calls": [
                {"id": call.id, "name": call.function.name, "arguments": call.function.arguments}
                for call in (message.tool_calls or [])
            ],
        }
