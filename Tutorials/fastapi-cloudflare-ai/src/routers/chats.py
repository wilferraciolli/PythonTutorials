from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ai import get_ai
from auth import AuthenticatedUser, get_authenticated_user
from config import get_config
from database import get_database
from models import ChatMessageCreate
from repositories.chat_repository import ChatRepository
from repositories.user_repository import UserRepository
from services.chat_service import DEFAULT_MODEL, ChatService
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


def get_chat_service(request: Request) -> ChatService:
    db = get_database(request)
    model = get_config(request, "AI_CHAT_MODEL", DEFAULT_MODEL)
    return ChatService(ChatRepository(db), get_ai(request), model)


@router.get("")
async def list_chats(
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    chats = await service.list_chats(user_id)
    return service.build_list_response(chats)


@router.post("", status_code=201)
async def create_chat(
    user_id: str = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
) -> dict[str, Any]:
    chat = await service.create_chat(user_id)
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
