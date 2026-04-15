"""
数据库迁移脚本
使用Alembic进行数据库版本控制
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from app.models import Base

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库到最新版本"""
    # 创建资源类别表
    op.create_table('resource_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_resource_categories_id'), 'resource_categories', ['id'])

    # 创建用户表
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('role', sa.String(), server_default='user', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('metadata_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'])
    op.create_index(op.f('ix_users_id'), 'users', ['id'])
    op.create_index(op.f('ix_users_username'), 'users', ['username'])

    # 创建会话表
    op.create_table('sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('metadata_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('session_type', sa.String(), server_default='chat', nullable=False),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_session_active', 'sessions', ['is_active'])
    op.create_index('idx_session_user_created', 'sessions', ['user_id', 'created_at'])
    op.create_index(op.f('ix_sessions_id'), 'sessions', ['id'])

    # 创建消息表
    op.create_table('messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tokens', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('message_type', sa.String(), server_default='text', nullable=False),
        sa.Column('parent_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['parent_message_id'], ['messages.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_message_session_created', 'messages', ['session_id', 'created_at'])
    op.create_index('idx_message_user_created', 'messages', ['user_id', 'created_at'])
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'])

    # 创建知识库表
    op.create_table('knowledge_bases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('metadata_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_kb_active', 'knowledge_bases', ['is_active'])
    op.create_index('idx_kb_owner', 'knowledge_bases', ['owner_id'])
    op.create_index('idx_kb_public', 'knowledge_bases', ['is_public'])
    op.create_index(op.f('ix_knowledge_bases_id'), 'knowledge_bases', ['id'])

    # 创建文档表
    op.create_table('documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('checksum', sa.String(), nullable=True),
        sa.Column('metadata_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_document_active', 'documents', ['is_active'])
    op.create_index('idx_document_title', 'documents', ['title'])
    op.create_index('idx_document_uploaded_by', 'documents', ['uploaded_by'])
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'])

    # 创建文档块表
    op.create_table('document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_order', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('embedding', postgresql.VECTOR(1536), nullable=True),
        sa.Column('metadata_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chunk_document_order', 'document_chunks', ['document_id', 'chunk_order'])
    op.create_index(op.f('ix_document_chunks_id'), 'document_chunks', ['id'])

    # 创建知识库文档关联表
    op.create_table('knowledge_base_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_base_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('added_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('metadata_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['added_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('knowledge_base_id', 'document_id')
    )
    op.create_index('idx_kbd_added_by', 'knowledge_base_documents', ['added_by'])
    op.create_index('idx_kbd_kb_doc', 'knowledge_base_documents', ['knowledge_base_id', 'document_id'])
    op.create_index(op.f('ix_knowledge_base_documents_id'), 'knowledge_base_documents', ['id'])

    # 创建RAG会话表
    op.create_table('rag_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_base_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('search_strategy', sa.String(), server_default='semantic', nullable=False),
        sa.Column('top_k', sa.Integer(), server_default=sa.text('5'), nullable=False),
        sa.Column('threshold', sa.Float(), server_default=sa.text('0.7'), nullable=False),
        sa.Column('metadata_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_rag_knowledge_base', 'rag_sessions', ['knowledge_base_id'])
    op.create_index('idx_rag_session', 'rag_sessions', ['session_id'])
    op.create_index(op.f('ix_rag_sessions_id'), 'rag_sessions', ['id'])

    # 创建RAG查询日志表
    op.create_table('rag_query_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rag_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('retrieved_chunks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('search_time_ms', sa.Integer(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['rag_session_id'], ['rag_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_rag_query_session', 'rag_query_logs', ['rag_session_id'])
    op.create_index('idx_rag_query_time', 'rag_query_logs', ['created_at'])
    op.create_index(op.f('ix_rag_query_logs_id'), 'rag_query_logs', ['id'])

    # 创建资源文件表
    op.create_table('resource_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('original_name', sa.String(), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('storage_url', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('checksum_md5', sa.String(), nullable=True),
        sa.Column('checksum_sha256', sa.String(), nullable=True),
        sa.Column('version', sa.String(), server_default='1.0.0', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('download_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['resource_categories.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_resource_active', 'resource_files', ['is_active'])
    op.create_index('idx_resource_category', 'resource_files', ['category_id'])
    op.create_index('idx_resource_name', 'resource_files', ['name'])
    op.create_index('idx_resource_public', 'resource_files', ['is_public'])
    op.create_index('idx_resource_uploader', 'resource_files', ['uploaded_by'])
    op.create_index(op.f('ix_resource_files_id'), 'resource_files', ['id'])

    # 创建资源访问日志表
    op.create_table('resource_access_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('access_type', sa.String(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('download_size', sa.Integer(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resource_id'], ['resource_files.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_access_resource', 'resource_access_logs', ['resource_id'])
    op.create_index('idx_access_time', 'resource_access_logs', ['created_at'])
    op.create_index('idx_access_type', 'resource_access_logs', ['access_type'])
    op.create_index('idx_access_user', 'resource_access_logs', ['user_id'])
    op.create_index(op.f('ix_resource_access_logs_id'), 'resource_access_logs', ['id'])

    # 创建模型注册表
    op.create_table('model_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model_type', sa.String(), nullable=False),
        sa.Column('framework', sa.String(), nullable=False),
        sa.Column('task_type', sa.String(), nullable=False),
        sa.Column('input_format', sa.String(), nullable=False),
        sa.Column('output_format', sa.String(), nullable=False),
        sa.Column('resource_file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hyperparameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('performance_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resource_file_id'], ['resource_files.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resource_file_id')
    )
    op.create_index('idx_model_creator', 'model_registry', ['created_by'])
    op.create_index('idx_model_framework', 'model_registry', ['framework'])
    op.create_index('idx_model_name', 'model_registry', ['name'])
    op.create_index('idx_model_task_type', 'model_registry', ['task_type'])
    op.create_index('idx_model_type', 'model_registry', ['model_type'])
    op.create_index(op.f('ix_model_registry_id'), 'model_registry', ['id'])

    # 创建数据集注册表
    op.create_table('dataset_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dataset_type', sa.String(), nullable=False),
        sa.Column('size_samples', sa.Integer(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('schema_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('statistics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('license_info', sa.String(), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('resource_file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resource_file_id'], ['resource_files.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_dataset_creator', 'dataset_registry', ['created_by'])
    op.create_index('idx_dataset_name', 'dataset_registry', ['name'])
    op.create_index('idx_dataset_type', 'dataset_registry', ['dataset_type'])
    op.create_index(op.f('ix_dataset_registry_id'), 'dataset_registry', ['id'])


def downgrade():
    """降级数据库到上一版本"""
    # 删除数据集注册表
    op.drop_table('dataset_registry')

    # 删除模型注册表
    op.drop_table('model_registry')

    # 删除资源访问日志表
    op.drop_table('resource_access_logs')

    # 删除资源文件表
    op.drop_table('resource_files')

    # 删除RAG查询日志表
    op.drop_table('rag_query_logs')

    # 删除RAG会话表
    op.drop_table('rag_sessions')

    # 删除知识库文档关联表
    op.drop_table('knowledge_base_documents')

    # 删除文档块表
    op.drop_table('document_chunks')

    # 删除文档表
    op.drop_table('documents')

    # 删除知识库表
    op.drop_table('knowledge_bases')

    # 删除消息表
    op.drop_table('messages')

    # 删除会话表
    op.drop_table('sessions')

    # 删除用户表
    op.drop_table('users')

    # 删除资源类别表
    op.drop_table('resource_categories')