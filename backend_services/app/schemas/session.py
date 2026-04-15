from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class SessionBase(BaseModel):
    title: Optional[str] = None
    metadata_info: Optional[Dict] = None


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    metadata_info: Optional[Dict] = None
    is_active: Optional[bool] = None


class SessionInDB(SessionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


class Session(SessionInDB):
    pass


class MessageBase(BaseModel):
    session_id: str
    role: str
    content: str
    tokens: Optional[int] = 0
    metadata_info: Optional[str] = None


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    metadata_info: Optional[str] = None


class MessageInDB(MessageBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Message(MessageInDB):
    pass