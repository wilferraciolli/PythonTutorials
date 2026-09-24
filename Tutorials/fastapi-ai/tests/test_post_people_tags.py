"""
Tagging people in posts (docs/social-groups.md "Tagging people"): the post
carries taggedUserIds, the response metadata resolves them to full names.
"""
import pytest
from pydantic import ValidationError

from core.common.errors import ForbiddenError, InvalidInputError
from groups.posts.schemas import PostCreateRequest, PostUpdateRequest
from timeline.timeline_repository import TimelineRepository
from timeline.enums import TimelineType
from timeline.timeline_service import TimelineService
from social import MEMBER, OWNER, make_social


@pytest.fixture
async def s(tmp_path):
    return await make_social(tmp_path)


async def tagged_post(s, group_id, people):
    _, row = await s.posts.create_post(
        MEMBER, group_id, PostCreateRequest(title="Ride", body="Sunday", taggedUserIds=people)
    )
    return row


async def test_a_post_carries_ids_and_the_metadata_names_them(s):
    group_id = await s.group()
    row = await tagged_post(s, group_id, ["owner", "outsider"])

    access, row = await s.posts.get_post(MEMBER, group_id, row.id)
    response = s.posts.build_post_response(MEMBER, access, row)

    assert response.data["post"].taggedUserIds == ["owner", "outsider"]
    assert [value.model_dump() for value in response.metadata.taggedUserIds.values] == [
        {"id": "owner", "value": "Owner"},
        {"id": "outsider", "value": "Outsider"},
    ]


async def test_duplicates_are_dropped_and_order_kept(s):
    group_id = await s.group()
    row = await tagged_post(s, group_id, ["outsider", "owner", "outsider"])
    assert [p.user_id for p in row.tagged_people] == ["outsider", "owner"]


async def test_unknown_users_are_rejected_and_nothing_is_saved(s):
    group_id = await s.group()
    with pytest.raises(InvalidInputError, match="ghost"):
        await tagged_post(s, group_id, ["owner", "ghost"])
    _, rows = await s.posts.list_posts(MEMBER, group_id)
    assert rows == []


def test_at_most_twenty_people():
    with pytest.raises(ValidationError):
        PostCreateRequest(title="t", body="b", taggedUserIds=[str(i) for i in range(21)])


async def test_the_author_replaces_or_clears_the_list_and_none_leaves_it(s):
    group_id = await s.group()
    row = await tagged_post(s, group_id, ["owner"])

    _, row = await s.posts.update_post(MEMBER, group_id, row.id, PostUpdateRequest(title="Ride!"))
    assert [p.user_id for p in row.tagged_people] == ["owner"]

    _, row = await s.posts.update_post(MEMBER, group_id, row.id, PostUpdateRequest(taggedUserIds=["outsider"]))
    assert [p.user_id for p in row.tagged_people] == ["outsider"]

    _, row = await s.posts.update_post(MEMBER, group_id, row.id, PostUpdateRequest(taggedUserIds=[]))
    assert row.tagged_people == []


async def test_only_the_author_changes_who_is_tagged(s):
    group_id = await s.group()
    row = await tagged_post(s, group_id, ["owner"])
    with pytest.raises(ForbiddenError):
        await s.posts.update_post(OWNER, group_id, row.id, PostUpdateRequest(taggedUserIds=[]))


async def test_a_list_names_everyone_tagged_across_its_posts_once(s):
    group_id = await s.group()
    await tagged_post(s, group_id, ["owner"])
    await tagged_post(s, group_id, ["owner", "outsider"])

    access, rows = await s.posts.list_posts(MEMBER, group_id)
    response = s.posts.build_posts_response(MEMBER, access, rows)
    assert [value.model_dump() for value in response.metadata.taggedUserIds.values] == [
        {"id": "owner", "value": "Owner"},
        {"id": "outsider", "value": "Outsider"},
    ]


async def test_the_timeline_carries_tags_too(s):
    group_id = await s.group()
    await tagged_post(s, group_id, ["outsider"])

    timeline = TimelineService(TimelineRepository(s.db), s.posts)
    rows = await timeline.list_posts(MEMBER)
    mine = next(r for r in rows if r.group_id == group_id)
    assert [p.user_id for p in mine.tagged_people] == ["outsider"]

    response = await timeline.build_response(MEMBER, TimelineType.ALL, rows)
    assert {"id": "outsider", "value": "Outsider"} in [value.model_dump() for value in response.metadata.taggedUserIds.values]


async def test_a_deleted_user_drops_out_of_the_tags(s):
    group_id = await s.group()
    row = await tagged_post(s, group_id, ["outsider"])
    await s.db.execute("DELETE FROM users WHERE id = ?", ("outsider",))

    _, row = await s.posts.get_post(MEMBER, group_id, row.id)
    assert row.tagged_people == []
