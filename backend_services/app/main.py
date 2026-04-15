from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from app.api.v1 import auth, users, sessions, chat, llm, health, admin, resources


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/api/docs",  # 标准化文档路径
    )

    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 包含API路由
    app.include_router(auth.router, prefix=settings.API_V1_STR)
    app.include_router(users.router, prefix=settings.API_V1_STR)
    app.include_router(sessions.router, prefix=settings.API_V1_STR)
    app.include_router(chat.router, prefix=settings.API_V1_STR)
    app.include_router(llm.router, prefix=settings.API_V1_STR)
    app.include_router(health.router, prefix=settings.API_V1_STR)
    app.include_router(admin.router, prefix=settings.API_V1_STR)
    app.include_router(resources.router, prefix=settings.API_V1_STR)

    @app.get("/")
    def read_root():
        return {"message": "Lansee Backend Services API"}

    @app.get("/health")
    def health_check():
        return {"status": "healthy", "service": "backend-services"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )