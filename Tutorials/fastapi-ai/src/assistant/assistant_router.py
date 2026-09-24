from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from assistant.tools.chat_tools import build_chat_tools
from assistant.tools.date_tools import build_date_tools
from assistant.tools.social_tools import build_social_tools
from assistant.tools.todo_tools import build_todo_tools, utc_now
from core.config.config import get_config
from core.config.database import get_database
from core.security.authorization import Caller
from core.ai.llm import OpenAICompatibleLlm
from assistant.schemas import AssistantAsk
from groups.social_query_repository import SocialQueryRepository
from todos.todo_repository import TodoRepository
from chats.chat_router import get_search_service
from groups.posts.post_router import get_post_search_service
from todos.todo_router import get_todo_search_service
from core.security.authorization import get_caller, require_owner
from assistant.assistant_service import AssistantService

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
    user_id: str = Depends(require_owner),
    caller: Caller = Depends(get_caller),
) -> dict[str, Any]:
    """Ask a question about your data (todos, chats) and the groups you can see, in plain English."""
    # require_owner already checked the path user is the caller.
    service = get_assistant_service(request, payload.provider, caller)
    answer = await service.ask(user_id, payload.question)
    return service.build_response(answer)
