"""
Social groups, step 1: groups, members, owner, followers (docs/social-groups.md).
Service tests on a real temp SQLite file, plus a few API tests for the wiring
(routes, 404 vs 403 mapping, "me" routes) with the Clerk dependency overridden.
"""
import pytest
from fastapi.testclient import TestClient

from auth import AuthenticatedUser, get_authenticated_user
from database import SQLiteDatabase
from errors import ConflictError, ForbiddenError, NotFoundError
from group_permissions import Caller
from models import GroupCreate, GroupUpdate, GroupVisibility, UserRole
from repositories.group_repository import GroupRepository
from repositories.user_repository import UserRepository
from services.group_service import GroupService
from services.me_service import MeService

OWNER = Caller("owner", False)
MEMBER = Caller("member", False)
OUTSIDER = Caller("outsider", False)
ADMIN = Caller("admin", True)

PRIVATE = GroupVisibility.PRIVATE


@pytest.fixture
async def env(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "groups.db"))
    users = UserRepository(db)
    for user_id in ("owner", "member", "outsider", "admin"):
        role = [UserRole.ADMIN] if user_id == "admin" else [UserRole.STANDARD]
        await users.create(user_id, user_id.title(), f"{user_id}@x.io", role, "2026-01-01T00:00:00Z")
    groups = GroupRepository(db)
    return db, groups, users, GroupService(groups, users)


async def make(service, caller=OWNER, name="Cyclists", visibility=GroupVisibility.PUBLIC):
    return (await service.create_group(caller, GroupCreate(name=name, visibility=visibility))).group["id"]


async def test_creator_is_owner_member_and_follower(env):
    _, groups, _, service = env
    access = await service.create_group(OWNER, GroupCreate(name="Cyclists", description="Bikes"))

    assert access.group["owner_id"] == "owner"
    assert access.is_member and access.is_following
    assert access.group["member_count"] == 1 and access.group["follower_count"] == 1


async def test_group_names_are_unique_ignoring_case(env):
    *_, service = env
    await make(service, name="Cyclists")
    with pytest.raises(ConflictError):
        await make(service, caller=MEMBER, name="cyclists")


async def test_private_group_is_invisible_to_outsiders_but_not_admins(env):
    *_, service = env
    group_id = await make(service, visibility=PRIVATE)

    with pytest.raises(NotFoundError):  # 404, not 403: existence isn't leaked
        await service.get_visible(OUTSIDER, group_id)
    assert group_id not in [a.group["id"] for a in await service.list_groups(OUTSIDER)]

    assert (await service.get_visible(ADMIN, group_id)).group["id"] == group_id
    assert group_id in [a.group["id"] for a in await service.list_groups(ADMIN)]


async def test_members_can_add_people_to_a_private_group_and_they_auto_follow(env):
    _, groups, _, service = env
    group_id = await make(service, visibility=PRIVATE)

    await service.add_member(OWNER, group_id, "member")
    await service.add_member(MEMBER, group_id, "outsider")  # any member may add

    assert await groups.is_member(group_id, "outsider")
    assert await groups.is_following(group_id, "outsider")
    assert (await service.get_visible(OUTSIDER, group_id)).is_member


async def test_outsiders_cannot_join_or_add_to_a_private_group(env):
    *_, service = env
    group_id = await make(service, visibility=PRIVATE)
    with pytest.raises(NotFoundError):
        await service.join(OUTSIDER, group_id)
    with pytest.raises(NotFoundError):
        await service.add_member(OUTSIDER, group_id, "outsider")


async def test_a_follower_of_a_public_group_cannot_add_members(env):
    *_, service = env
    group_id = await make(service)
    await service.follow(OUTSIDER, group_id)
    with pytest.raises(ForbiddenError):
        await service.add_member(OUTSIDER, group_id, "member")


async def test_unfollow_keeps_membership(env):
    _, groups, _, service = env
    group_id = await make(service)
    await service.join(MEMBER, group_id)

    access = await service.unfollow(MEMBER, group_id)
    assert access.is_member and not access.is_following


async def test_leaving_or_removal_from_a_private_group_also_unfollows(env):
    _, groups, _, service = env
    group_id = await make(service, visibility=PRIVATE)
    await service.add_member(OWNER, group_id, "member")
    await service.add_member(OWNER, group_id, "outsider")

    await service.remove_member(MEMBER, group_id, "member")  # leave
    await service.remove_member(OWNER, group_id, "outsider")  # removed by the owner

    for user_id in ("member", "outsider"):
        assert not await groups.is_member(group_id, user_id)
        assert not await groups.is_following(group_id, user_id)


async def test_leaving_a_public_group_keeps_following(env):
    _, groups, _, service = env
    group_id = await make(service)
    await service.join(MEMBER, group_id)
    await service.remove_member(MEMBER, group_id, "member")
    assert await groups.is_following(group_id, "member")


async def test_only_owner_or_admin_removes_other_members(env):
    *_, service = env
    group_id = await make(service)
    await service.join(MEMBER, group_id)
    await service.join(OUTSIDER, group_id)

    with pytest.raises(ForbiddenError):
        await service.remove_member(MEMBER, group_id, "outsider")
    await service.remove_member(ADMIN, group_id, "outsider")


async def test_owner_who_leaves_leaves_the_group_ownerless_and_admin_reassigns(env):
    _, groups, _, service = env
    group_id = await make(service)
    await service.join(MEMBER, group_id)

    await service.remove_member(OWNER, group_id, "owner")
    assert (await groups.get(group_id))["owner_id"] is None

    with pytest.raises(ForbiddenError):  # no owner: only an admin can manage it
        await service.assign_owner(MEMBER, group_id, "member")
    access = await service.assign_owner(ADMIN, group_id, "member")
    assert access.group["owner_id"] == "member"


async def test_new_owner_must_be_a_member(env):
    *_, service = env
    group_id = await make(service)
    with pytest.raises(ConflictError):
        await service.assign_owner(OWNER, group_id, "outsider")


async def test_edit_and_delete_are_owner_or_admin_only(env):
    _, groups, _, service = env
    group_id = await make(service)
    await service.join(MEMBER, group_id)

    with pytest.raises(ForbiddenError):
        await service.update_group(MEMBER, group_id, GroupUpdate(description="x"))
    with pytest.raises(ForbiddenError):
        await service.delete_group(MEMBER, group_id)

    await service.update_group(ADMIN, group_id, GroupUpdate(description="by admin"))
    await service.delete_group(OWNER, group_id)
    assert await groups.get(group_id) is None


async def test_making_a_group_private_drops_non_member_followers(env):
    _, groups, _, service = env
    group_id = await make(service)
    await service.follow(OUTSIDER, group_id)

    await service.update_group(OWNER, group_id, GroupUpdate(visibility=PRIVATE))

    assert not await groups.is_following(group_id, "outsider")
    assert await groups.is_following(group_id, "owner")


async def test_admin_can_join_a_private_group(env):
    *_, service = env
    group_id = await make(service, visibility=PRIVATE)
    assert (await service.join(ADMIN, group_id)).is_member


async def test_list_filters(env):
    *_, service = env
    cyclists = await make(service, name="Cyclists")
    await make(service, caller=MEMBER, name="Runners")
    await service.follow(OWNER, cyclists)

    assert [a.group["name"] for a in await service.list_groups(OWNER, term="run")] == ["Runners"]
    assert [a.group["name"] for a in await service.list_groups(OWNER, mine=True)] == ["Cyclists"]
    assert [a.group["name"] for a in await service.list_groups(OWNER, following=True)] == ["Cyclists"]


async def test_deleting_a_user_leaves_their_groups_ownerless(env):
    _, groups, users, service = env
    group_id = await make(service)
    await users.delete("owner")
    group = await groups.get(group_id)
    assert group["owner_id"] is None and group["member_count"] == 0


async def test_links_follow_permissions(env):
    *_, service = env
    group_id = await make(service)
    owner_links = service.build_group_links(OWNER, await service.get_visible(OWNER, group_id))
    outsider_links = service.build_group_links(OUTSIDER, await service.get_visible(OUTSIDER, group_id))

    assert {"update", "delete", "assignOwner", "leave", "unfollow"} <= owner_links.keys()
    assert {"join", "follow"} <= outsider_links.keys()
    assert not {"update", "delete", "addMember", "leave"} & outsider_links.keys()


async def test_roles_are_resynced_from_clerk(env):
    _, _, users, _ = env
    me = MeService(users)
    clerk = AuthenticatedUser(id="clerk-1", name="Sam", email="sam@x.io", role_ids=[], claims={})
    row = await me.get_or_create_current_user(clerk)
    assert row["roleIds"] == ["STANDARD"]

    promoted = AuthenticatedUser(id="clerk-1", name="Sam", email="sam@x.io", role_ids=["ADMIN"], claims={})
    assert (await me.get_or_create_current_user(promoted))["roleIds"] == ["ADMIN"]


async def test_clerk_roles_match_case_insensitively(env):
    # Clerk metadata is free text: `"roles": ["admin"]` must make an admin, not a standard user.
    _, _, users, _ = env
    me = MeService(users)
    for index, claim in enumerate(["admin", "Admin", " ADMIN "]):
        clerk = AuthenticatedUser(
            id=f"clerk-{index}", name="Wil", email=f"w{index}@x.io", role_ids=[claim], claims={}
        )
        assert (await me.get_or_create_current_user(clerk))["roleIds"] == ["ADMIN"]

    # and an existing standard user is upgraded on their next request
    clerk = AuthenticatedUser(id="clerk-9", name="Wil", email="w9@x.io", role_ids=[], claims={})
    assert (await me.get_or_create_current_user(clerk))["roleIds"] == ["STANDARD"]
    clerk = AuthenticatedUser(id="clerk-9", name="Wil", email="w9@x.io", role_ids=["admin"], claims={})
    assert (await me.get_or_create_current_user(clerk))["roleIds"] == ["ADMIN"]


# --- API wiring


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_MODE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "api.db"))
    from main import app

    who = {"user": AuthenticatedUser(id="clerk-a", name="Alice", email="a@x.io", role_ids=[], claims={})}
    app.dependency_overrides[get_authenticated_user] = lambda: who["user"]
    yield TestClient(app), who
    app.dependency_overrides.clear()


def test_api_create_hide_and_join(client):
    http, who = client
    created = http.post("/api/groups", json={"name": "Secret", "visibility": "PRIVATE"})
    assert created.status_code == 201
    group = created.json()["_data"]["group"]
    assert group["isOwner"] and group["links"]["delete"]["href"] == f"/api/groups/{group['id']}"

    who["user"] = AuthenticatedUser(id="clerk-b", name="Bob", email="b@x.io", role_ids=[], claims={})
    assert http.get(f"/api/groups/{group['id']}").status_code == 404
    assert http.put(f"/api/groups/{group['id']}/members/me").status_code == 404

    public = http.post("/api/groups", json={"name": "Open"}).json()["_data"]["group"]
    who["user"] = AuthenticatedUser(id="clerk-a", name="Alice", email="a@x.io", role_ids=[], claims={})
    joined = http.put(f"/api/groups/{public['id']}/members/me")
    assert joined.status_code == 200 and joined.json()["_data"]["group"]["isFollowing"]
    assert http.delete(f"/api/groups/{public['id']}").status_code == 403
    assert http.delete(f"/api/groups/{public['id']}/followers/me").json()["_data"]["group"]["isFollowing"] is False
