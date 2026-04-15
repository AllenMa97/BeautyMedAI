from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class User(Base):
    __tablename__ = "users"

    # 使用UUID作为主键，更适合分布式系统
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    role = Column(String, default="user", nullable=False)  # user, admin, superuser
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    avatar_url = Column(String, nullable=True)  # 头像URL
    bio = Column(Text, nullable=True)  # 个人简介
    metadata_info = Column(JSONB, nullable=True)  # 额外的元数据
    failed_login_attempts = Column(Integer, default=0, nullable=False)  # 登录失败次数
    locked_until = Column(DateTime(timezone=True), nullable=True)  # 账户锁定至