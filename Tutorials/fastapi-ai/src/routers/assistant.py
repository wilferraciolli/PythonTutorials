from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from assistant.chat_tools import build_chat_tools
from assistant.todo_tools import build_todo_tools
from config import get_config
from database import get_database
from llm import OpenAICompatibleLlm
from models import AssistantAsk
from repositories.todo_repository import TodoRepository
from routers.chats import get_current_user_id, get_search_service
from services.assistant_service import AssistantService

router = APIRouter(prefix="/users/{user_id}/assistant", tags=["assistant"])


def _required(request: Request, key: str) -> str:
    value = get_config(request, key)
    if not value:
        raise HTTPException(status_code=503, detail=f"{key} must be configured (see .env.example)")
    return value


def get_assistant_service(request: Request, provider: str) -> AssistantService:
    if provider == "groq":
        llm = OpenAICompatibleLlm(_required(request, "GROQ_API_KEY"), _required(request, "GROQ_BASE_URL"))
        model = _required(request, "GROQ_MODEL")
    else:
        # Workers AI over its OpenAI-compatible endpoint (needs the REST credentials, not the binding).
        account_id = _required(request, "CF_AI_ACCOUNT_ID")
        llm = OpenAICompatibleLlm(
            _required(request, "CF_AI_API_TOKEN"),
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1",
        )
        model = _required(request, "CF_AI_MODEL")

    db = get_database(request)
    tools = [
        *build_todo_tools(TodoRepository(db)),
        *build_chat_tools(get_search_service(request)),
    ]
    return AssistantService(llm, model, provider, tools)


@router.post("/ask")
async def ask(
    payload: AssistantAsk,
    request: Request,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Ask a question about the user's own data (todos, chat history, ...) in plain English."""
    service = get_assistant_service(request, payload.provider)
    answer = await service.ask(user_id, payload.question)
    return service.build_response(answer)
