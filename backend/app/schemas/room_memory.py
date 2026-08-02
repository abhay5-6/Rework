from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone


class RoomMemoryCreate(
    BaseModel
):

    content: str

    memory_type: str = "note"

    source_type: str = "manual"

    source_id: int | None = None

    domain: str = "general"

    importance_score: int = 1

    tags: list[str] = Field(default_factory=list)


class RoomMemoryUpdate(
    BaseModel
):

    content: str | None = None

    importance_score: int | None = None

    tags: list[str] | None = None


class RoomMemoryResponse(
    BaseModel
):

    id: int

    room_id: int

    created_by: int

    content: str

    memory_type: str

    source_type: str

    source_id: int | None

    domain: str

    importance_score: int

    confidence_score: float

    tags: list[str]

    last_reinforced_at: datetime

    creator_username: str | None = None

    created_at: datetime

    @field_validator("created_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime):
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    class Config:

        from_attributes = True


class SearchMessage(
    BaseModel
):

    type: str

    id: int

    content: str

    created_at: datetime

    score: float

    @field_validator("created_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime):
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class SearchResult(
    BaseModel
):

    messages: list[
        SearchMessage
    ]

    memories: list[
        RoomMemoryResponse
    ]
