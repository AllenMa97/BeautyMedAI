from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, LargeBinary, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # 如果pgvector不可用，则使用ARRAY作为替代
    Vector = ARRAY(Float)


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)  # 文档内容
    source_url = Column(String, nullable=True)  # 文档来源URL
    file_path = Column(String, nullable=True)  # 文件存储路径
    mime_type = Column(String, nullable=True)  # MIME类型
    size_bytes = Column(Integer, nullable=True)  # 文件大小
    checksum = Column(String, nullable=True)  # 文件校验和
    metadata_info = Column(JSONB, nullable=True)  # 文档元数据
    tags = Column(JSONB, nullable=True)  # 文档标签
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # 上传用户
    is_active = Column(Boolean, default=True, nullable=False)

    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_document_title', 'title'),
        Index('idx_document_uploaded_by', 'uploaded_by'),
        Index('idx_document_active', 'is_active'),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_order = Column(Integer, nullable=False)  # 块顺序
    content = Column(Text, nullable=False)  # 块内容
    token_count = Column(Integer, default=0, nullable=False)  # token数量
    embedding = Column(ARRAY(Float), nullable=True)  # 向量嵌入，使用数组替代
    metadata_info = Column(JSONB, nullable=True)  # 块元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_chunk_document_order', 'document_id', 'chunk_order'),
    )


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)  # 知识库名称
    description = Column(Text, nullable=True)  # 知识库描述
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)  # 所有者
    is_public = Column(Boolean, default=False, nullable=False)  # 是否公开
    metadata_info = Column(JSONB, nullable=True)  # 知识库元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)

    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_kb_owner', 'owner_id'),
        Index('idx_kb_public', 'is_public'),
        Index('idx_kb_active', 'is_active'),
    )


class KnowledgeBaseDocument(Base):
    __tablename__ = "knowledge_base_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    added_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # 添加用户
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_info = Column(JSONB, nullable=True)  # 关联元数据

    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_kbd_kb_doc', 'knowledge_base_id', 'document_id', unique=True),  # 确保知识库中文档唯一
        Index('idx_kbd_added_by', 'added_by'),
    )


class RAGSession(Base):
    __tablename__ = "rag_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)  # 关联普通会话
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=True, index=True)  # 使用的知识库
    search_strategy = Column(String, default="semantic", nullable=False)  # 搜索策略: semantic, keyword, hybrid
    top_k = Column(Integer, default=5, nullable=False)  # 返回前k个结果
    threshold = Column(Float, default=0.7, nullable=False)  # 相似度阈值
    metadata_info = Column(JSONB, nullable=True)  # RAG会话元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_rag_session', 'session_id'),
        Index('idx_rag_knowledge_base', 'knowledge_base_id'),
    )


class RAGQueryLog(Base):
    __tablename__ = "rag_query_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    rag_session_id = Column(UUID(as_uuid=True), ForeignKey("rag_sessions.id"), nullable=False, index=True)
    query_text = Column(Text, nullable=False)  # 查询文本
    response_text = Column(Text, nullable=False)  # 响应文本
    retrieved_chunks = Column(JSONB, nullable=True)  # 检索到的块信息
    search_time_ms = Column(Integer, nullable=True)  # 搜索耗时(毫秒)
    tokens_used = Column(Integer, default=0, nullable=False)  # 使用的token数
    user_rating = Column(Integer, nullable=True)  # 用户评分
    feedback = Column(Text, nullable=True)  # 用户反馈
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_rag_query_session', 'rag_session_id'),
        Index('idx_rag_query_time', 'created_at'),
    )