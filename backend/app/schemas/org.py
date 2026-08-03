from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OrgBase(BaseModel):
    name: str

class OrgCreate(OrgBase):
    pass

class OrganizationSchema(OrgBase):
    id: int
    created_by: int
    created_at: datetime
    allow_private_channels: bool
    allow_public_workspaces: bool

    class Config:
        from_attributes = True

class OrgUpdate(BaseModel):
    name: Optional[str] = None
    allow_private_channels: Optional[bool] = None
    allow_public_workspaces: Optional[bool] = None

class OrgMemberBase(BaseModel):
    user_id: int
    role: str

class OrgMemberAdd(OrgMemberBase):
    pass

class OrgMemberSchema(OrgMemberBase):
    org_id: int
    created_at: datetime
    username: Optional[str] = None

    class Config:
        from_attributes = True
