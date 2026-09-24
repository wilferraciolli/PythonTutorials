"""Social groups: likes and post_stats (score = comments x 2 + likes)."""
import pytest

from core.common.errors import ConflictError, ForbiddenError, NotFoundError
from groups.enums import GroupVisibility
from groups.posts.post_stats_repository import PostStatsRepository
from groups.group_repository import GroupRepository
from users.user_repository import UserRepository
from users.user_service import UserService
from social import ADMIN, MEMBER, OUTSIDER, OWNER, make_social


@pytest.fixture
async def s(tmp_path):
    return await make_social(tmp_path)


async def stats(s, post_id):
    return await s.db.fetch_one("SELECT like_count, comment_count, score FROM post_stats WHERE post_id = ?", (post_id,))


async def test_score_counts_comments_twice_and_likes_once(s):
    group_id = await s.group()
    row = await s.post(group_id)
    assert await stats(s, row.id) == {"like_count": 0, "comment_count": 0, "score": 0}

    top = await s.comment(group_id, row.id)
    await s.comment(group_id, row.id, caller=OWNER, parent=top.id)  # replies count as comments
    await s.posts.like(OWNER, group_id, row.id)
    await s.posts.like(MEMBER, group_id, row.id)

    assert await stats(s, row.id) == {"like_count": 2, "comment_count": 2, "score": 6}


async def test_liking_twice_counts_once_and_unlike_reverts(s):
    group_id = await s.group()
    row = await s.post(group_id)

    await s.posts.like(MEMBER, group_id, row.id)
    _, liked = await s.posts.like(MEMBER, group_id, row.id)
    assert liked.like_count == 1 and liked.liked_by_me

    _, unliked = await s.posts.unlike(MEMBER, group_id, row.id)
    assert unliked.like_count == 0 and not unliked.liked_by_me
    assert (await stats(s, row.id))["score"] == 0


async def test_liked_by_me_is_per_user(s):
    group_id = await s.group()
    row = await s.post(group_id)
    await s.posts.like(OWNER, group_id, row.id)

    _, rows = await s.posts.list_posts(MEMBER, group_id)
    assert rows[0].like_count == 1 and not rows[0].liked_by_me
    access, mine = await s.posts.get_post(OWNER, group_id, row.id)
    assert mine.liked_by_me and "unlike" in s.posts.to_dto(OWNER, access, mine).links


async def test_comment_likes_do_not_change_the_post_score(s):
    group_id = await s.group()
    row = await s.post(group_id)
    comment = await s.comment(group_id, row.id)

    _, _, liked = await s.comments.like(OWNER, group_id, row.id, comment.id)
    assert liked.like_count == 1 and liked.liked_by_me
    assert (await stats(s, row.id))["score"] == 2  # just the comment

    _, _, unliked = await s.comments.unlike(OWNER, group_id, row.id, comment.id)
    assert unliked.like_count == 0


async def test_only_members_and_admins_like(s):
    group_id = await s.group()
    row = await s.post(group_id)
    await s.groups.follow(OUTSIDER, group_id)

    with pytest.raises(ForbiddenError):  # a follower isn't a member
        await s.posts.like(OUTSIDER, group_id, row.id)
    await s.posts.like(ADMIN, group_id, row.id)


async def test_cannot_like_hidden_or_deleted_posts(s):
    private_id = await s.group(GroupVisibility.PRIVATE, name="Secret")
    hidden = await s.post(private_id)
    with pytest.raises(NotFoundError):
        await s.posts.like(OUTSIDER, private_id, hidden.id)

    await s.posts.delete_post(MEMBER, private_id, hidden.id)
    with pytest.raises(ConflictError):
        await s.posts.like(MEMBER, private_id, hidden.id)


async def test_deleting_a_user_removes_their_likes_from_scores(s):
    group_id = await s.group()
    row = await s.post(group_id, caller=OWNER)
    await s.posts.like(MEMBER, group_id, row.id)

    assert await UserService(UserRepository(s.db), GroupRepository(s.db), PostStatsRepository(s.db)).delete_user("member", ADMIN)
    assert (await stats(s, row.id))["like_count"] == 0


async def test_rebuild_fixes_drifted_stats(s):
    group_id = await s.group()
    row = await s.post(group_id)
    await s.posts.like(OWNER, group_id, row.id)
    await s.db.execute("UPDATE post_stats SET like_count = 99, score = 99 WHERE post_id = ?", (row.id,))

    await PostStatsRepository(s.db).rebuild_all("2026-01-01T00:00:00Z")
    assert await stats(s, row.id) == {"like_count": 1, "comment_count": 0, "score": 1}
