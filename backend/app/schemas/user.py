from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password must be 8-128 characters"
    )


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_system_admin: bool = False

    class Config:
        from_attributes = True