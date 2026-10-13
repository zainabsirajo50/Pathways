"""Explicit public response contracts; never serialize catalog ORM objects wholesale."""
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class DestinationCategory(str, Enum):
    waterfall = 'waterfall'
    lake = 'lake'
    gorge = 'gorge'
    forest = 'forest'
    river = 'river'
    coast = 'coast'
    mountain = 'mountain'
    garden = 'garden'
    park = 'park'


class PublicModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class DestinationResponse(PublicModel):
    slug: str
    name: str
    category: DestinationCategory
    region: str
    city: str | None
    state: str
    description: str | None
    official_website: str | None
    access_notes: str | None
    latitude: float | None = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(ge=-180, le=180, allow_inf_nan=False)


class DestinationPage(PublicModel):
    items: list[DestinationResponse]
    total: int
    page: int
    page_size: int


class CategoryResponse(PublicModel):
    categories: list[DestinationCategory]


class HealthResponse(PublicModel):
    status: str
