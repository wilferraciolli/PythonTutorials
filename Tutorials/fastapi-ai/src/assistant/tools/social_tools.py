from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from assistant.tools.tool import Tool
from core.common.serializers import format_utc_datetime
from core.security.authorization import Caller
from groups.posts.post_search_service import PostSearchService
from groups.posts.post_service import display_author
from groups.social_query_repository import SocialQueryRepository

MAX_LIST = 25

_COMMON = {
    "group": {
        "type": "string",
        "description": "Only this group, by name (case-insensitive). Use my_groups to see group names.",
    },
    "mine": {"type": "boolean", "description": "true = only ones the user wrote themselves."},
    "created_from": {"type": "string", "description": "Only ones created on/after this date (YYYY-MM-DD)."},
    "created_to": {"type": "string", "description": "Only ones created on/before this date (YYYY-MM-DD)."},
}


def _day(value: str) -> str:
    day = date.fromisoformat(value)
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc).isoformat()


def build_social_tools(
    caller: Caller, queries: SocialQueryRepository, search: Optional[PostSearchService] = None
) -> List[Tool]:
    """
    Tools over groups, posts and comments. Unlike todos these are shared, so
    every tool runs as `caller` (the path user, with their system role) and
    every query applies the API's visibility rule: the assistant can only
    count, list or find what the caller could open in the app.
    """

    async def _filters(user_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if user_id != caller.user_id:  # tools are built per request for exactly this user
            return {"error": "not allowed"}
        filters: Dict[str, Any] = {"group_id": None, "author_id": None, "created_from": None, "created_to": None}
        if args.get("group"):
            group = await queries.find_visible_group(caller.user_id, caller.is_admin, str(args["group"]).strip())
            if group is None:
                return {"error": f"no group called {args['group']!r} that you can see; call my_groups"}
            filters["group_id"] = group.id
        if args.get("mine") is True:
            filters["author_id"] = caller.user_id
        try:
            if args.get("created_from"):
                filters["created_from"] = _day(args["created_from"])
            if args.get("created_to"):  # inclusive: up to the start of the next day
                filters["created_to"] = (
                    datetime.fromisoformat(_day(args["created_to"])) + timedelta(days=1)
                ).isoformat()
        except ValueError:
            return {"error": "dates must be YYYY-MM-DD"}
        return filters

    async def count_posts(user_id: str, args: Dict[str, Any]) -> Any:
        filters = await _filters(user_id, args)
        if "error" in filters:
            return filters
        return {"count": await queries.count_posts(caller.user_id, caller.is_admin, **filters)}

    async def list_posts(user_id: str, args: Dict[str, Any]) -> Any:
        filters = await _filters(user_id, args)
        if "error" in filters:
            return filters
        sort = args.get("sort") or "newest"
        if sort not in ("newest", "popular"):
            return {"error": "sort must be newest or popular"}
        limit = max(1, min(int(args.get("limit") or 10), MAX_LIST))
        posts = await queries.list_posts(caller.user_id, caller.is_admin, sort == "popular", limit, **filters)
        return {
            "posts": [
                {
                    "title": post.title,
                    "group": post.group_name,
                    "author": display_author(None, post.author_id, post.author_name),
                    "created_date": format_utc_datetime(post.created_date),
                    "likes": post.like_count,
                    "comments": post.comment_count,
                    "score": post.score,
                }
                for post in posts
            ]
        }

    async def count_comments(user_id: str, args: Dict[str, Any]) -> Any:
        filters = await _filters(user_id, args)
        if "error" in filters:
            return filters
        return {"count": await queries.count_comments(caller.user_id, caller.is_admin, **filters)}

    async def my_groups(user_id: str, args: Dict[str, Any]) -> Any:
        if user_id != caller.user_id:
            return {"error": "not allowed"}
        groups = await queries.my_groups(caller.user_id, caller.is_admin)
        return {
            "groups": [
                {
                    "name": group.name,
                    "visibility": group.visibility.value,
                    "owner": group.is_owner,
                    "member": group.is_member,
                    "following": group.is_following,
                    "members": group.member_count,
                    "posts": group.post_count,
                    "last_post_date": format_utc_datetime(group.last_post_date) if group.last_post_date else None,
                }
                for group in groups
            ]
        }

    tools = [
        Tool(
            name="count_posts",
            description=(
                "Count posts in the social groups the user can see. Filters: group, mine (written by "
                "the user), created date range. For 'this month' etc. call date_range first."
            ),
            parameters={"type": "object", "properties": dict(_COMMON)},
            handler=count_posts,
        ),
        Tool(
            name="list_posts",
            description=(
                "List posts in groups the user can see (title, group, author, date, likes, comments, "
                "score). Same filters as count_posts; sort='popular' for most liked/discussed "
                "(comment = 2 points, like = 1), else newest first."
            ),
            parameters={
                "type": "object",
                "properties": {
                    **_COMMON,
                    "sort": {"type": "string", "enum": ["newest", "popular"]},
                    "limit": {"type": "integer", "description": f"Max posts (default 10, max {MAX_LIST})."},
                },
            },
            handler=list_posts,
        ),
        Tool(
            name="count_comments",
            description=(
                "Count comments and replies in groups the user can see. Filters: group, mine, created "
                "date range."
            ),
            parameters={"type": "object", "properties": dict(_COMMON)},
            handler=count_comments,
        ),
        Tool(
            name="my_groups",
            description=(
                "The groups the user owns, is a member of or follows, with member and post counts and "
                "the date of the latest post (for 'which of my groups is most active')."
            ),
            parameters={"type": "object", "properties": {}},
            handler=my_groups,
        ),
    ]

    if search:

        async def search_posts(user_id: str, args: Dict[str, Any]) -> Any:
            if user_id != caller.user_id:
                return {"error": "not allowed"}
            query = str(args.get("query") or "").strip()
            if not query:
                return {"error": "query is required"}
            group_id = None
            if args.get("group"):
                group = await queries.find_visible_group(caller.user_id, caller.is_admin, str(args["group"]).strip())
                if group is None:
                    return {"error": f"no group called {args['group']!r} that you can see; call my_groups"}
                group_id = group.id
            matches = await search.search(caller, query, group_id, int(args.get("limit") or 5))
            return {
                "matches": [
                    match.model_dump(
                        mode="json",
                        include={"title", "group", "author", "created_date", "likes", "comments",
                                 "snippet", "matching_comment"},
                    )
                    for match in matches
                ]
            }

        tools.append(
            Tool(
                name="search_posts",
                description=(
                    "Find posts (and what people said in their comments) by what they are ABOUT, e.g. "
                    "'what did people say about the bike lanes'. Only searches groups the user can see. "
                    "Use count_posts / list_posts for counts, dates, authors and popularity."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "What the posts are about."},
                        "group": _COMMON["group"],
                        "limit": {"type": "integer", "description": "Max posts (default 5)."},
                    },
                    "required": ["query"],
                },
                handler=search_posts,
            )
        )

    return tools
