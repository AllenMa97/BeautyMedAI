from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserInDB
from app.core.security import get_password_hash
from typing import List, Optional
import uuid


def get_user_by_id(db: Session, user_id: str) -> Optional[UserInDB]:
    """根据ID获取用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return UserInDB.from_orm(user)
    return None


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[UserInDB]:
    """获取用户列表"""
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserInDB.from_orm(user) for user in users]


def create_user(db: Session, user: UserCreate) -> UserInDB:
    """创建新用户"""
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        id=user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserInDB.from_orm(db_user)


def update_user(db: Session, user_id: str, user_update: UserUpdate) -> Optional[UserInDB]:
    """更新用户信息"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    
    # 更新可修改的字段
    if user_update.full_name is not None:
        db_user.full_name = user_update.full_name
    if user_update.email is not None:
        db_user.email = user_update.email
    if user_update.is_active is not None:
        db_user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(db_user)
    
    return UserInDB.from_orm(db_user)


def delete_user(db: Session, user_id: str) -> bool:
    """删除用户"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True