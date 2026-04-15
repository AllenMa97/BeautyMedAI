from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings
from sqlalchemy.pool import QueuePool


# PostgreSQL数据库URL
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# 创建引擎，针对PostgreSQL优化
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # 连接池大小
    max_overflow=40,  # 最大溢出连接数
    pool_pre_ping=True,  # 连接前测试
    pool_recycle=300,  # 连接回收时间
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()