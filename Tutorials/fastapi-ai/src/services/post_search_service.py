from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from database import Database
from group_permissions import Caller
from repositories.social_query_repository import SocialQueryRepository
from resource_vector_store import ResourceVectorStore

EmbedFn = Callable[[List[str]], Awaitable[List[List[float]]]]

DEFAULT_LIMIT = 5
MAX_LIMIT = 20
RRF_K = 60  # same reciprocal-rank-fusion constant as chat and todo search
SNIPPET_CHARS = 240


def post_text(row: Dict[str, Any]) -> str:
    return f"{row['title']}\n{row.get('body') or ''}".strip()


def _snippet(text: str) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= SNIPPET_CHARS else text[: SNIPPET_CHARS - 1] + "…"


class PostSearchService:
    """
    Search posts and comments by meaning plus keyword, merged with reciprocal
    rank fusion: the same recipe as chat and todo search.

    The difference is **who may see what**. Posts are shared, so vectors are
    scoped by group id (resource_embeddings.user_id holds the group id) and a
    search only looks inside the groups the caller can see right now. A
    comment hit is reported as its post. Counting and filtering by group,
    author or date are plain queries (assistant/social_tools.py).
    """

    def __init__(self, db: Database, embed: EmbedFn, embedding_model: str) -> None:
        self.queries = SocialQueryRepository(db)
        self.posts = ResourceVectorStore(db, "post")
        self.comments = ResourceVectorStore(db, "comment")
        self.embed = embed
        self.embedding_model = embedding_model

    # --- keeping the index up to date (callers treat failures as best effort)

    async def index_post(self, row: Dict[str, Any]) -> None:
        [vector] = await self.embed([post_text(row)])
        await self.posts.upsert(row["id"], row["group_id"], self.embedding_model, vector, _now())

    async def index_comment(self, comment_id: str, body: str, group_id: str) -> None:
        [vector] = await self.embed([body])
        await self.comments.upsert(comment_id, group_id, self.embedding_model, vector, _now())

    async def remove_post(self, post_id: str) -> None:
        await self.posts.delete(post_id)

    async def remove_comment(self, comment_id: str) -> None:
        await self.comments.delete(comment_id)

    async def reindex_missing(self) -> Dict[str, int]:
        """Backfill: embed every live post and comment that has no vector yet (e.g. the News seed)."""
        indexed_posts, indexed_comments = await self.posts.all_ids(), await self.comments.all_ids()
        posts = [row for row in await self.queries.live_posts() if row["id"] not in indexed_posts]
        comments = [row for row in await self.queries.live_comments() if row["id"] not in indexed_comments]

        now = _now()
        if posts:
            for row, vector in zip(posts, await self.embed([post_text(row) for row in posts])):
                await self.posts.upsert(row["id"], row["group_id"], self.embedding_model, vector, now)
        if comments:
            for row, vector in zip(comments, await self.embed([row["body"] for row in comments])):
                await self.comments.upsert(row["id"], row["group_id"], self.embedding_model, vector, now)
        return {"posts": len(posts), "comments": len(comments)}

    # --- search

    async def search(
        self, caller: Caller, query: str, group_id: Optional[str] = None, limit: int = DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        query = query.strip()
        if not query:
            return []
        limit = max(1, min(limit, MAX_LIMIT))
        pool = limit * 3

        # Only the groups the caller can see (or the one they asked about, if they can see it).
        scopes = await self.queries.visible_group_ids(caller.id, caller.is_admin)
        if group_id:
            scopes = [scope for scope in scopes if scope == group_id]
        if not scopes:
            return []

        [vector] = await self.embed([query])
        post_hits = await self.posts.query_scopes(scopes, vector, pool)
        comment_hits = await self.comments.query_scopes(scopes, vector, pool)
        keyword_posts = await self.queries.keyword_posts(caller.id, caller.is_admin, query, group_id, pool)
        keyword_comments = await self.queries.keyword_comments(caller.id, caller.is_admin, query, group_id, pool)

        comment_ids = [cid for cid, _ in comment_hits] + [row["id"] for row in keyword_comments]
        comments = {
            row["id"]: row for row in await self.queries.comments_by_ids(caller.id, caller.is_admin, comment_ids)
        }

        # One ranked list per signal, at post level, so a post with many comments
        # isn't boosted just for having them. Meaning: a post's similarity is the
        # best of its own vector and its comments' vectors.
        similarity: Dict[str, float] = {}
        matched_comment: Dict[str, str] = {}
        for post_id, score in post_hits:
            similarity[post_id] = max(similarity.get(post_id, score), score)
        for comment_id, score in comment_hits:
            comment = comments.get(comment_id)
            if comment is None:  # deleted, or in a group the caller can't see
                continue
            post_id = comment["post_id"]
            if score > similarity.get(post_id, float("-inf")):
                similarity[post_id] = score
                matched_comment[post_id] = comment["body"]
        meaning_ranked = sorted(similarity, key=lambda pid: similarity[pid], reverse=True)

        # Keyword: posts whose text matches, then posts with a matching comment.
        keyword_ranked: List[str] = []
        for row in keyword_posts:
            if row["id"] not in keyword_ranked:
                keyword_ranked.append(row["id"])
        for row in keyword_comments:
            if row["id"] in comments and row["post_id"] not in keyword_ranked:
                keyword_ranked.append(row["post_id"])
                matched_comment.setdefault(row["post_id"], row["body"])
        keyword_ids = set(keyword_ranked)

        scores: Dict[str, float] = {}
        for ranked in (meaning_ranked, keyword_ranked):
            for rank, post_id in enumerate(ranked):
                scores[post_id] = scores.get(post_id, 0.0) + 1 / (RRF_K + rank + 1)

        # Re-read the posts through the visibility filter: a vector is never trusted on its own.
        rows = {
            row["id"]: row
            for row in await self.queries.posts_by_ids(caller.id, caller.is_admin, list(scores))
        }
        ranked_ids = [pid for pid in sorted(scores, key=lambda pid: scores[pid], reverse=True) if pid in rows]
        return [
            {
                "id": post_id,
                "group_id": rows[post_id]["group_id"],
                "group": rows[post_id]["group_name"],
                "title": rows[post_id]["title"],
                "author": rows[post_id]["author_name"] or ("System" if rows[post_id]["author_id"] is None else None),
                "created_date": rows[post_id]["created_date"],
                "likes": rows[post_id]["like_count"],
                "comments": rows[post_id]["comment_count"],
                "snippet": _snippet(rows[post_id]["body"]),
                "matching_comment": _snippet(matched_comment[post_id]) if post_id in matched_comment else None,
                "keywordMatch": post_id in keyword_ids,
                "score": round(scores[post_id], 6),
            }
            for post_id in ranked_ids[:limit]
        ]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
