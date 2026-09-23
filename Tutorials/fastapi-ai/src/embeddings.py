from ai import AI

DEFAULT_EMBEDDING_MODEL = "@cf/baai/bge-base-en-v1.5"

# bge models read ~512 tokens; long messages are truncated for now
# (chunking is a later phase — see docs/ai-search-plan.md).
MAX_EMBED_CHARS = 2000

BATCH_SIZE = 50


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
