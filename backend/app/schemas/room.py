from pydantic import BaseModel


class RoomCreate(BaseModel):
    name: str
    description: str | None = None
    is_private: bool = False
    ai_enabled: bool = True
    organization_id: int | None = None

class RoomUpdate(BaseModel):
    ai_enabled: bool


class RoomResponse(BaseModel):

    id: int

    name: str

    description: str | None

    is_private: bool

    owner_id: int

    is_member: bool

    role: str | None = None

    ai_enabled: bool = True

    class Config:
        from_attributes = True

class RoomMemberResponse(BaseModel):

    user_id: int

    username: str

    role: str