from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChannelBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False

class ChannelCreate(ChannelBase):
    workspace_id: int

class ChannelSchema(ChannelBase):
    id: int
    workspace_id: int
    created_at: datetime

    class Config:
        from_attributes = True
