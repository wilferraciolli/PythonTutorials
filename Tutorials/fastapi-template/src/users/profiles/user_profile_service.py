from typing import Optional

from core.common.api_response import API_PREFIX
from core.common.base_dto import FieldMetadata, Link
from core.security.authorization import Caller
from core.security.roles import role_options
from users.models import UserModel
from users.profiles.constants import (
    LINK_SEARCH_USERS,
    LINK_SELF,
    LINK_USER,
    LINK_USER_SETTINGS,
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
    - Personal links (e.g. `userSettings`) only appear on your own profile.
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
        # No standalone `createUser` link here: the create URL is never
        # POSTed to blind. Clients GET `userTemplate` (its field metadata
        # says what's mandatory) and derive the create URL from that link.
        links = {
            LINK_SELF: Link(href=f"{API_PREFIX}/users/{user_id}/profile", method="GET"),
            LINK_USER: Link(href=f"{API_PREFIX}/users/{user_id}", method="GET"),
            LINK_USERS: Link(href=f"{API_PREFIX}/users", method="GET"),
            LINK_SEARCH_USERS: Link(href=f"{API_PREFIX}/users/search", method="GET"),
        }

        # Settings are personal: only offered on your own profile.
        if caller.user_id == user_id:
            links[LINK_USER_SETTINGS] = Link(href=f"{API_PREFIX}/users/{user_id}/settings", method="GET")

        # Creating users is admin-only, so only admins get the way in.
        if caller.is_admin:
            links[LINK_USER_TEMPLATE] = Link(href=f"{API_PREFIX}/users/template", method="GET")

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
