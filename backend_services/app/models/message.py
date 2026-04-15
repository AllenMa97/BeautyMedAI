from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    tokens = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    metadata_info = Column(JSONB, nullable=True)  # 额外的元数据
    message_type = Column(String, default="text", nullable=False)  # text, image, file, etc.
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)  # 支持消息回复链
    rating = Column(Integer, nullable=True)  # 用户对消息的评分
    feedback = Column(Text, nullable=True)  # 用户反馈

    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_message_session_created', 'session_id', 'created_at'),
        Index('idx_message_user_created', 'user_id', 'created_at'),
    )