from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.schemas.session import MessageCreate
from app.schemas.user import User
from app.services.session_service import create_message, get_messages_by_session
from app.core.database import get_db
from app.core.security import get_current_user
from typing import Any, Dict, AsyncGenerator
import httpx
from config.settings import settings
import json


router = APIRouter(prefix="/chat", tags=["Chat"])


async def forward_to_algorithm_service(payload: Dict) -> AsyncGenerator[str, None]:
    """转发请求到算法服务并处理流式响应"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 发送到算法服务的入口点
            async with client.stream(
                "POST", 
                f"{settings.ALGORITHM_SERVICE_URL}/api/v1/entrance",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                
                # 处理流式响应
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        yield chunk
                        
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Error connecting to algorithm service: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Algorithm service returned error: {str(e)}"
            )


@router.post("/completions")
async def chat_completions(
    request: Request,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """聊天完成接口"""
    # 验证会话是否属于当前用户
    from app.services.session_service import get_session_by_id
    session = get_session_by_id(db, message.session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 从数据库获取历史消息
    history_messages = get_messages_by_session(db, message.session_id)
    
    # 构造上下文
    context_list = []
    for msg in history_messages:
        context_list.append({
            "user": msg.content if msg.role == "user" else "",
            "response": msg.content if msg.role == "assistant" else ""
        })
    
    # 如果当前消息是用户消息，则添加到上下文中
    if message.role == "user":
        context_list.append({
            "user": message.content,
            "response": ""
        })
    
    context_str = json.dumps(context_list, ensure_ascii=False)
    
    # 构造发送到算法服务的请求
    algorithm_payload = {
        "session_id": message.session_id,
        "user_id": current_user.id,
        "lang": "zh-CN",
        "stream_flag": False,  # 非流式请求
        "user_input": message.content,
        "context": context_str
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{settings.ALGORITHM_SERVICE_URL}/api/v1/entrance",
                json=algorithm_payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 保存用户消息
            user_message = MessageCreate(
                session_id=message.session_id,
                role="user",
                content=message.content,
                tokens=len(message.content)
            )
            create_message(db, user_message, current_user.id)
            
            # 保存AI响应消息
            ai_response_content = result.get("data", {}).get("final_result", "") if result.get("code") == 200 else "抱歉，处理请求时出现错误"
            ai_message = MessageCreate(
                session_id=message.session_id,
                role="assistant",
                content=ai_response_content,
                tokens=len(ai_response_content)
            )
            create_message(db, ai_message, current_user.id)
            
            return result
            
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Error connecting to algorithm service: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Algorithm service returned error: {str(e)}"
            )


@router.post("/stream")
async def chat_stream(
    request: Request,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """流式聊天接口"""
    # 验证会话是否属于当前用户
    from app.services.session_service import get_session_by_id
    session = get_session_by_id(db, message.session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 从数据库获取历史消息
    history_messages = get_messages_by_session(db, message.session_id)
    
    # 构造上下文
    context_list = []
    for msg in history_messages:
        context_list.append({
            "user": msg.content if msg.role == "user" else "",
            "response": msg.content if msg.role == "assistant" else ""
        })
    
    # 如果当前消息是用户消息，则添加到上下文中
    if message.role == "user":
        context_list.append({
            "user": message.content,
            "response": ""
        })
    
    context_str = json.dumps(context_list, ensure_ascii=False)
    
    # 构造发送到算法服务的请求
    algorithm_payload = {
        "session_id": message.session_id,
        "user_id": current_user.id,
        "lang": "zh-CN",
        "stream_flag": True,  # 流式请求
        "user_input": message.content,
        "context": context_str
    }
    
    # 保存用户消息
    user_message = MessageCreate(
        session_id=message.session_id,
        role="user",
        content=message.content,
        tokens=len(message.content)
    )
    create_message(db, user_message, current_user.id)
    
    # 返回流式响应
    from fastapi.responses import StreamingResponse
    
    async def generate():
        async for chunk in forward_to_algorithm_service(algorithm_payload):
            yield f"data: {chunk}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取聊天历史"""
    # 验证会话是否属于当前用户
    from app.services.session_service import get_session_by_id
    session = get_session_by_id(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    messages = get_messages_by_session(db, session_id, skip=skip, limit=limit)
    return messages