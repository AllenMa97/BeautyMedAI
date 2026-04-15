from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import User, UserCreate, UserUpdate
from app.services.user_service import get_user_by_id, get_users, create_user, update_user, delete_user
from app.core.database import get_db
from app.core.security import get_current_user
from typing import List, Any


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """获取用户列表"""
    # 检查权限 - 只有管理员可以查看用户列表
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    users = get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=User)
async def read_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Any:
    """获取特定用户信息"""
    # 用户只能查看自己的信息，管理员可以查看任何用户
    if current_user.id != user_id and not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=User)
async def update_user_endpoint(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """更新用户信息"""
    # 用户只能更新自己的信息，管理员可以更新任何用户
    if current_user.id != user_id and not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    updated_user = update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.delete("/{user_id}")
async def delete_user_endpoint(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """删除用户"""
    # 只有管理员可以删除用户
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}