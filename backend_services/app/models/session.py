from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=True)
    metadata_info = Column(JSONB, nullable=True)  # 存储会话元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 会话过期时间
    is_active = Column(Boolean, default=True, nullable=False)
    session_type = Column(String, default="chat", nullable=False)  # chat, rag_search, etc.
    tags = Column(JSONB, nullable=True)  # 会话标签
    summary = Column(Text, nullable=True)  # 会话摘要

    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_session_user_created', 'user_id', 'created_at'),
        Index('idx_session_active', 'is_active'),
    )