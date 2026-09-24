from pydantic import BaseModel

from core.common.api_response import ApiResponse
from core.common.base_dto import NoMetadata
from groups.posts.schemas import PostIndexCountsDTO


# --- DTO: what the application service returns ------------------------------

class AdminToolDTO(BaseModel):
    """One thing an admin can run; its id is also its `_metaLinks` name."""
    id: str
    name: str
    description: str


class AdminDTO(BaseModel):
    """The admin hub: the tools an admin can run."""
    tools: list[AdminToolDTO]


class PostStatsRebuildDTO(BaseModel):
    """How many posts had their stats recomputed."""
    rebuilt: int


class PostSearchReindexDTO(BaseModel):
    """How many posts and comments were embedded for AI search."""
    indexed: PostIndexCountsDTO


# --- Response: the envelopes the service builds -----------------------------

AdminResponse = ApiResponse[AdminDTO, NoMetadata]
PostStatsRebuildResponse = ApiResponse[PostStatsRebuildDTO, NoMetadata]
PostSearchReindexResponse = ApiResponse[PostSearchReindexDTO, NoMetadata]
