from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ai import get_ai
from embeddings import DEFAULT_EMBEDDING_MODEL, embed
from auth import AuthenticatedUser, get_authenticated_user
from config import get_config
from database import get_database
from models import ChatCreate, ChatMessageCreate, ChatProvider, ChatTitleUpdate
from repositories.chat_repository import ChatRepository
from repositories.user_repository import UserRepository
from services.chat_service import ChatService
from services.me_service import MeService
from services.search_service import DEFAULT_LIMIT, SearchService
from vector_store import DatabaseVectorStore

router = APIRouter(prefix="/users/{user_id}/chats", tags=["chats"])


async def get_current_user_id(
    user_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
) -> str:
    """
    The user whose chats are being addressed: the `{user_id}` in the path.

    The caller (Clerk identity -> our `users` row, the same mapping /me uses)
    is resolved separately and compared with it. Business-logic seam: today
    only the owner may touch their chats; loosen it here (e.g. admins, or
    users who share a chat) once those rules exist.
    """
    db = get_database(request)
    me_service = MeService(UserRepository(db))
    caller = await me_service.get_or_create_current_user(current_user)
    if caller["id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this user's chats")
    return user_id


def _required_config(request: Request, key: str) -> str:
    value = get_config(request, key)
    if not value:
        raise RuntimeError(f"{key} must be configured (see .env.example)")
    return value


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
        get_search_service(request),
    )


def get_search_service(request: Request) -> SearchService:
    db = get_database(request)
    embedding_model = get_config(request, "CF_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL) or DEFAULT_EMBEDDING_MODEL
    # Embeddings always come from Workers AI, whichever provider answers a chat.
    ai = get_ai(request, "cloudflare")

    async def embed_texts(texts: list[str]) -> list[list[float]]:
        return await embed(ai, embedding_model, texts)

    return SearchService(
        ChatRepository(db),
        DatabaseVectorStore(db),
        embed_texts,
        embedding_model,
        ["cloudflare", "groq"],
    )


@router.get("")
async def list_chats(
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    chats = await service.list_chats(user_id)
    return service.build_list_response(user_id, chats)


@router.post("", status_code=201)
async def create_chat(
    payload: ChatCreate,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    chat = await service.create_chat(user_id, payload.provider)
    return service.build_response(chat)


@router.get("/search")
async def search_chats(
    q: str,
    limit: int = DEFAULT_LIMIT,
    user_id: str = Depends(get_current_user_id),
    service: SearchService = Depends(get_search_service),
) -> dict[str, Any]:
    """Find messages in the user's chats by meaning (embeddings) and by keyword, best first."""
    hits = await service.search(user_id, q, limit)
    return service.build_response(user_id, hits)


@router.post("/search/reindex")
async def reindex_chats(
    user_id: str = Depends(get_current_user_id),
    service: SearchService = Depends(get_search_service),
) -> dict[str, Any]:
    """Backfill: embed this user's messages that aren't indexed yet."""
    indexed = await service.reindex_user(user_id)
    return service.build_reindex_response(indexed)


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    chat = await service.get_chat_with_messages(chat_id, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return service.build_response(chat)


@router.post("/{chat_id}/messages", status_code=201)
async def send_message(
    chat_id: str,
    payload: ChatMessageCreate,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    chat = await service.send_message(chat_id, user_id, payload.content)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return service.build_response(chat)


@router.put("/{chat_id}")
async def update_chat_title(
    chat_id: str,
    payload: ChatTitleUpdate,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    chat = await service.update_title(chat_id, user_id, payload.title)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return service.build_response(chat)


@router.delete("/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
) -> Response:
    deleted = await service.delete_chat(chat_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
    return Response(status_code=204)
