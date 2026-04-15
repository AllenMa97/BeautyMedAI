from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class ResourceCategory(Base):
    __tablename__ = "resource_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False, unique=True)  # 分类名称，如 "datasets", "models", "checkpoints"
    description = Column(Text, nullable=True)  # 分类描述
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ResourceFile(Base):
    __tablename__ = "resource_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)  # 文件名
    original_name = Column(String, nullable=False)  # 原始文件名
    category_id = Column(UUID(as_uuid=True), ForeignKey("resource_categories.id"), nullable=False, index=True)
    file_path = Column(String, nullable=True)  # 本地存储路径
    storage_url = Column(String, nullable=True)  # 外部存储URL (如S3, OSS等)
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    mime_type = Column(String, nullable=True)  # MIME类型
    checksum_md5 = Column(String, nullable=True)  # MD5校验和
    checksum_sha256 = Column(String, nullable=True)  # SHA256校验和
    version = Column(String, default="1.0.0", nullable=False)  # 版本号
    description = Column(Text, nullable=True)  # 文件描述
    tags = Column(JSONB, nullable=True)  # 标签
    metadata_info = Column(JSONB, nullable=True)  # 额外元数据
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)  # 上传用户
    is_public = Column(Boolean, default=False, nullable=False)  # 是否公开
    is_active = Column(Boolean, default=True, nullable=False)  # 是否激活
    download_count = Column(Integer, default=0, nullable=False)  # 下载次数
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    uploaded_at = Column(DateTime(timezone=True), nullable=True)  # 上传时间

    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_resource_category', 'category_id'),
        Index('idx_resource_uploader', 'uploaded_by'),
        Index('idx_resource_public', 'is_public'),
        Index('idx_resource_active', 'is_active'),
        Index('idx_resource_name', 'name'),
    )


class ResourceAccessLog(Base):
    __tablename__ = "resource_access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("resource_files.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)  # 可以为NULL表示匿名访问
    access_type = Column(String, nullable=False)  # "download", "view", "api_call"
    ip_address = Column(String, nullable=True)  # IP地址
    user_agent = Column(Text, nullable=True)  # User-Agent
    success = Column(Boolean, default=True, nullable=False)  # 是否成功
    download_size = Column(Integer, nullable=True)  # 实际下载大小（字节）
    response_time_ms = Column(Integer, nullable=True)  # 响应时间（毫秒）
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_access_resource', 'resource_id'),
        Index('idx_access_user', 'user_id'),
        Index('idx_access_type', 'access_type'),
        Index('idx_access_time', 'created_at'),
    )


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)  # 模型名称
    display_name = Column(String, nullable=True)  # 显示名称
    description = Column(Text, nullable=True)  # 模型描述
    model_type = Column(String, nullable=False)  # 模型类型: "transformer", "cnn", "rnn", "custom", etc.
    framework = Column(String, nullable=False)  # 框架: "pytorch", "tensorflow", "jax", etc.
    task_type = Column(String, nullable=False)  # 任务类型: "classification", "generation", "embedding", etc.
    input_format = Column(String, nullable=False)  # 输入格式
    output_format = Column(String, nullable=False)  # 输出格式
    resource_file_id = Column(UUID(as_uuid=True), ForeignKey("resource_files.id"), nullable=False, unique=True, index=True)  # 模型文件
    hyperparameters = Column(JSONB, nullable=True)  # 超参数
    performance_metrics = Column(JSONB, nullable=True)  # 性能指标
    tags = Column(JSONB, nullable=True)  # 标签
    metadata_info = Column(JSONB, nullable=True)  # 额外元数据
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # 创建用户
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_model_name', 'name'),
        Index('idx_model_type', 'model_type'),
        Index('idx_model_framework', 'framework'),
        Index('idx_model_task_type', 'task_type'),
        Index('idx_model_creator', 'created_by'),
    )


class DatasetRegistry(Base):
    __tablename__ = "dataset_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)  # 数据集名称
    display_name = Column(String, nullable=True)  # 显示名称
    description = Column(Text, nullable=True)  # 数据集描述
    dataset_type = Column(String, nullable=False)  # 数据集类型: "text", "image", "audio", "tabular", etc.
    size_samples = Column(Integer, nullable=True)  # 样本数量
    size_bytes = Column(Integer, nullable=True)  # 数据集大小（字节）
    schema_info = Column(JSONB, nullable=True)  # 数据集结构信息
    statistics = Column(JSONB, nullable=True)  # 统计信息
    license_info = Column(String, nullable=True)  # 许可证信息
    tags = Column(JSONB, nullable=True)  # 标签
    metadata_info = Column(JSONB, nullable=True)  # 额外元数据
    resource_file_id = Column(UUID(as_uuid=True), ForeignKey("resource_files.id"), nullable=False, index=True)  # 数据集文件
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # 创建用户
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_dataset_name', 'name'),
        Index('idx_dataset_type', 'dataset_type'),
        Index('idx_dataset_creator', 'created_by'),
    )