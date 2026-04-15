from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.schemas.session import SessionCreate, SessionUpdate, Session, MessageCreate, MessageUpdate, Message
from app.schemas.user import User
from app.services.session_service import (
    create_session, get_session_by_id, get_sessions_by_user, 
    update_session, delete_session, create_message, 
    get_messages_by_session, update_message
)
from app.core.database import get_db
from app.core.security import get_current_user
from typing import List, Any
from app.services.llm_service import llm_service, LLMRequest
from app.services.gpu_manager_service import gpu_manager_service
from datetime import datetime
import uuid


router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/", response_model=Session)
async def create_new_session(
    session: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """创建新会话"""
    return create_session(db, session, current_user.id)


@router.get("/", response_model=List[Session])
async def read_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """获取用户会话列表"""
    return get_sessions_by_user(db, current_user.id, skip=skip, limit=limit)


@router.get("/{session_id}", response_model=Session)
async def read_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """获取特定会话"""
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # 检查会话是否属于当前用户
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return session


@router.put("/{session_id}", response_model=Session)
async def update_session_endpoint(
    session_id: str,
    session_update: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """更新会话"""
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # 检查会话是否属于当前用户
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    updated_session = update_session(db, session_id, session_update)
    if not updated_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated_session


@router.delete("/{session_id}")
async def delete_session_endpoint(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """删除会话"""
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # 检查会话是否属于当前用户
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    success = delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted successfully"}


@router.post("/{session_id}/messages", response_model=Message)
async def create_message_endpoint(
    session_id: str,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """创建新消息"""
    # 验证会话是否属于当前用户
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return create_message(db, message, current_user.id)


@router.get("/{session_id}/messages", response_model=List[Message])
async def read_messages(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """获取会话消息列表"""
    # 验证会话是否属于当前用户
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return get_messages_by_session(db, session_id, skip=skip, limit=limit)


@router.put("/messages/{message_id}", response_model=Message)
async def update_message_endpoint(
    message_id: str,
    message_update: MessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """更新消息"""
    # 这里需要获取消息所属的会话，然后验证用户权限
    from app.models.message import Message as MessageModel
    db_message = db.query(MessageModel).filter(MessageModel.id == message_id).first()
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # 验证消息所属的会话是否属于当前用户
    session = get_session_by_id(db, db_message.session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    updated_message = update_message(db, message_id, message_update)
    if not updated_message:
        raise HTTPException(status_code=404, detail="Message not found")
    return updated_message


@router.get("/{session_id}/summary")
async def get_session_summary(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """获取会话摘要"""
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 获取会话的所有消息
    messages = get_messages_by_session(db, session_id)
    
    # 生成摘要（这里可以调用LLM服务）
    message_contents = [msg.content for msg in messages]
    combined_content = "\n".join(message_contents)
    
    # 使用LLM生成摘要
    llm_request = LLMRequest(
        model="qwen-flash",
        provider="algorithm_service",
        messages=[
            {
                "role": "system", 
                "content": "你是一个专业的对话摘要生成器。请根据以下对话内容生成简洁准确的摘要。"
            },
            {
                "role": "user", 
                "content": f"请为以下对话生成摘要：\n\n{combined_content[:2000]}"  # 限制长度
            }
        ],
        max_tokens=512
    )
    
    try:
        summary_response = await llm_service.call_llm(llm_request)
        summary = summary_response.choices[0].message.content
    except Exception:
        summary = "摘要生成失败"
    
    return {
        "session_id": session_id,
        "summary": summary,
        "message_count": len(messages),
        "last_updated": session.updated_at
    }


@router.post("/{session_id}/share")
async def share_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """分享会话"""
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 生成分享链接
    share_token = str(uuid.uuid4())
    
    # 这里可以将分享信息存储到数据库
    # 为简化，这里直接返回分享链接
    share_link = f"/shared/session/{share_token}"
    
    return {
        "session_id": session_id,
        "share_token": share_token,
        "share_link": share_link,
        "created_at": datetime.utcnow()
    }


@router.get("/{session_id}/export")
async def export_session(
    session_id: str,
    format: str = "json",  # json, txt, md
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """导出会话"""
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 获取会话的所有消息
    messages = get_messages_by_session(db, session_id)
    
    if format == "txt":
        content = f"会话标题: {session.title}\n"
        content += f"创建时间: {session.created_at}\n"
        content += f"更新时间: {session.updated_at}\n\n"
        
        for msg in messages:
            role = "用户" if msg.role == "user" else "助手" if msg.role == "assistant" else msg.role
            content += f"[{msg.created_at}] {role}: {msg.content}\n\n"
        
        return {
            "format": "txt",
            "content": content,
            "filename": f"session_{session_id}.txt"
        }
    
    elif format == "md":
        content = f"# {session.title}\n\n"
        content += f"*创建时间: {session.created_at}*\n\n"
        
        for msg in messages:
            role = "**用户**" if msg.role == "user" else "**助手**" if msg.role == "assistant" else f"**{msg.role}**"
            content += f"### {role}\n{msg.content}\n\n---\n\n"
        
        return {
            "format": "md",
            "content": content,
            "filename": f"session_{session_id}.md"
        }
    
    else:  # json
        return {
            "format": "json",
            "session": {
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at,
                        "tokens": msg.tokens
                    } for msg in messages
                ]
            },
            "filename": f"session_{session_id}.json"
        }