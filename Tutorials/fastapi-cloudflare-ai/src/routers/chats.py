from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ai import get_ai
from auth import AuthenticatedUser, get_authenticated_user
from config import get_config
from database import get_database
from models import ChatCreate, ChatMessageCreate, ChatProvider, ChatTitleUpdate
from repositories.chat_repository import ChatRepository
from repositories.user_repository import UserRepository
from services.chat_service import ChatService
from services.me_service import MeService

router = APIRouter(prefix="/chats", tags=["chats"])


async def get_current_user_id(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
) -> str:
    # Chats belong to our own `users` row, not the Clerk identity directly —
    # same identity-to-row mapping /me uses (me_service.py), reused here so
    # a chat's user_id is the same id /me and /users/{id} already expose.
    db = get_database(request)
    me_service = MeService(UserRepository(db))
    user_row = await me_service.get_or_create_current_user(current_user)
    return user_row["id"]


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
    )


@router.get("")
async def list_chats(
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    chats = await service.list_chats(user_id)
    return service.build_list_response(chats)


@router.post("", status_code=201)
async def create_chat(
    payload: ChatCreate,
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    chat = await service.create_chat(user_id, payload.provider)
    return service.build_response(chat)


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
