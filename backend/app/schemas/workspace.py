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

    can_create_private_channel: bool = True

    class Config:
        from_attributes = True

class WorkspaceMemberResponse(BaseModel):

    user_id: int

    username: str
    
    email: str

    role: str

class RoleUpdate(BaseModel):
    role: str