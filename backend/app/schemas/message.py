from datetime import datetime, timezone

from pydantic import BaseModel, field_validator


class MessageCreate(BaseModel):
    content: str
    desk_id: int | None = None


class MessageResponse(BaseModel):
    id: int
    content: str
    sender_id: int | None
    room_id: int
    desk_id: int | None = None
    created_at: datetime
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