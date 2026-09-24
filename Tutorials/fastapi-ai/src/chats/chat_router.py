from fastapi import APIRouter, Depends, HTTPException, Request, Response

from chats.chat_repository import ChatRepository
from chats.chat_search_service import DEFAULT_LIMIT, ChatSearchService
from chats.chat_service import ChatService
from chats.schemas import (
    ChatCreateRequest,
    ChatListResponse,
    ChatMessageCreateRequest,
    ChatReindexResponse,
    ChatResponse,
    ChatSearchResponse,
    ChatTitleUpdateRequest,
)
from core.ai.ai import ChatProvider, get_ai
from core.ai.embeddings import get_embedder
from core.ai.vector_store import DatabaseVectorStore
from core.config.config import get_config
from core.config.database import get_database
from core.security.authorization import require_owner

# Personal resource: only the user in the path may use it (require_owner, 403).
router = APIRouter(prefix="/users/{user_id}/chats", tags=["chats"])


def _required_config(request: Request, key: str) -> str:
    value = get_config(request, key)
    if not value:
        raise RuntimeError(f"{key} must be configured (see .env.example)")
    return value


def get_chat_search_service(request: Request) -> ChatSearchService:
    db = get_database(request)
    embed_texts, embedding_model = get_embedder(request)

    return ChatSearchService(
        ChatRepository(db),
        DatabaseVectorStore(db),
        embed_texts,
        embedding_model,
        ["cloudflare", "groq"],
    )


def get_chat_service(request: Request) -> ChatService:
    db = get_database(request)
    models: dict[ChatProvider, str] = {
        "cloudflare": _required_config(request, "CF_AI_MODEL"),
        "groq": _required_config(request, "GROQ_MODEL"),
    }
    return ChatService(
        ChatRepository(db),
        lambda provider: get_ai(request, provider),
        models,
        get_chat_search_service(request),
    )


@router.get("")
async def list_chats(
    user_id: str = Depends(require_owner),
    service: ChatService = Depends(get_chat_service),
) -> ChatListResponse:
    return service.build_list_response(user_id, await service.list_chats(user_id))


@router.post("", status_code=201)
async def create_chat(
    request: ChatCreateRequest,
    user_id: str = Depends(require_owner),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    return service.build_response(await service.create_chat(user_id, request.provider))


@router.get("/search")
async def search_chats(
    q: str,
    limit: int = DEFAULT_LIMIT,
    user_id: str = Depends(require_owner),
    service: ChatSearchService = Depends(get_chat_search_service),
) -> ChatSearchResponse:
    """Find messages in the user's chats by meaning (embeddings) and by keyword, best first."""
    return service.build_response(user_id, await service.search(user_id, q, limit))


@router.post("/search/reindex")
async def reindex_chats(
    user_id: str = Depends(require_owner),
    service: ChatSearchService = Depends(get_chat_search_service),
) -> ChatReindexResponse:
    """Backfill: embed this user's messages that aren't indexed yet."""
    return service.build_reindex_response(await service.reindex_user(user_id))


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str,
    user_id: str = Depends(require_owner),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    chat = await service.get_chat_with_messages(chat_id, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return service.build_response(chat)


@router.post("/{chat_id}/messages", status_code=201)
async def send_message(
    chat_id: str,
    request: ChatMessageCreateRequest,
    user_id: str = Depends(require_owner),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    chat = await service.send_message(chat_id, user_id, request.content)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return service.build_response(chat)


@router.put("/{chat_id}")
async def update_chat_title(
    chat_id: str,
    request: ChatTitleUpdateRequest,
    user_id: str = Depends(require_owner),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    chat = await service.update_title(chat_id, user_id, request.title)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return service.build_response(chat)


@router.delete("/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: str,
    user_id: str = Depends(require_owner),
    service: ChatService = Depends(get_chat_service),
) -> Response:
    if not await service.delete_chat(chat_id, user_id):
        raise HTTPException(status_code=404, detail="Chat not found")
    return Response(status_code=204)
