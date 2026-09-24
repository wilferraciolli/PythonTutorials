from typing import Awaitable, Callable

from fastapi import Request

from core.ai.ai import AI, get_ai
from core.config.config import get_config

DEFAULT_EMBEDDING_MODEL = "@cf/baai/bge-base-en-v1.5"

# bge models read ~512 tokens; long messages are truncated for now
# (chunking is a later phase — see docs/ai-search-plan.md).
MAX_EMBED_CHARS = 2000

BATCH_SIZE = 50

EmbedFn = Callable[[list[str]], Awaitable[list[list[float]]]]


async def embed(ai: AI, model: str, texts: list[str]) -> list[list[float]]:
    """Embed texts with a Workers AI embedding model; returns one vector per text, in order."""
    vectors: list[list[float]] = []

    for start in range(0, len(texts), BATCH_SIZE):
        batch = [text[:MAX_EMBED_CHARS] for text in texts[start : start + BATCH_SIZE]]
        result = await ai.run(model, {"text": batch})
        data = result.get("data")
        if not isinstance(data, list) or len(data) != len(batch):
            raise RuntimeError(f"unexpected embedding response shape: {str(result)[:200]}")
        vectors.extend([[float(value) for value in vector] for vector in data])

    return vectors


def get_embedder(request: Request) -> tuple[EmbedFn, str]:
    """(embed function, model name) — embeddings always come from Workers AI, whichever provider chats."""
    model = get_config(request, "CF_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL) or DEFAULT_EMBEDDING_MODEL

    async def embed_texts(texts: list[str]) -> list[list[float]]:
        # Built on first use, so routes that never embed (todo CRUD without
        # Workers AI credentials) don't fail just for constructing the service.
        return await embed(get_ai(request, "cloudflare"), model, texts)

    return embed_texts, model
