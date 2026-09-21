from typing import Any, Optional

from api_response import envelope
from models import Link, UserProfile, UserRole


class UserProfileService:
    """
    Application entrypoint for UI navigation.

    Until authentication is added, this returns a local development profile.
    When Clerk is added, this service should build the profile from the
    authenticated user and apply permission-based metadata/links.
    """

    def get_user_profile(self) -> UserProfile:
        return UserProfile(
            id="local-dev-user",
            name="Local Developer",
            roleIds=[UserRole.STANDARD],
            links=self.build_user_profile_links(),
        )

    def build_user_profile_links(self) -> dict[str, Link]:
        return {
            "self": Link(href="/userprofiles", method="GET"),
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
        messages: Optional[list[dict[str, str]]] = None,
    ) -> dict[str, Any]:
        return envelope(
            data_name="userProfile",
            data=self.get_user_profile(),
            metadata=self.build_metadata(),
            meta_links=self.build_meta_links(),
            messages=messages,
        )
