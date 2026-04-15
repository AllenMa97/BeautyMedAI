from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.schemas.user import User
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.storage_service import storage_service
from app.models.resources import (
    ResourceCategory, 
    ResourceFile, 
    ResourceAccessLog, 
    ModelRegistry, 
    DatasetRegistry
)
from app.services.gpu_manager_service import gpu_manager_service


router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("/categories", response_model=List[dict])
async def get_resource_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取资源类别列表"""
    categories = db.query(ResourceCategory).all()
    return [{"id": str(cat.id), "name": cat.name, "description": cat.description} for cat in categories]


@router.post("/categories", response_model=dict)
async def create_resource_category(
    name: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建资源类别"""
    # 检查类别是否已存在
    existing_cat = db.query(ResourceCategory).filter(ResourceCategory.name == name).first()
    if existing_cat:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    category = ResourceCategory(
        id=uuid.uuid4(),
        name=name,
        description=description or f"Category for {name} files"
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return {"id": str(category.id), "name": category.name, "description": category.description}


@router.post("/upload", response_model=dict)
async def upload_resource_file(
    file: UploadFile = File(...),
    category_id: str = Form(...),
    description: str = Form(None),
    tags: str = Form(None),  # JSON string
    version: str = Form("1.0.0"),
    is_public: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传资源文件"""
    try:
        # 验证类别
        category = db.query(ResourceCategory).filter(ResourceCategory.id == uuid.UUID(category_id)).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # 读取文件内容
        file_content = await file.read()
        original_name = file.filename
        
        # 上传到存储服务
        storage_path = await storage_service.upload_file(
            file_content, 
            original_name, 
            file.content_type
        )
        
        if not storage_path:
            raise HTTPException(status_code=500, detail="Failed to upload file to storage")
        
        # 创建资源文件记录
        resource_file = ResourceFile(
            id=uuid.uuid4(),
            name=f"{uuid.uuid4()}_{original_name}",
            original_name=original_name,
            category_id=uuid.UUID(category_id),
            file_path=storage_path,
            file_size=len(file_content),
            mime_type=file.content_type,
            description=description,
            tags={"tags": tags.split(",")} if tags else {},
            metadata_info={"version": version},
            uploaded_by=current_user.id,
            is_public=is_public,
            version=version
        )
        
        db.add(resource_file)
        db.commit()
        db.refresh(resource_file)
        
        return {
            "id": str(resource_file.id),
            "name": resource_file.original_name,
            "file_path": resource_file.file_path,
            "size": resource_file.file_size,
            "uploaded_at": resource_file.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/files", response_model=List[dict])
async def list_resource_files(
    category_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出资源文件"""
    query = db.query(ResourceFile)
    
    # 只适用于当前用户或公共文件
    query = query.filter(
        (ResourceFile.uploaded_by == current_user.id) | 
        (ResourceFile.is_public == True)
    )
    
    if category_id:
        query = query.filter(ResourceFile.category_id == uuid.UUID(category_id))
    
    files = query.offset(skip).limit(limit).all()
    
    return [{
        "id": str(f.id),
        "name": f.original_name,
        "size": f.file_size,
        "mime_type": f.mime_type,
        "uploaded_by": str(f.uploaded_by),
        "uploaded_at": f.created_at,
        "is_public": f.is_public,
        "version": f.version,
        "description": f.description
    } for f in files]


@router.get("/files/{file_id}", response_model=dict)
async def get_resource_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取资源文件详情"""
    resource_file = db.query(ResourceFile).filter(ResourceFile.id == uuid.UUID(file_id)).first()
    
    if not resource_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # 检查权限：用户必须是上传者或文件是公共的
    if resource_file.uploaded_by != current_user.id and not resource_file.is_public:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return {
        "id": str(resource_file.id),
        "name": resource_file.original_name,
        "size": resource_file.file_size,
        "mime_type": resource_file.mime_type,
        "file_path": resource_file.file_path,
        "uploaded_by": str(resource_file.uploaded_by),
        "uploaded_at": resource_file.created_at,
        "is_public": resource_file.is_public,
        "version": resource_file.version,
        "description": resource_file.description,
        "download_count": resource_file.download_count
    }


@router.get("/files/{file_id}/download")
async def download_resource_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载资源文件"""
    resource_file = db.query(ResourceFile).filter(ResourceFile.id == uuid.UUID(file_id)).first()
    
    if not resource_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # 检查权限：用户必须是上传者或文件是公共的
    if resource_file.uploaded_by != current_user.id and not resource_file.is_public:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # 记录访问日志
    access_log = ResourceAccessLog(
        id=uuid.uuid4(),
        resource_id=resource_file.id,
        user_id=current_user.id,
        access_type="download",
        success=True
    )
    db.add(access_log)
    
    # 增加下载计数
    resource_file.download_count += 1
    db.commit()
    
    # 从存储服务获取文件内容
    file_content = await storage_service.download_file(resource_file.file_path)
    
    if not file_content:
        raise HTTPException(status_code=404, detail="File not found in storage")
    
    # 返回文件内容
    from fastapi.responses import StreamingResponse
    import io
    return StreamingResponse(io.BytesIO(file_content), media_type=resource_file.mime_type, 
                             headers={"Content-Disposition": f"attachment; filename={resource_file.original_name}"})


@router.delete("/files/{file_id}")
async def delete_resource_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除资源文件"""
    resource_file = db.query(ResourceFile).filter(ResourceFile.id == uuid.UUID(file_id)).first()
    
    if not resource_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # 检查权限：用户必须是上传者
    if resource_file.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # 从存储服务删除文件
    await storage_service.delete_file(resource_file.file_path)
    
    # 从数据库删除记录
    db.delete(resource_file)
    db.commit()
    
    return {"message": "File deleted successfully"}


@router.get("/models", response_model=List[dict])
async def list_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出模型"""
    models = db.query(ModelRegistry).offset(skip).limit(limit).all()
    
    return [{
        "id": str(m.id),
        "name": m.name,
        "display_name": m.display_name,
        "description": m.description,
        "model_type": m.model_type,
        "framework": m.framework,
        "task_type": m.task_type,
        "created_by": str(m.created_by),
        "created_at": m.created_at,
        "is_active": m.is_active
    } for m in models]


@router.get("/datasets", response_model=List[dict])
async def list_datasets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出数据集"""
    datasets = db.query(DatasetRegistry).offset(skip).limit(limit).all()
    
    return [{
        "id": str(d.id),
        "name": d.name,
        "display_name": d.display_name,
        "description": d.description,
        "dataset_type": d.dataset_type,
        "size_samples": d.size_samples,
        "size_bytes": d.size_bytes,
        "created_by": str(d.created_by),
        "created_at": d.created_at,
        "is_active": d.is_active
    } for d in datasets]


@router.get("/gpu-status")
async def get_gpu_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取GPU状态"""
    if not gpu_manager_service._initialized:
        await gpu_manager_service.initialize()
    
    gpu_status = gpu_manager_service.get_gpu_status()
    gpu_stats = gpu_manager_service.get_gpu_statistics()
    user_gpu_usage = gpu_manager_service.get_user_gpu_usage(str(current_user.id))
    
    return {
        "gpus": [
            {
                "id": gpu.id,
                "name": gpu.name,
                "total_memory": gpu.total_memory,
                "used_memory": gpu.used_memory,
                "memory_util": gpu.memory_util,
                "gpu_util": gpu.gpu_util,
                "status": gpu.status.value,
                "temperature": gpu.temperature
            } for gpu in gpu_status
        ],
        "statistics": gpu_stats,
        "user_usage": user_gpu_usage
    }