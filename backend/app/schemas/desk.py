from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DeskBase(BaseModel):
    name: str
    description: Optional[str] = None

class DeskCreate(DeskBase):
    room_id: int

class DeskSchema(DeskBase):
    id: int
    room_id: int
    created_at: datetime

    class Config:
        from_attributes = True
