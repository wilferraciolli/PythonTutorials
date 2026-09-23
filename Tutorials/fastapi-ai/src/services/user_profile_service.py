from typing import Any, Dict, Optional

from api_response import API_PREFIX, envelope
from models import Link, UserProfile, UserRole
from repositories.user_repository import UserRepository


class UserProfileService:
    """
    Application entrypoint for UI navigation.

    `/me` only tells the client who it is and hands out the `userProfile`
    link. Every other link the UI follows lives here, on
    `/users/{user_id}/profile`, keyed by the user id in the path — so the
    rules for "may this caller see that user's resources?" live in one
    place (`can_view_profile`) instead of being scattered over each feature.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def get_user_profile(self, user_id: str, caller: Dict[str, Any]) -> Optional[UserProfile]:
        """
        Build the profile for the user in the path, as seen by `caller`.

        Returns None if that user doesn't exist; raises PermissionError if
        the caller may not see them (the router maps it to 403).
        """
        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return None

        if not self.can_view_profile(caller, user):
            raise PermissionError(f"user {caller['id']} may not view profile {user['id']}")

        return UserProfile(
            id=user["id"],
            externalId=user.get("external_user_id"),
            name=user["name"],
            email=user.get("email"),
            roleIds=user["roleIds"],
            links=self.build_user_profile_links(user["id"]),
        )

    def can_view_profile(self, caller: Dict[str, Any], target: Dict[str, Any]) -> bool:
        # Business-logic seam: decide whether `caller` (the logged-in
        # user's row) may see `target` (the user whose id is in the path)
        # and, through the links built for that id, their resources.
        # Currently open to any signed-in caller — tighten here (e.g. self
        # or ADMIN only).
        return True

    def build_user_profile_links(self, user_id: str) -> dict[str, Link]:
        # No standalone `createTodo` link here: the create URL is never
        # POSTed to blind. Clients GET `todoTemplate` (its field metadata
        # says what's mandatory) and derive the create URL from that link.
        return {
            "self": Link(href=f"{API_PREFIX}/users/{user_id}/profile", method="GET"),
            "user": Link(href=f"{API_PREFIX}/users/{user_id}", method="GET"),
            "users": Link(href=f"{API_PREFIX}/users", method="GET"),
            "userTemplate": Link(href=f"{API_PREFIX}/users/template", method="GET"),
            "searchUsers": Link(href=f"{API_PREFIX}/users/search", method="GET"),
            "todos": Link(href=f"{API_PREFIX}/users/{user_id}/todos", method="GET"),
            "todoTemplate": Link(href=f"{API_PREFIX}/users/{user_id}/todos/template", method="GET"),
            "tags": Link(href=f"{API_PREFIX}/tags", method="GET"),
            "createTag": Link(href=f"{API_PREFIX}/tags", method="POST"),
            "tagTemplate": Link(href=f"{API_PREFIX}/tags/template", method="GET"),
            "aiChats": Link(href=f"{API_PREFIX}/users/{user_id}/chats", method="GET"),
            "aiChatSearch": Link(href=f"{API_PREFIX}/users/{user_id}/chats/search", method="GET"),
            "aiAssistant": Link(href=f"{API_PREFIX}/users/{user_id}/assistant/ask", method="POST"),
        }

    def build_metadata(self) -> dict[str, Any]:
        return {
            "id": {
                "readOnly": True,
                "hidden": True,
            },
            "name": {
                "readOnly": True,
            },
            "roleIds": {
                "readOnly": True,
                "values": [
                    {
                        "id": UserRole.STANDARD.value,
                        "value": "Standard user",
                    },
                    {
                        "id": UserRole.ADMIN.value,
                        "value": "System Administrator",
                    },
                ],
            },
        }

    def build_response(
        self,
        user_profile: UserProfile,
        messages: Optional[list[dict[str, str]]] = None,
    ) -> dict[str, Any]:
        return envelope(
            data_name="userProfile",
            data=user_profile,
            metadata=self.build_metadata(),
            meta_links={},
            messages=messages,
        )
