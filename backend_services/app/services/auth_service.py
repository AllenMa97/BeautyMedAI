from datetime import timedelta
from fastapi import HTTPException, status, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.security import authenticate_user, create_access_token, create_refresh_token, get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserInDB
from app.schemas.auth import LoginRequest, RegisterRequest
from app.core.database import get_db
import uuid


def login_user(db: Session, request: LoginRequest) -> tuple:
    """用户登录"""
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 更新最后登录时间
    user.last_login = func.now()
    db.commit()
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username}
    )
    
    # 创建刷新令牌
    refresh_token = create_refresh_token(
        data={"sub": user.id, "username": user.username}
    )
    
    return access_token, refresh_token, user


def register_user(db: Session, request: RegisterRequest) -> UserInDB:
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(
        (User.username == request.username) | (User.email == request.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # 创建新用户
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(request.password)
    
    db_user = User(
        id=user_id,
        username=request.username,
        email=request.email,
        full_name=request.full_name,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def refresh_access_token(db: Session, refresh_token: str) -> str:
    """刷新访问令牌"""
    from app.core.security import verify_token
    
    payload = verify_token(refresh_token, refresh=True)
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # 验证用户仍然存在且激活
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # 创建新的访问令牌
    new_access_token = create_access_token(
        data={"sub": user.id, "username": user.username}
    )
    
    return new_access_token