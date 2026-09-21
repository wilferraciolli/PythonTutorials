from typing import Any, Optional

from api_response import envelope
from models import Link, UserProfile, UserRole
from repositories.user_repository import UserRepository


class UserProfileService:
    """
    Application entrypoint for UI navigation.

    Until authentication is added, this returns a local development profile.
    When Clerk is added, this service should build the profile from the
    authenticated user and apply permission-based metadata/links.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return None

        return UserProfile(
            id=user["id"],
            name=user["name"],
            roleIds=user["roleIds"],
            links=self.build_user_profile_links(user["id"]),
        )

    def build_user_profile_links(self, user_id: str) -> dict[str, Link]:
        return {
            "self": Link(href=f"/users/{user_id}/profile", method="GET"),
            "user": Link(href=f"/users/{user_id}", method="GET"),
            "todos": Link(href="/todos", method="GET"),
            "createTodo": Link(href="/todos", method="POST"),
            "todoTemplate": Link(href="/todos/template", method="GET"),
            "tags": Link(href="/tags", method="GET"),
            "createTag": Link(href="/tags", method="POST"),
            "tagTemplate": Link(href="/tags/template", method="GET"),
            "users": Link(href="/users", method="GET"),
            "userTemplate": Link(href="/users/template", method="GET"),
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

    def build_meta_links(self) -> dict[str, Link]:
        return {
            "createTodo": Link(href="/todos", method="POST"),
            "todoTemplate": Link(href="/todos/template", method="GET"),
            "tags": Link(href="/tags", method="GET"),
            "tagTemplate": Link(href="/tags/template", method="GET"),
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
            meta_links=self.build_meta_links(),
            messages=messages,
        )
