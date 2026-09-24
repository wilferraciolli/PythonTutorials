from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from core.common.api_response import API_PREFIX
from core.common.base_dto import EmbeddedRef, FieldMetadata, Link, NoMetadata
from core.common.errors import ConflictError, ForbiddenError, NotFoundError
from core.security.authorization import Caller
from groups.constants import (
    FOLLOWERS_DATA_NAME,
    GROUP_DATA_NAME,
    GROUP_NOT_FOUND,
    GROUPS_DATA_NAME,
    LINK_ADD_MEMBER,
    LINK_ASSIGN_OWNER,
    LINK_CREATE_GROUP,
    LINK_CREATE_POST,
    LINK_DELETE,
    LINK_FOLLOW,
    LINK_FOLLOWERS,
    LINK_JOIN,
    LINK_LEAVE,
    LINK_MAKE_OWNER,
    LINK_MEMBERS,
    LINK_POSTS,
    LINK_REMOVE,
    LINK_SEARCH,
    LINK_SELF,
    LINK_UNFOLLOW,
    LINK_UPDATE,
    MEMBERS_DATA_NAME,
    NAME_MAX_LENGTH,
)
from groups.enums import GroupVisibility
from groups.group_permissions import GroupAccess, GroupPermissions
from groups.group_repository import GroupRepository
from groups.models import GroupFollowerModel, GroupMemberModel, GroupModel
from groups.schemas import (
    GroupCreateRequest,
    GroupDTO,
    GroupFollowerDTO,
    GroupFollowerListResponse,
    GroupListResponse,
    GroupMemberDTO,
    GroupMemberListResponse,
    GroupMetadata,
    GroupResponse,
    GroupUpdateRequest,
)
from users.user_repository import UserRepository


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GroupService:
    """
    Groups, members, owner and followers (docs/social-groups.md).

    Every rule question goes to GroupPermissions. A group the caller can't see
    is reported as 404, never 403, so a private group's existence isn't leaked.
    """

    def __init__(
        self,
        groups: GroupRepository,
        users: UserRepository,
        permissions: Optional[GroupPermissions] = None,
    ) -> None:
        self.groups = groups
        self.users = users
        self.permissions = permissions or GroupPermissions()

    # --- loading with access

    async def _access(self, caller: Caller, group: GroupModel) -> GroupAccess:
        return GroupAccess(
            group=group,
            is_member=await self.groups.is_member(group.id, caller.user_id),
            is_following=await self.groups.is_following(group.id, caller.user_id),
        )

    async def get_visible(self, caller: Caller, group_id: str) -> GroupAccess:
        """The group and the caller's place in it, or NotFoundError if it doesn't exist or is hidden."""
        group = await self.groups.get(group_id)
        if group is None:
            raise NotFoundError(GROUP_NOT_FOUND)

        access = await self._access(caller, group)
        if not self.permissions.can_view(caller, access):
            raise NotFoundError(GROUP_NOT_FOUND)
        return access

    # --- groups

    async def list_groups(
        self, caller: Caller, term: Optional[str] = None, following: bool = False, mine: bool = False
    ) -> List[GroupAccess]:
        groups = await self.groups.list_visible(caller.user_id, caller.is_admin, term, following, mine)
        return [await self._access(caller, group) for group in groups]

    async def create_group(self, caller: Caller, request: GroupCreateRequest) -> GroupAccess:
        name = request.name.strip()
        if await self.groups.get_by_name(name):
            raise ConflictError(f"A group called {name!r} already exists")

        now = _now()
        group = await self.groups.create(
            str(uuid4()), name, request.description, request.visibility.value, caller.user_id, now
        )
        await self.groups.add_member(group.id, caller.user_id, now)
        await self.groups.add_follower(group.id, caller.user_id, now)
        return await self.get_visible(caller, group.id)

    async def update_group(self, caller: Caller, group_id: str, request: GroupUpdateRequest) -> GroupAccess:
        access = await self.get_visible(caller, group_id)
        if not self.permissions.can_manage(caller, access):
            raise ForbiddenError("Only the group owner or an admin can edit the group")

        name = request.name.strip() if request.name is not None else None
        if name is not None:
            existing = await self.groups.get_by_name(name)
            if existing and existing.id != group_id:
                raise ConflictError(f"A group called {name!r} already exists")

        visibility = request.visibility.value if request.visibility is not None else None
        await self.groups.update(group_id, name=name, description=request.description, visibility=visibility)

        # A private group can only be followed by its members.
        if visibility == GroupVisibility.PRIVATE.value:
            await self.groups.remove_non_member_followers(group_id)

        return await self.get_visible(caller, group_id)

    async def delete_group(self, caller: Caller, group_id: str) -> None:
        access = await self.get_visible(caller, group_id)
        if not self.permissions.can_manage(caller, access):
            raise ForbiddenError("Only the group owner or an admin can delete the group")
        await self.groups.delete(group_id)

    async def assign_owner(self, caller: Caller, group_id: str, new_owner_id: str) -> GroupAccess:
        access = await self.get_visible(caller, group_id)
        if not self.permissions.can_manage(caller, access):
            raise ForbiddenError("Only the group owner or an admin can assign a new owner")
        if not await self.groups.is_member(group_id, new_owner_id):
            raise ConflictError("The new owner must be a member of the group; add them first")

        await self.groups.set_owner(group_id, new_owner_id)
        return await self.get_visible(caller, group_id)

    # --- members

    async def list_members(self, caller: Caller, group_id: str) -> tuple[GroupAccess, List[GroupMemberModel]]:
        access = await self.get_visible(caller, group_id)
        return access, await self.groups.list_members(group_id)

    async def join(self, caller: Caller, group_id: str) -> GroupAccess:
        access = await self.get_visible(caller, group_id)
        if access.is_member:
            return access
        if not self.permissions.can_join(caller, access):
            raise ForbiddenError("Private groups can only be joined by being added by a member")

        await self._make_member(group_id, caller.user_id)
        return await self.get_visible(caller, group_id)

    async def add_member(self, caller: Caller, group_id: str, user_id: str) -> GroupAccess:
        access = await self.get_visible(caller, group_id)
        if not self.permissions.can_add_member(caller, access):
            raise ForbiddenError("Only members, the owner or an admin can add people to this group")
        if await self.users.get_by_id(user_id) is None:
            raise NotFoundError("User not found")

        await self._make_member(group_id, user_id)
        return await self.get_visible(caller, group_id)

    async def remove_member(self, caller: Caller, group_id: str, user_id: str) -> None:
        access = await self.get_visible(caller, group_id)
        if not self.permissions.can_remove_member(caller, access, user_id):
            raise ForbiddenError("Only the group owner or an admin can remove other members")
        if not await self.groups.is_member(group_id, user_id):
            raise NotFoundError("Not a member of this group")

        await self.groups.remove_member(group_id, user_id)
        if access.group.owner_id == user_id:
            await self.groups.set_owner(group_id, None)  # an owner who leaves stops being owner
        if not access.is_public:
            await self.groups.remove_follower(group_id, user_id)  # can no longer see it

    async def _make_member(self, group_id: str, user_id: str) -> None:
        now = _now()
        await self.groups.add_member(group_id, user_id, now)
        await self.groups.add_follower(group_id, user_id, now)  # members follow automatically

    # --- followers

    async def list_followers(self, caller: Caller, group_id: str) -> tuple[GroupAccess, List[GroupFollowerModel]]:
        access = await self.get_visible(caller, group_id)
        return access, await self.groups.list_followers(group_id)

    async def follow(self, caller: Caller, group_id: str) -> GroupAccess:
        # Seeing the group is enough: a private group is only visible to members (and admins).
        await self.get_visible(caller, group_id)
        await self.groups.add_follower(group_id, caller.user_id, _now())
        return await self.get_visible(caller, group_id)

    async def unfollow(self, caller: Caller, group_id: str) -> GroupAccess:
        await self.get_visible(caller, group_id)
        await self.groups.remove_follower(group_id, caller.user_id)
        return await self.get_visible(caller, group_id)

    # --- responses

    def to_dto(self, caller: Caller, access: GroupAccess) -> GroupDTO:
        group = access.group
        return GroupDTO(
            id=group.id,
            name=group.name,
            description=group.description,
            visibility=group.visibility,
            ownerId=group.owner_id,
            createdBy=group.created_by,
            created_date=group.created_date,
            memberCount=group.member_count,
            followerCount=group.follower_count,
            isOwner=access.is_owner(caller),
            isMember=access.is_member,
            isFollowing=access.is_following,
            links=self.build_group_links(caller, access),
        )

    def build_group_links(self, caller: Caller, access: GroupAccess) -> Dict[str, Link]:
        base = f"{API_PREFIX}/groups/{access.group.id}"
        p = self.permissions
        links = {
            LINK_SELF: Link(href=base, method="GET"),
            LINK_MEMBERS: Link(href=f"{base}/members", method="GET"),
            LINK_FOLLOWERS: Link(href=f"{base}/followers", method="GET"),
            LINK_POSTS: Link(href=f"{base}/posts", method="GET"),
        }
        if p.can_post(caller, access):
            links[LINK_CREATE_POST] = Link(href=f"{base}/posts", method="POST")
        if p.can_join(caller, access):
            links[LINK_JOIN] = Link(href=f"{base}/members/me", method="PUT")
        if p.can_leave(caller, access):
            links[LINK_LEAVE] = Link(href=f"{base}/members/me", method="DELETE")
        if p.can_follow(caller, access):
            links[LINK_FOLLOW] = Link(href=f"{base}/followers/me", method="PUT")
        if access.is_following:
            links[LINK_UNFOLLOW] = Link(href=f"{base}/followers/me", method="DELETE")
        if p.can_add_member(caller, access):
            links[LINK_ADD_MEMBER] = Link(href=f"{base}/members/{{userId}}", method="PUT")
        if p.can_manage(caller, access):
            links[LINK_UPDATE] = Link(href=base, method="PUT")
            links[LINK_DELETE] = Link(href=base, method="DELETE")
            links[LINK_ASSIGN_OWNER] = Link(href=f"{base}/owner", method="PUT")
        return links

    def member_to_dto(self, caller: Caller, access: GroupAccess, member: GroupMemberModel) -> GroupMemberDTO:
        base = f"{API_PREFIX}/groups/{access.group.id}"
        is_owner = member.user_id == access.group.owner_id
        links: Dict[str, Link] = {}
        if self.permissions.can_remove_member(caller, access, member.user_id):
            links[LINK_REMOVE] = Link(href=f"{base}/members/{member.user_id}", method="DELETE")
        if self.permissions.can_manage(caller, access) and not is_owner:
            links[LINK_MAKE_OWNER] = Link(href=f"{base}/owner", method="PUT")
        return GroupMemberDTO(
            userId=member.user_id,
            name=member.name,
            isOwner=is_owner,
            joined_date=member.joined_date,
            links=links,
        )

    @staticmethod
    def build_metadata() -> GroupMetadata:
        return GroupMetadata(
            name=FieldMetadata(mandatory=True, maxLength=NAME_MAX_LENGTH),
            visibility=FieldMetadata(
                mandatory=True,
                values=[
                    EmbeddedRef(id=GroupVisibility.PUBLIC.value, value="Public"),
                    EmbeddedRef(id=GroupVisibility.PRIVATE.value, value="Private"),
                ],
            ),
            ownerId=FieldMetadata(readOnly=True),
        )

    def build_response(self, caller: Caller, access: GroupAccess) -> GroupResponse:
        return GroupResponse.of(GROUP_DATA_NAME, self.to_dto(caller, access), self.build_metadata())

    def build_list_response(self, caller: Caller, accesses: List[GroupAccess]) -> GroupListResponse:
        return GroupListResponse.of(
            GROUPS_DATA_NAME,
            [self.to_dto(caller, access) for access in accesses],
            self.build_metadata(),
            {
                LINK_CREATE_GROUP: Link(href=f"{API_PREFIX}/groups", method="POST"),
                LINK_SEARCH: Link(href=f"{API_PREFIX}/groups?q=", method="GET"),
            },
        )

    def build_members_response(
        self, caller: Caller, access: GroupAccess, members: List[GroupMemberModel]
    ) -> GroupMemberListResponse:
        return GroupMemberListResponse.of(
            MEMBERS_DATA_NAME, [self.member_to_dto(caller, access, member) for member in members], NoMetadata()
        )

    @staticmethod
    def build_followers_response(followers: List[GroupFollowerModel]) -> GroupFollowerListResponse:
        return GroupFollowerListResponse.of(
            FOLLOWERS_DATA_NAME,
            [
                GroupFollowerDTO(userId=follower.user_id, name=follower.name, created_date=follower.created_date)
                for follower in followers
            ],
            NoMetadata(),
        )
