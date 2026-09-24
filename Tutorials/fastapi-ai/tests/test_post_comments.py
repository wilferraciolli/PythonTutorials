"""Social groups: comments and replies on posts (docs/social-groups.md)."""
import pytest
from social import ADMIN, MEMBER, OUTSIDER, OWNER, make_social

from core.common.errors import ConflictError, ForbiddenError, NotFoundError
from groups.enums import GroupVisibility
from groups.posts.comments.schemas import CommentCreateRequest, CommentUpdateRequest


@pytest.fixture
async def s(tmp_path):
    return await make_social(tmp_path)


async def test_comments_and_replies_are_threaded_oldest_first(s):
    group_id = await s.group()
    row = await s.post(group_id)

    top = await s.comment(group_id, row.id, caller=OWNER, body="Top")
    reply = await s.comment(group_id, row.id, body="Reply", parent=top.id)
    await s.comment(group_id, row.id, caller=OWNER, body="Deeper", parent=reply.id)

    _, _, listed = await s.comments.list_comments(MEMBER, group_id, row.id)
    assert [(c.body, c.parent_comment_id) for c in listed] == [
        ("Top", None),
        ("Reply", top.id),
        ("Deeper", reply.id),
    ]
    assert (await s.posts.get_post(MEMBER, group_id, row.id))[1].comment_count == 3


async def test_private_group_comments_are_hidden_from_outsiders(s):
    group_id = await s.group(GroupVisibility.PRIVATE, name="Secret")
    row = await s.post(group_id)
    with pytest.raises(NotFoundError):
        await s.comments.list_comments(OUTSIDER, group_id, row.id)


async def test_reply_parent_must_be_on_the_same_post_and_not_deleted(s):
    group_id = await s.group()
    a, b = await s.post(group_id), await s.post(group_id)
    on_a = await s.comment(group_id, a.id, body="on a")

    with pytest.raises(NotFoundError):
        await s.comment(group_id, b.id, parent=on_a.id)

    await s.comments.delete_comment(MEMBER, group_id, a.id, on_a.id)
    with pytest.raises(ConflictError):
        await s.comment(group_id, a.id, parent=on_a.id)


async def test_deleted_comment_keeps_its_replies_and_stops_counting(s):
    group_id = await s.group()
    row = await s.post(group_id)
    top = await s.comment(group_id, row.id, caller=OWNER, body="Top")
    await s.comment(group_id, row.id, body="Reply", parent=top.id)

    await s.comments.delete_comment(ADMIN, group_id, row.id, top.id)

    access, post_row, listed = await s.comments.list_comments(MEMBER, group_id, row.id)
    shown = [s.comments.to_dto(MEMBER, access, post_row, c) for c in listed]
    assert shown[0].isDeleted and shown[0].body == "[deleted]" and shown[0].links == {}
    assert shown[1].body == "Reply" and shown[1].parentCommentId == top.id
    assert post_row.comment_count == 1 and post_row.score == 2


async def test_delete_by_author_owner_or_admin(s):
    group_id = await s.group()
    await s.groups.join(OUTSIDER, group_id)
    row = await s.post(group_id)
    comments = [await s.comment(group_id, row.id) for _ in range(3)]

    with pytest.raises(ForbiddenError):
        await s.comments.delete_comment(OUTSIDER, group_id, row.id, comments[0].id)
    await s.comments.delete_comment(MEMBER, group_id, row.id, comments[0].id)
    await s.comments.delete_comment(OWNER, group_id, row.id, comments[1].id)
    await s.comments.delete_comment(ADMIN, group_id, row.id, comments[2].id)


async def test_comment_edit_author_only_and_non_members_cannot_comment(s):
    group_id = await s.group()
    row = await s.post(group_id)
    comment = await s.comment(group_id, row.id, body="Hi")

    with pytest.raises(ForbiddenError):
        await s.comments.update_comment(OWNER, group_id, row.id, comment.id, CommentUpdateRequest(body="x"))
    with pytest.raises(ForbiddenError):
        await s.comment(group_id, row.id, caller=OUTSIDER)

    _, _, edited = await s.comments.update_comment(
        MEMBER, group_id, row.id, comment.id, CommentUpdateRequest(body="Hello")
    )
    assert edited.body == "Hello"


async def test_no_comments_on_a_deleted_post(s):
    group_id = await s.group()
    row = await s.post(group_id)
    await s.posts.delete_post(MEMBER, group_id, row.id)
    with pytest.raises(ConflictError):
        await s.comments.create_comment(MEMBER, group_id, row.id, CommentCreateRequest(body="x"))
