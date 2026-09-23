"""Shared setup for the social-groups tests (not a test module itself)."""
from dataclasses import dataclass

from database import SQLiteDatabase
from group_permissions import Caller
from models import CommentCreate, GroupCreate, GroupVisibility, PostCreate, UserRole
from repositories.group_repository import GroupRepository
from repositories.post_comment_repository import PostCommentRepository
from repositories.post_repository import PostRepository
from repositories.post_stats_repository import PostStatsRepository
from repositories.reaction_repository import ReactionRepository
from repositories.user_repository import UserRepository
from services.group_service import GroupService
from services.post_comment_service import PostCommentService
from services.post_service import PostService

OWNER = Caller("owner", False)
MEMBER = Caller("member", False)
OUTSIDER = Caller("outsider", False)
ADMIN = Caller("admin", True)

NEWS_ID = "00000000-0000-4000-8000-000000000001"


@dataclass
class Social:
    db: SQLiteDatabase
    users: UserRepository
    groups: GroupService
    posts: PostService
    comments: PostCommentService

    async def group(self, visibility=GroupVisibility.PUBLIC, name="Cyclists") -> str:
        """A group owned by OWNER with MEMBER in it."""
        access = await self.groups.create_group(OWNER, GroupCreate(name=name, visibility=visibility))
        await self.groups.add_member(OWNER, access.group["id"], "member")
        return access.group["id"]

    async def post(self, group_id, caller=MEMBER, title="Bike lanes", body="Thoughts?"):
        _, row = await self.posts.create_post(caller, group_id, PostCreate(title=title, body=body))
        return row

    async def comment(self, group_id, post_id, caller=MEMBER, body="Nice", parent=None):
        _, _, row = await self.comments.create_comment(
            caller, group_id, post_id, CommentCreate(body=body, parentCommentId=parent)
        )
        return row


async def make_social(tmp_path, media=None) -> Social:
    db = SQLiteDatabase(str(tmp_path / "social.db"))
    users = UserRepository(db)
    for user_id in ("owner", "member", "outsider", "admin"):
        role = [UserRole.ADMIN] if user_id == "admin" else [UserRole.STANDARD]
        await users.create(user_id, user_id.title(), f"{user_id}@x.io", role, "2026-01-01T00:00:00Z")

    stats, reactions = PostStatsRepository(db), ReactionRepository(db)
    groups = GroupService(GroupRepository(db), users)
    posts = PostService(PostRepository(db), stats, reactions, groups, media)
    comments = PostCommentService(PostCommentRepository(db), stats, reactions, posts)
    return Social(db, users, groups, posts, comments)
