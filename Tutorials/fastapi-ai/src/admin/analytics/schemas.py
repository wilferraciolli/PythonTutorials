from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from core.common.api_response import ApiResponse
from core.common.base_dto import FieldMetadata


# --- DTO: what the application service returns ------------------------------

class EngagementCountsDTO(BaseModel):
    """How many of each thing were created."""
    groups: int
    posts: int
    comments: int
    likes: int


class EngagementDayDTO(BaseModel):
    """One UTC day's counts."""
    date: date
    groups: int
    posts: int
    comments: int
    likes: int


class EngagementDTO(BaseModel):
    """
    Activity over the last `days` days (today included, UTC), per day and in
    total, with the totals of the `days` before for comparison.
    """
    model_config = ConfigDict(populate_by_name=True)

    # `from` is a Python keyword, hence the alias.
    from_: date = Field(alias="from")
    to: date
    days: int
    totals: EngagementCountsDTO
    previousTotals: EngagementCountsDTO
    daily: list[EngagementDayDTO]


class EngagementMetadata(BaseModel):
    """The metrics with their labels, and the allowed `days`."""
    metric: FieldMetadata
    days: FieldMetadata


# --- Response: the envelope the service builds ------------------------------

EngagementResponse = ApiResponse[EngagementDTO, EngagementMetadata]
