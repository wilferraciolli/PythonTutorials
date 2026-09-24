from dataclasses import dataclass
from typing import Optional

from core.security.authorization import Caller
from groups.enums import GroupVisibility
from groups.models import GroupModel


@dataclass(frozen=True)
class GroupAccess:
    """What the permission checks need to know about one group and the caller's place in it."""

    group: GroupModel
    is_member: bool
    is_following: bool

    @property
    def is_public(self) -> bool:
        return self.group.visibility == GroupVisibility.PUBLIC

    def is_owner(self, caller: Caller) -> bool:
        return self.group.owner_id is not None and self.group.owner_id == caller.user_id


class GroupPermissions:
    """
    Every "may this caller ...?" question about groups, in one place, so the
    API, the timeline and the AI tools can't disagree (docs/social-groups.md).

    Rule zero: a system ADMIN (their saved roles) bypasses all of it.
    """

    def can_view(self, caller: Caller, access: GroupAccess) -> bool:
        return caller.is_admin or access.is_public or access.is_member or access.is_owner(caller)

    def can_manage(self, caller: Caller, access: GroupAccess) -> bool:
        """Edit the group, change visibility, remove other members, assign owner, delete."""
        return caller.is_admin or access.is_owner(caller)

    def can_join(self, caller: Caller, access: GroupAccess) -> bool:
        return not access.is_member and (caller.is_admin or access.is_public)

    def can_leave(self, caller: Caller, access: GroupAccess) -> bool:
        return access.is_member

    def can_add_member(self, caller: Caller, access: GroupAccess) -> bool:
        # A private group is only visible to its members, so any member may bring someone in.
        return caller.is_admin or access.is_member or access.is_owner(caller)

    def can_remove_member(self, caller: Caller, access: GroupAccess, target_user_id: str) -> bool:
        return target_user_id == caller.user_id or self.can_manage(caller, access)

    def can_follow(self, caller: Caller, access: GroupAccess) -> bool:
        return not access.is_following and self.can_view(caller, access)

    def can_post(self, caller: Caller, access: GroupAccess) -> bool:
        return caller.is_admin or access.is_member

    def can_delete_content(self, caller: Caller, access: GroupAccess, author_id: Optional[str]) -> bool:
        """Delete a post or comment: its author, the group owner, or an admin."""
        return (author_id is not None and author_id == caller.user_id) or self.can_manage(caller, access)
