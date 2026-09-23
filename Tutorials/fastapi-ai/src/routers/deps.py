from fastapi import Depends, HTTPException, Request

from auth import AuthenticatedUser, get_authenticated_user
from database import get_database
from repositories.user_repository import UserRepository
from services.me_service import MeService


async def get_current_user_id(
    user_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
) -> str:
    """
    The user whose resources are being addressed: the `{user_id}` in the path.

    The caller (Clerk identity -> our `users` row, the same mapping /me uses)
    is resolved separately and compared with it. Business-logic seam: today
    only the owner may touch a user's chats, todos and assistant; loosen it
    here (e.g. admins, or users who share something) once those rules exist.
    """
    db = get_database(request)
    me_service = MeService(UserRepository(db))
    caller = await me_service.get_or_create_current_user(current_user)
    if caller["id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this user's resources")
    return user_id


def get_embedder(request: Request):
    """(embed function, model name) — embeddings always come from Workers AI, whichever provider chats."""
    from ai import get_ai
    from config import get_config
    from embeddings import DEFAULT_EMBEDDING_MODEL, embed

    model = get_config(request, "CF_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL) or DEFAULT_EMBEDDING_MODEL

    async def embed_texts(texts: list[str]) -> list[list[float]]:
        # Built on first use, so routes that never embed (todo CRUD without
        # Workers AI credentials) don't fail just for constructing the service.
        return await embed(get_ai(request, "cloudflare"), model, texts)

    return embed_texts, model


def get_todo_search_service(request: Request):
    from repositories.todo_repository import TodoRepository
    from resource_vector_store import ResourceVectorStore
    from services.todo_search_service import TodoSearchService

    db = get_database(request)
    embed_texts, model = get_embedder(request)
    return TodoSearchService(TodoRepository(db), ResourceVectorStore(db, "todo"), embed_texts, model)


async def get_caller(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """The signed-in user as a permissions Caller (our users.id + whether they are a system ADMIN)."""
    from group_permissions import Caller

    db = get_database(request)
    return Caller.from_user_row(await MeService(UserRepository(db)).get_or_create_current_user(current_user))
