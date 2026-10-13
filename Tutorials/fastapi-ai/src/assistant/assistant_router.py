from fastapi import APIRouter, Depends, Request
from wiltech_labs_ai import get_tool_llm
from wiltech_labs_auth import Caller, get_caller, require_owner
from wiltech_labs_core import get_database

from assistant.assistant_service import AssistantService
from assistant.schemas import AssistantAnswerResponse, AssistantAskRequest
from assistant.tools.chat_tools import build_chat_tools
from assistant.tools.date_tools import build_date_tools
from assistant.tools.social_tools import build_social_tools
from assistant.tools.todo_tools import build_todo_tools, utc_now
from chats.chat_router import get_chat_search_service
from groups.posts.post_router import get_post_search_service
from groups.social_query_repository import SocialQueryRepository
from todos.todo_repository import TodoRepository
from todos.todo_router import get_todo_search_service

# Personal resource: only the user in the path may ask about their data (require_owner, 403).
router = APIRouter(prefix="/users/{user_id}/assistant", tags=["assistant"])


def get_assistant_service(request: Request, provider: str, caller: Caller) -> AssistantService:
    # Groq or Workers AI over its OpenAI-compatible endpoint (needs the REST
    # credentials, not the binding). Missing settings answer 503 naming the key.
    llm, model = get_tool_llm(request, provider)

    db = get_database(request)
    tools = [
        *build_todo_tools(TodoRepository(db), search=get_todo_search_service(request)),
        *build_date_tools(utc_now),
        *build_chat_tools(get_chat_search_service(request)),
        # Shared data: scoped by the caller's group visibility, not just their id.
        *build_social_tools(caller, SocialQueryRepository(db), get_post_search_service(request)),
    ]
    return AssistantService(llm, model, provider, tools)


@router.post("/ask")
async def ask(
    body: AssistantAskRequest,
    request: Request,
    user_id: str = Depends(require_owner),
    caller: Caller = Depends(get_caller),
) -> AssistantAnswerResponse:
    """Ask a question about your data (todos, chats) and the groups you can see, in plain English."""
    service = get_assistant_service(request, body.provider, caller)
    return service.build_response(await service.ask(user_id, body.question))
