"""
数据库初始化脚本
用于创建所有必要的表结构和初始数据
"""

import asyncio
import sys
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError
from app.core.database import engine, Base
from app.models.user import User
from app.models.resources import ResourceCategory
from app.core.security import get_password_hash
from uuid import uuid4


def init_db():
    """初始化数据库，创建所有表"""
    print("开始初始化数据库...")
    
    try:
        # 检查数据库连接
        with engine.connect() as conn:
            print("数据库连接成功!")
    except OperationalError as e:
        print(f"数据库连接失败: {e}")
        print("请确保数据库服务正在运行并且配置正确")
        sys.exit(1)
    
    # 创建所有表
    print("创建数据表...")
    Base.metadata.create_all(bind=engine)
    
    # 检查已创建的表
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"数据库初始化完成! 共创建了 {len(tables)} 个表:")
    for table in tables:
        print(f"  - {table}")
    
    print("\n表结构创建成功!")


def setup_initial_data():
    """设置初始数据"""
    from sqlalchemy.orm import sessionmaker
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("设置初始数据...")
        
        # 检查是否已有管理员用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            # 创建管理员用户
            admin_user = User(
                id=uuid4(),
                username="admin",
                email="admin@lansee.local",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrator",
                is_active=True,
                is_superuser=True,
                role="superuser"
            )
            db.add(admin_user)
            print("创建管理员用户: admin / admin123")
        
        # 检查是否已有资源类别
        categories = ["models", "datasets", "checkpoints", "configs", "logs", "documents"]
        for cat_name in categories:
            category = db.query(ResourceCategory).filter(ResourceCategory.name == cat_name).first()
            if not category:
                category = ResourceCategory(
                    id=uuid4(),
                    name=cat_name,
                    description=f"Category for {cat_name} files"
                )
                db.add(category)
                print(f"创建资源类别: {cat_name}")
        
        db.commit()
        print("初始数据设置完成!")
        
    except Exception as e:
        print(f"设置初始数据时出错: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """主函数"""
    print("Lansee Backend Services - 数据库初始化")
    print("=" * 50)
    
    # 初始化数据库表
    init_db()
    
    # 设置初始数据
    setup_initial_data()
    
    print("=" * 50)
    print("数据库初始化完成!")


if __name__ == "__main__":
    main()