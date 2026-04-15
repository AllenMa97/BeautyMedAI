from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    id: str
    is_active: bool
    is_superuser: bool
    role: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDB):
    pass


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None