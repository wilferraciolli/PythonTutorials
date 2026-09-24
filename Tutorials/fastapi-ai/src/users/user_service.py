from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from core.common.api_response import API_PREFIX
from core.common.base_dto import FieldMetadata, Link
from core.security.authorization import Caller
from core.security.roles import UserRole, role_options
from groups.group_repository import GroupRepository
from groups.posts.post_stats_repository import PostStatsRepository
from users.constants import (
    LINK_CREATE_USER,
    LINK_DELETE_USER,
    LINK_SEARCH_USERS,
    LINK_SELF,
    LINK_UPDATE_USER,
    LINK_USER_TEMPLATE,
    USER_DATA_NAME,
    USERS_DATA_NAME,
)
from users.exceptions import SelfLockoutError
from users.models import UserModel
from users.schemas import (
    UserCreateRequest,
    UserDTO,
    UserListResponse,
    UserMetadata,
    UserResponse,
    UserTemplateMetadata,
    UserTemplateResponse,
    UserUpdateRequest,
)
from users.user_repository import UserRepository


class UserService:
    """
    Application service for users.

    Owns business logic, UUID generation, and the response envelopes with
    their metadata and links. Write links (update/delete/create) are only
    handed to admins, matching the routes that require_admin guards.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        group_repository: GroupRepository,
        post_stats_repository: PostStatsRepository,
    ) -> None:
        self.user_repository = user_repository
        self.group_repository = group_repository
        self.post_stats_repository = post_stats_repository

    async def create_user(self, request: UserCreateRequest, caller: Caller) -> UserDTO:
        model = await self.user_repository.create(
            user_id=str(uuid4()),
            name=request.name,
            email=request.email,
            role_ids=self.normalise_role_ids(request.roleIds),
            created_date=datetime.now(timezone.utc).isoformat(),
        )

        return self.to_dto(model, caller)

    async def get_user(self, user_id: str, caller: Caller) -> Optional[UserDTO]:
        model = await self.user_repository.get_by_id(user_id)
        return self.to_dto(model, caller) if model else None

    async def get_users(self, caller: Caller) -> List[UserDTO]:
        models = await self.user_repository.get_all()
        return [self.to_dto(model, caller) for model in models]

    async def search_users(self, term: Optional[str], caller: Caller) -> List[UserDTO]:
        models = await self.user_repository.search(term)
        return [self.to_dto(model, caller) for model in models]

    async def update_user(self, user_id: str, request: UserUpdateRequest, caller: Caller) -> Optional[UserDTO]:
        existing = await self.user_repository.get_by_id(user_id)

        if not existing:
            return None

        role_ids = (
            self.normalise_role_ids(request.roleIds)
            if "roleIds" in request.model_fields_set
            else None
        )

        if role_ids is not None and existing.id == caller.user_id and UserRole.ADMIN not in role_ids:
            raise SelfLockoutError("You cannot remove your own Admin role.")

        updated = await self.user_repository.update(
            user_id,
            name=request.name,
            email=request.email,
            role_ids=role_ids,
        )

        return self.to_dto(updated, caller)

    async def delete_user(self, user_id: str, caller: Caller) -> bool:
        existing = await self.user_repository.get_by_id(user_id)

        if not existing:
            return False

        if existing.id == caller.user_id:
            raise SelfLockoutError("You cannot delete yourself.")

        # Groups they owned carry on without an owner, and posts they liked
        # lose those likes (docs/social-groups.md).
        await self.group_repository.forget_user(user_id)
        await self.post_stats_repository.rebuild_all(datetime.now(timezone.utc).isoformat())
        await self.user_repository.delete(user_id)
        return True

    @staticmethod
    def normalise_role_ids(role_ids: Optional[list[UserRole]]) -> list[UserRole]:
        if not role_ids:
            return [UserRole.STANDARD]

        return list(dict.fromkeys(role_ids))

    def to_dto(self, model: UserModel, caller: Caller) -> UserDTO:
        return UserDTO(
            id=model.id,
            external_user_id=model.external_user_id,
            name=model.name,
            email=model.email,
            roleIds=model.role_ids,
            created_date=model.created_date,
            links=self.build_links(model.id, caller),
        )

    @staticmethod
    def build_links(user_id: str, caller: Caller) -> dict[str, Link]:
        url = f"{API_PREFIX}/users/{user_id}"
        links = {LINK_SELF: Link(href=url, method="GET")}

        if caller.is_admin:
            links[LINK_UPDATE_USER] = Link(href=url, method="PUT")
            # No delete link on yourself: the API refuses it (SelfLockoutError).
            if user_id != caller.user_id:
                links[LINK_DELETE_USER] = Link(href=url, method="DELETE")

        return links

    @staticmethod
    def build_meta_links(caller: Caller) -> dict[str, Link]:
        links = {LINK_SEARCH_USERS: Link(href=f"{API_PREFIX}/users/search", method="GET")}

        if caller.is_admin:
            links[LINK_CREATE_USER] = Link(href=f"{API_PREFIX}/users", method="POST")
            links[LINK_USER_TEMPLATE] = Link(href=f"{API_PREFIX}/users/template", method="GET")

        return links

    @staticmethod
    def build_metadata() -> UserMetadata:
        return UserMetadata(
            id=FieldMetadata(readOnly=True, hidden=True),
            external_user_id=FieldMetadata(readOnly=True, hidden=True),
            name=FieldMetadata(mandatory=True),
            email=FieldMetadata(mandatory=True),
            roleIds=FieldMetadata(mandatory=True, values=role_options()),
            created_date=FieldMetadata(readOnly=True),
        )

    def build_response(self, user: UserDTO, caller: Caller) -> UserResponse:
        return UserResponse.of(USER_DATA_NAME, user, self.build_metadata(), self.build_meta_links(caller))

    def build_list_response(self, users: List[UserDTO], caller: Caller) -> UserListResponse:
        return UserListResponse.of(USERS_DATA_NAME, users, self.build_metadata(), self.build_meta_links(caller))

    @staticmethod
    def build_template_response() -> UserTemplateResponse:
        return UserTemplateResponse.of(
            USER_DATA_NAME,
            UserCreateRequest(name="", email=""),
            UserTemplateMetadata(
                name=FieldMetadata(mandatory=True),
                email=FieldMetadata(mandatory=True),
                roleIds=FieldMetadata(mandatory=True, values=role_options()),
            ),
            {LINK_CREATE_USER: Link(href=f"{API_PREFIX}/users", method="POST")},
        )
