from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from api_response import API_PREFIX, envelope
from errors import ConflictError, ForbiddenError, NotFoundError
from group_permissions import Caller, GroupAccess, GroupPermissions
from models import Group, GroupCreate, GroupFollower, GroupMember, GroupUpdate, GroupVisibility, Link
from repositories.group_repository import GroupRepository
from repositories.user_repository import UserRepository

GROUP_NOT_FOUND = "Group not found"


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

    async def _access(self, caller: Caller, group: Dict[str, Any]) -> GroupAccess:
        return GroupAccess(
            group=group,
            is_member=await self.groups.is_member(group["id"], caller.id),
            is_following=await self.groups.is_following(group["id"], caller.id),
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

    async def _reload(self, caller: Caller, group_id: str) -> GroupAccess:
        return await self.get_visible(caller, group_id)

    # --- groups

    async def list_groups(
        self, caller: Caller, term: Optional[str] = None, following: bool = False, mine: bool = False
    ) -> List[GroupAccess]:
        rows = await self.groups.list_visible(caller.id, caller.is_admin, term, following, mine)
        return [await self._access(caller, row) for row in rows]

    async def create_group(self, caller: Caller, payload: GroupCreate) -> GroupAccess:
        name = payload.name.strip()
        if await self.groups.get_by_name(name):
            raise ConflictError(f"A group called {name!r} already exists")

        now = _now()
        group = await self.groups.create(
            str(uuid4()), name, payload.description, payload.visibility.value, caller.id, now
        )
        await self.groups.add_member(group["id"], caller.id, now)
        await self.groups.add_follower(group["id"], caller.id, now)
        return await self._reload(caller, group["id"])

    async def update_group(self, caller: Caller, group_id: str, payload: GroupUpdate) -> GroupAccess:
        access = await self.get_visible(caller, group_id)
        if not self.permissions.can_manage(caller, access):
            raise ForbiddenError("Only the group owner or an admin can edit the group")

        name = payload.name.strip() if payload.name is not None else None
        if name is not None:
            existing = await self.groups.get_by_name(name)
            if existing and existing["id"] != group_id:
                raise ConflictError(f"A group called {name!r} already exists")

        visibility = payload.visibility.value if payload.visibility is not None else None
        await self.groups.update(group_id, name=name, description=payload.description, visibility=visibility)

        # A private group can only be followed by its members.
        if visibility == GroupVisibility.PRIVATE.value:
            await self.groups.remove_non_member_followers(group_id)

        return await self._reload(caller, group_id)

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
        return await self._reload(caller, group_id)

    # --- members

    async def list_members(self, caller: Caller, group_id: str) -> tuple[GroupAccess, List[Dict[str, Any]]]:
        access = await self.get_visible(caller, group_id)
        return access, await self.groups.list_members(group_id)

    async def join(self, caller: Caller, group_id: str) -> GroupAccess:
        access = await self.get_visible(caller, group_id)
        if access.is_member:
            return access
        if not self.permissions.can_join(caller, access):
            raise ForbiddenError("Private groups can only be joined by being added by a member")

        await self._make_member(group_id, caller.id)
        return await self._reload(caller, group_id)

    async def add_member(self, caller: Caller, group_id: str, user_id: str) -> GroupAccess:
        access = await self.get_visible(caller, group_id)
        if not self.permissions.can_add_member(caller, access):
            raise ForbiddenError("Only members, the owner or an admin can add people to this group")
        if await self.users.get_by_id(user_id) is None:
            raise NotFoundError("User not found")

        await self._make_member(group_id, user_id)
        return await self._reload(caller, group_id)

    async def remove_member(self, caller: Caller, group_id: str, user_id: str) -> None:
        access = await self.get_visible(caller, group_id)
        if not self.permissions.can_remove_member(caller, access, user_id):
            raise ForbiddenError("Only the group owner or an admin can remove other members")
        if not await self.groups.is_member(group_id, user_id):
            raise NotFoundError("Not a member of this group")

        await self.groups.remove_member(group_id, user_id)
        if access.group.get("owner_id") == user_id:
            await self.groups.set_owner(group_id, None)  # an owner who leaves stops being owner
        if not access.is_public:
            await self.groups.remove_follower(group_id, user_id)  # can no longer see it

    async def _make_member(self, group_id: str, user_id: str) -> None:
        now = _now()
        await self.groups.add_member(group_id, user_id, now)
        await self.groups.add_follower(group_id, user_id, now)  # members follow automatically

    # --- followers

    async def list_followers(self, caller: Caller, group_id: str) -> tuple[GroupAccess, List[Dict[str, Any]]]:
        access = await self.get_visible(caller, group_id)
        return access, await self.groups.list_followers(group_id)

    async def follow(self, caller: Caller, group_id: str) -> GroupAccess:
        # Seeing the group is enough: a private group is only visible to members (and admins).
        await self.get_visible(caller, group_id)
        await self.groups.add_follower(group_id, caller.id, _now())
        return await self._reload(caller, group_id)

    async def unfollow(self, caller: Caller, group_id: str) -> GroupAccess:
        await self.get_visible(caller, group_id)
        await self.groups.remove_follower(group_id, caller.id)
        return await self._reload(caller, group_id)

    # --- responses

    def to_group(self, caller: Caller, access: GroupAccess) -> Group:
        group = access.group
        return Group(
            id=group["id"],
            name=group["name"],
            description=group.get("description"),
            visibility=group["visibility"],
            ownerId=group.get("owner_id"),
            createdBy=group.get("created_by"),
            created_date=group["created_date"],
            memberCount=group.get("member_count", 0),
            followerCount=group.get("follower_count", 0),
            isOwner=access.is_owner(caller),
            isMember=access.is_member,
            isFollowing=access.is_following,
            links=self.build_group_links(caller, access),
        )

    def build_group_links(self, caller: Caller, access: GroupAccess) -> Dict[str, Link]:
        base = f"{API_PREFIX}/groups/{access.group['id']}"
        p = self.permissions
        links = {
            "self": Link(href=base, method="GET"),
            "members": Link(href=f"{base}/members", method="GET"),
            "followers": Link(href=f"{base}/followers", method="GET"),
        }
        if p.can_join(caller, access):
            links["join"] = Link(href=f"{base}/members/me", method="PUT")
        if p.can_leave(caller, access):
            links["leave"] = Link(href=f"{base}/members/me", method="DELETE")
        if p.can_follow(caller, access):
            links["follow"] = Link(href=f"{base}/followers/me", method="PUT")
        if access.is_following:
            links["unfollow"] = Link(href=f"{base}/followers/me", method="DELETE")
        if p.can_add_member(caller, access):
            links["addMember"] = Link(href=f"{base}/members/{{userId}}", method="PUT")
        if p.can_manage(caller, access):
            links["update"] = Link(href=base, method="PUT")
            links["delete"] = Link(href=base, method="DELETE")
            links["assignOwner"] = Link(href=f"{base}/owner", method="PUT")
        return links

    def build_response(self, caller: Caller, access: GroupAccess) -> Dict[str, Any]:
        return envelope(
            data_name="group", data=self.to_group(caller, access), metadata=self._metadata(), meta_links={}
        )

    def build_list_response(self, caller: Caller, accesses: List[GroupAccess]) -> Dict[str, Any]:
        return envelope(
            data_name="groups",
            data=[self.to_group(caller, access) for access in accesses],
            metadata=self._metadata(),
            meta_links={
                "createGroup": Link(href=f"{API_PREFIX}/groups", method="POST"),
                "search": Link(href=f"{API_PREFIX}/groups?q=", method="GET"),
            },
        )

    def build_members_response(self, caller: Caller, access: GroupAccess, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        base = f"{API_PREFIX}/groups/{access.group['id']}/members"
        members = []
        for row in rows:
            links = {}
            if self.permissions.can_remove_member(caller, access, row["user_id"]):
                links["remove"] = Link(href=f"{base}/{row['user_id']}", method="DELETE")
            if self.permissions.can_manage(caller, access) and row["user_id"] != access.group.get("owner_id"):
                links["makeOwner"] = Link(href=f"{API_PREFIX}/groups/{access.group['id']}/owner", method="PUT")
            members.append(
                GroupMember(
                    userId=row["user_id"],
                    name=row.get("name"),
                    isOwner=row["user_id"] == access.group.get("owner_id"),
                    joined_date=row["joined_date"],
                    links=links,
                )
            )
        return envelope(data_name="members", data=members, metadata={}, meta_links={})

    def build_followers_response(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        followers = [
            GroupFollower(userId=row["user_id"], name=row.get("name"), created_date=row["created_date"])
            for row in rows
        ]
        return envelope(data_name="followers", data=followers, metadata={}, meta_links={})

    def _metadata(self) -> Dict[str, Any]:
        return {
            "name": {"mandatory": True, "maxLength": 80},
            "visibility": {
                "mandatory": True,
                "values": [
                    {"id": GroupVisibility.PUBLIC.value, "value": "Public"},
                    {"id": GroupVisibility.PRIVATE.value, "value": "Private"},
                ],
            },
            "ownerId": {"readOnly": True},
        }
