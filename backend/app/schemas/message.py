from datetime import datetime, timezone

from pydantic import BaseModel, field_validator


class MessageCreate(BaseModel):
    content: str
    channel_id: int | None = None
    parent_id: int | None = None

class MessageUpdate(BaseModel):
    content: str

class MessageMove(BaseModel):
    channel_id: int

class MessageResponse(BaseModel):
    id: int
    content: str
    sender_id: int | None
    workspace_id: int
    channel_id: int | None = None
    parent_id: int | None = None
    created_at: datetime
    edited_at: datetime | None = None
    username: str | None = None
    extra_data: dict[str, object] | None = None

    @field_validator("created_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime):
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    class Config:
        from_attributes = True