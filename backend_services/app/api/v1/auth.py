from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import LoginRequest, RegisterRequest, RefreshTokenRequest, Token
from app.schemas.user import User as UserSchema
from app.services.auth_service import login_user, register_user, refresh_access_token
from app.core.database import get_db
from app.core.security import get_current_user
from typing import Any


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest, db: Session = Depends(get_db)) -> Any:
    """用户登录"""
    access_token, refresh_token, user = login_user(db, login_request)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/register", response_model=UserSchema)
async def register(register_request: RegisterRequest, db: Session = Depends(get_db)) -> Any:
    """用户注册"""
    user = register_user(db, register_request)
    return user


@router.post("/refresh", response_model=dict)
async def refresh_token(refresh_request: RefreshTokenRequest, db: Session = Depends(get_db)) -> Any:
    """刷新访问令牌"""
    new_access_token = refresh_access_token(db, refresh_request.refresh_token)
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserSchema)
async def get_current_user_profile(current_user: UserSchema = Depends(get_current_user)) -> Any:
    """获取当前用户信息"""
    return current_user