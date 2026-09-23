from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from assistant.chat_tools import build_chat_tools
from assistant.date_tools import build_date_tools
from assistant.social_tools import build_social_tools
from assistant.todo_tools import build_todo_tools, utc_now
from config import get_config
from database import get_database
from group_permissions import Caller
from llm import OpenAICompatibleLlm
from models import AssistantAsk
from repositories.social_query_repository import SocialQueryRepository
from repositories.todo_repository import TodoRepository
from routers.chats import get_search_service
from routers.deps import get_caller, get_current_user_id, get_post_search_service, get_todo_search_service
from services.assistant_service import AssistantService

router = APIRouter(prefix="/users/{user_id}/assistant", tags=["assistant"])


def _required(request: Request, key: str) -> str:
    value = get_config(request, key)
    if not value:
        raise HTTPException(status_code=503, detail=f"{key} must be configured (see .env.example)")
    return value


def get_assistant_service(request: Request, provider: str, caller: Caller) -> AssistantService:
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
        *build_todo_tools(TodoRepository(db), search=get_todo_search_service(request)),
        *build_date_tools(utc_now),
        *build_chat_tools(get_search_service(request)),
        # Shared data: scoped by the caller's group visibility, not just their id.
        *build_social_tools(caller, SocialQueryRepository(db), get_post_search_service(request)),
    ]
    return AssistantService(llm, model, provider, tools)


@router.post("/ask")
async def ask(
    payload: AssistantAsk,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    caller: Caller = Depends(get_caller),
) -> dict[str, Any]:
    """Ask a question about your data (todos, chats) and the groups you can see, in plain English."""
    # get_current_user_id already checked the path user is the caller.
    service = get_assistant_service(request, payload.provider, caller)
    answer = await service.ask(user_id, payload.question)
    return service.build_response(answer)
