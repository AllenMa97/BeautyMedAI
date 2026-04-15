from sqlalchemy.orm import Session
from app.models.session import Session as SessionModel
from app.models.message import Message
from app.schemas.session import SessionCreate, SessionUpdate, SessionInDB, MessageCreate, MessageUpdate, MessageInDB
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from config.settings import settings


def create_session(db: Session, session: SessionCreate, user_id: str) -> SessionInDB:
    """创建新会话"""
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=settings.SESSION_TIMEOUT_HOURS)
    
    db_session = SessionModel(
        id=session_id,
        user_id=user_id,
        title=session.title,
        metadata_info=session.metadata_info,
        expires_at=expires_at
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return SessionInDB.from_orm(db_session)


def get_session_by_id(db: Session, session_id: str) -> Optional[SessionInDB]:
    """根据ID获取会话"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if db_session and db_session.is_active:
        return SessionInDB.from_orm(db_session)
    return None


def get_sessions_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[SessionInDB]:
    """获取用户的会话列表"""
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == user_id,
        SessionModel.is_active == True
    ).offset(skip).limit(limit).all()
    
    return [SessionInDB.from_orm(session) for session in sessions]


def update_session(db: Session, session_id: str, session_update: SessionUpdate) -> Optional[SessionInDB]:
    """更新会话"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        return None
    
    # 更新可修改的字段
    if session_update.title is not None:
        db_session.title = session_update.title
    if session_update.metadata_info is not None:
        db_session.metadata_info = session_update.metadata_info
    if session_update.is_active is not None:
        db_session.is_active = session_update.is_active
    
    db.commit()
    db.refresh(db_session)
    
    return SessionInDB.from_orm(db_session)


def delete_session(db: Session, session_id: str) -> bool:
    """删除会话（软删除）"""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        return False
    
    db_session.is_active = False
    db.commit()
    return True


def create_message(db: Session, message: MessageCreate, user_id: str) -> MessageInDB:
    """创建新消息"""
    message_id = str(uuid.uuid4())
    
    db_message = Message(
        id=message_id,
        session_id=message.session_id,
        user_id=user_id,
        role=message.role,
        content=message.content,
        tokens=message.tokens,
        metadata_info=message.metadata_info
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return MessageInDB.from_orm(db_message)


def get_messages_by_session(db: Session, session_id: str, skip: int = 0, limit: int = 100) -> List[MessageInDB]:
    """获取会话的消息列表"""
    messages = db.query(Message).filter(Message.session_id == session_id).offset(skip).limit(limit).all()
    return [MessageInDB.from_orm(message) for message in messages]


def update_message(db: Session, message_id: str, message_update: MessageUpdate) -> Optional[MessageInDB]:
    """更新消息"""
    db_message = db.query(Message).filter(Message.id == message_id).first()
    if not db_message:
        return None
    
    # 更新可修改的字段
    if message_update.content is not None:
        db_message.content = message_update.content
    if message_update.metadata_info is not None:
        db_message.metadata_info = message_update.metadata_info
    
    db.commit()
    db.refresh(db_message)
    
    return MessageInDB.from_orm(db_message)