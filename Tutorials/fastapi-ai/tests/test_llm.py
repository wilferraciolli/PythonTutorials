"""The httpx chat-completions client that replaced the `openai` package."""
import json

import httpx
import pytest

from ai import GroqAdapter
from llm import OpenAICompatibleLlm

TOOLS = [{"type": "function", "function": {"name": "count_todos", "parameters": {"type": "object"}}}]


def replying(message, status=200, seen=None):
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(status, json={"choices": [{"message": message}]} if status < 400 else {"error": "no"})

    return httpx.MockTransport(handler)


async def test_sends_an_openai_style_request_and_parses_tool_calls():
    seen = []
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "count_todos", "arguments": '{"state": "NEW"}'},
    }
    llm = OpenAICompatibleLlm(
        "key", "https://api.groq.com/openai/v1/", replying({"content": None, "tool_calls": [tool_call]}, seen=seen)
    )

    turn = await llm.complete("model-x", [{"role": "user", "content": "hi"}], TOOLS)

    assert turn == {"content": None, "tool_calls": [{"id": "call_1", "name": "count_todos", "arguments": '{"state": "NEW"}'}]}
    request = seen[0]
    assert str(request.url) == "https://api.groq.com/openai/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer key"
    body = json.loads(request.content)
    assert body["model"] == "model-x" and body["tools"] == TOOLS and body["tool_choice"] == "auto"


async def test_a_plain_answer_has_no_tool_calls():
    llm = OpenAICompatibleLlm("key", "https://x/v1", replying({"content": "You have 2 todos."}))
    assert await llm.complete("m", [], TOOLS) == {"content": "You have 2 todos.", "tool_calls": []}


async def test_errors_are_raised_with_the_status():
    llm = OpenAICompatibleLlm("key", "https://x/v1", replying({}, status=429))
    with pytest.raises(RuntimeError, match="429"):
        await llm.complete("m", [], TOOLS)


async def test_groq_chat_adapter_returns_the_reply_text(monkeypatch):
    import llm as llm_module

    real = llm_module.chat_completion

    async def fake(api_key, base_url, payload, transport=None):
        assert payload == {"model": "m", "messages": [{"role": "user", "content": "hello"}]}
        return await real(api_key, base_url, payload, replying({"content": "Hi there"}))

    monkeypatch.setattr(llm_module, "chat_completion", fake)
    result = await GroqAdapter("key", "https://api.groq.com/openai/v1").run(
        "m", {"messages": [{"role": "user", "content": "hello"}]}
    )
    assert result == {"response": "Hi there"}
