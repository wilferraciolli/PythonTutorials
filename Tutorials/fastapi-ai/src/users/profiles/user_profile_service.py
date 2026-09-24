from typing import Optional

from core.common.api_response import API_PREFIX
from core.common.base_dto import FieldMetadata, Link
from core.security.authorization import Caller
from core.security.roles import role_options
from users.models import UserModel
from users.profiles.constants import (
    LINK_ADMIN,
    LINK_AI_ASSISTANT,
    LINK_AI_CHAT_SEARCH,
    LINK_AI_CHATS,
    LINK_CREATE_GROUP,
    LINK_CREATE_TAG,
    LINK_GROUPS,
    LINK_SEARCH_UNSPLASH,
    LINK_SEARCH_USERS,
    LINK_SELF,
    LINK_TAG_TEMPLATE,
    LINK_TAGS,
    LINK_TIMELINE_ALL,
    LINK_TIMELINE_FOLLOWING,
    LINK_TIMELINE_POPULAR,
    LINK_TODO_TEMPLATE,
    LINK_TODOS,
    LINK_USER,
    LINK_USER_TEMPLATE,
    LINK_USERS,
    USER_PROFILE_DATA_NAME,
)
from users.profiles.schemas import UserProfileDTO, UserProfileMetadata, UserProfileResponse
from users.user_repository import UserRepository


class UserProfileService:
    """
    Application entrypoint for UI navigation.

    `/me` only tells the client who it is and hands out the `userProfile`
    link. Every other link the UI follows lives here, on
    `/users/{user_id}/profile`, keyed by the user id in the path — so the
    rules for "may this caller see that user's resources?" live in one
    place (`can_view_profile`) instead of being scattered over each feature.

    Access rules:
    - Any signed-in caller may view any profile.
    - Only the owner may change a profile. There is no PUT yet; when one is
      added, guard it with `can_edit_profile`.
    - Personal links (todos, AI chats, the assistant) only appear on your
      own profile: those APIs refuse anyone else (require_owner).
    - Admin links (`userTemplate`, `admin`) only appear for admins.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def get_user_profile(self, user_id: str, caller: Caller) -> Optional[UserProfileDTO]:
        """
        Build the profile for the user in the path, as seen by `caller`.

        Returns None if that user doesn't exist; raises PermissionError if
        the caller may not see them (the router maps it to 403).
        """
        target = await self.user_repository.get_by_id(user_id)

        if not target:
            return None

        if not self.can_view_profile(caller, target):
            raise PermissionError(f"{caller.external_id} may not view profile {target.id}")

        return UserProfileDTO(
            id=target.id,
            externalId=target.external_user_id,
            name=target.name,
            email=target.email,
            roleIds=target.role_ids,
            links=self.build_links(target.id, caller),
        )

    @staticmethod
    def can_view_profile(caller: Caller, target: UserModel) -> bool:
        # Everyone signed in may see everyone's profile.
        return True

    @staticmethod
    def can_edit_profile(caller: Caller, target: UserModel) -> bool:
        # Only the owner may change their profile — use this to guard a PUT.
        return caller.user_id is not None and caller.user_id == target.id

    @staticmethod
    def build_links(user_id: str, caller: Caller) -> dict[str, Link]:
        # No standalone `createTodo`/`createUser` link here: a create URL is
        # never POSTed to blind. Clients GET the template (its field metadata
        # says what's mandatory) and derive the create URL from that link.
        links = {
            LINK_SELF: Link(href=f"{API_PREFIX}/users/{user_id}/profile", method="GET"),
            LINK_USER: Link(href=f"{API_PREFIX}/users/{user_id}", method="GET"),
            LINK_USERS: Link(href=f"{API_PREFIX}/users", method="GET"),
            LINK_SEARCH_USERS: Link(href=f"{API_PREFIX}/users/search", method="GET"),
            LINK_TAGS: Link(href=f"{API_PREFIX}/tags", method="GET"),
            LINK_CREATE_TAG: Link(href=f"{API_PREFIX}/tags", method="POST"),
            LINK_TAG_TEMPLATE: Link(href=f"{API_PREFIX}/tags/template", method="GET"),
            LINK_GROUPS: Link(href=f"{API_PREFIX}/groups", method="GET"),
            LINK_CREATE_GROUP: Link(href=f"{API_PREFIX}/groups", method="POST"),
            LINK_TIMELINE_ALL: Link(href=f"{API_PREFIX}/timeline/posts?type=ALL", method="GET"),
            LINK_TIMELINE_FOLLOWING: Link(href=f"{API_PREFIX}/timeline/posts?type=FOLLOWING", method="GET"),
            LINK_TIMELINE_POPULAR: Link(href=f"{API_PREFIX}/timeline/posts?type=POPULAR", method="GET"),
            # Unsplash search for the post media picker (append ?q=...). Giphy is searched
            # from the browser and YouTube needs no search.
            LINK_SEARCH_UNSPLASH: Link(href=f"{API_PREFIX}/media/unsplash/search", method="GET"),
        }

        # Todos, AI chats and the assistant are personal: only offered on
        # your own profile.
        if caller.user_id == user_id:
            links[LINK_TODOS] = Link(href=f"{API_PREFIX}/users/{user_id}/todos", method="GET")
            links[LINK_TODO_TEMPLATE] = Link(href=f"{API_PREFIX}/users/{user_id}/todos/template", method="GET")
            links[LINK_AI_CHATS] = Link(href=f"{API_PREFIX}/users/{user_id}/chats", method="GET")
            links[LINK_AI_CHAT_SEARCH] = Link(href=f"{API_PREFIX}/users/{user_id}/chats/search", method="GET")
            links[LINK_AI_ASSISTANT] = Link(href=f"{API_PREFIX}/users/{user_id}/assistant/ask", method="POST")

        # Creating users is admin-only, so only admins get the way in.
        if caller.is_admin:
            links[LINK_USER_TEMPLATE] = Link(href=f"{API_PREFIX}/users/template", method="GET")

        # The admin area, only on an admin's own profile.
        if caller.is_admin and caller.user_id == user_id:
            links[LINK_ADMIN] = Link(href=f"{API_PREFIX}/admin", method="GET")

        return links

    @staticmethod
    def build_metadata() -> UserProfileMetadata:
        return UserProfileMetadata(
            id=FieldMetadata(readOnly=True, hidden=True),
            name=FieldMetadata(readOnly=True),
            roleIds=FieldMetadata(readOnly=True, values=role_options()),
        )

    def build_response(self, user_profile: UserProfileDTO) -> UserProfileResponse:
        return UserProfileResponse.of(USER_PROFILE_DATA_NAME, user_profile, self.build_metadata())
