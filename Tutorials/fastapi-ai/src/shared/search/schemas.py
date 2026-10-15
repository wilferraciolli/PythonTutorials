from pydantic import BaseModel


class ReindexDTO(BaseModel):
    """The result of an AI search backfill: how many items were embedded."""
    indexed: int
