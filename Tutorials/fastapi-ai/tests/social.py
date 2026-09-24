"""Shared setup for the social-groups tests (not a test module itself)."""
from dataclasses import dataclass

from core.config.database import SQLiteDatabase
from core.security.authorization import Caller
from core.security.roles import UserRole
from groups.enums import GroupVisibility
from groups.group_repository import GroupRepository
from groups.group_service import GroupService
from groups.posts.comments.comment_repository import CommentRepository
from groups.posts.comments.comment_service import CommentService
from groups.posts.comments.schemas import CommentCreateRequest
from groups.posts.post_repository import PostRepository
from groups.posts.post_service import PostService
from groups.posts.post_stats_repository import PostStatsRepository
from groups.posts.reaction_repository import ReactionRepository
from groups.posts.schemas import PostCreateRequest
from groups.schemas import GroupCreateRequest
from users.user_repository import UserRepository

OWNER = Caller(external_id="owner", user_id="owner", role_ids=[])
MEMBER = Caller(external_id="member", user_id="member", role_ids=[])
OUTSIDER = Caller(external_id="outsider", user_id="outsider", role_ids=[])
ADMIN = Caller(external_id="admin", user_id="admin", role_ids=["ADMIN"])

NEWS_ID = "00000000-0000-4000-8000-000000000001"


@dataclass
class Social:
    db: SQLiteDatabase
    users: UserRepository
    groups: GroupService
    posts: PostService
    comments: CommentService

    async def group(self, visibility=GroupVisibility.PUBLIC, name="Cyclists") -> str:
        """A group owned by OWNER with MEMBER in it."""
        access = await self.groups.create_group(OWNER, GroupCreateRequest(name=name, visibility=visibility))
        await self.groups.add_member(OWNER, access.group.id, "member")
        return access.group.id

    async def post(self, group_id, caller=MEMBER, title="Bike lanes", body="Thoughts?"):
        _, row = await self.posts.create_post(caller, group_id, PostCreateRequest(title=title, body=body))
        return row

    async def comment(self, group_id, post_id, caller=MEMBER, body="Nice", parent=None):
        _, _, row = await self.comments.create_comment(
            caller, group_id, post_id, CommentCreateRequest(body=body, parentCommentId=parent)
        )
        return row


async def make_social(tmp_path, media=None, search=None) -> Social:
    """`search`: a function db -> PostSearchService, to index posts and comments as they're written."""
    db = SQLiteDatabase(str(tmp_path / "social.db"))
    users = UserRepository(db)
    for user_id in ("owner", "member", "outsider", "admin"):
        role = [UserRole.ADMIN] if user_id == "admin" else [UserRole.STANDARD]
        await users.create(user_id, user_id.title(), f"{user_id}@x.io", role, "2026-01-01T00:00:00Z")

    stats, reactions = PostStatsRepository(db), ReactionRepository(db)
    groups = GroupService(GroupRepository(db), users)
    posts = PostService(PostRepository(db), stats, reactions, groups, media, search(db) if search else None)
    comments = CommentService(CommentRepository(db), stats, reactions, posts)
    return Social(db, users, groups, posts, comments)
