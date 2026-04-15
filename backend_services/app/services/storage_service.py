from typing import Optional, BinaryIO, Union, Dict, Any, List
import os
from datetime import datetime
from abc import ABC, abstractmethod
import boto3
from botocore.exceptions import ClientError
from minio import Minio
from minio.error import S3Error
from urllib.parse import urlparse
import logging
from config.settings import settings
import uuid
from app.models.resources import ResourceFile, ResourceCategory, ResourceAccessLog
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """存储后端抽象基类"""
    
    @abstractmethod
    async def upload_file(self, file_data: Union[BinaryIO, bytes], filename: str, 
                         content_type: Optional[str] = None, metadata: Optional[dict] = None) -> Optional[str]:
        pass
    
    @abstractmethod
    async def download_file(self, file_path: str) -> Optional[bytes]:
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        pass


class LocalStorageBackend(StorageBackend):
    """本地存储后端"""
    
    def __init__(self, storage_path: str = "uploads"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    async def upload_file(self, file_data: Union[BinaryIO, bytes], filename: str, 
                         content_type: Optional[str] = None, metadata: Optional[dict] = None) -> Optional[str]:
        try:
            # 生成唯一文件名
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(self.storage_path, unique_filename)
            
            # 写入文件
            if hasattr(file_data, 'read'):
                with open(file_path, 'wb') as f:
                    f.write(file_data.read())
            else:
                with open(file_path, 'wb') as f:
                    f.write(file_data)
            
            return f"/storage/local/{unique_filename}"
        except Exception as e:
            logger.error(f"Local storage upload failed: {str(e)}")
            return None
    
    async def download_file(self, file_path: str) -> Optional[bytes]:
        try:
            if file_path.startswith('/storage/local/'):
                filename = file_path[14:]  # 移除 '/storage/local/' 前缀
            else:
                filename = file_path
            
            full_path = os.path.join(self.storage_path, filename)
            if os.path.exists(full_path):
                with open(full_path, 'rb') as f:
                    return f.read()
            return None
        except Exception as e:
            logger.error(f"Local storage download failed: {str(e)}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        try:
            if file_path.startswith('/storage/local/'):
                filename = file_path[14:]  # 移除 '/storage/local/' 前缀
            else:
                filename = file_path
            
            full_path = os.path.join(self.storage_path, filename)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Local storage delete failed: {str(e)}")
            return False
    
    async def file_exists(self, file_path: str) -> bool:
        try:
            if file_path.startswith('/storage/local/'):
                filename = file_path[14:]  # 移除 '/storage/local/' 前缀
            else:
                filename = file_path
            
            full_path = os.path.join(self.storage_path, filename)
            return os.path.exists(full_path)
        except Exception as e:
            logger.error(f"Local storage exists check failed: {str(e)}")
            return False


class S3StorageBackend(StorageBackend):
    """AWS S3存储后端"""
    
    def __init__(self, endpoint_url: str, access_key: str, secret_key: str, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                self.client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created S3 bucket: {self.bucket_name}")
    
    async def upload_file(self, file_data: Union[BinaryIO, bytes], filename: str, 
                         content_type: Optional[str] = None, metadata: Optional[dict] = None) -> Optional[str]:
        try:
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if metadata:
                # S3 metadata keys must be prefixed with 'x-amz-meta-'
                meta_args = {f'x-amz-meta-{k}': str(v) for k, v in metadata.items()}
                extra_args.update(meta_args)
            
            if hasattr(file_data, 'read'):
                self.client.upload_fileobj(
                    file_data, 
                    self.bucket_name, 
                    unique_filename,
                    ExtraArgs=extra_args
                )
            else:
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=unique_filename,
                    Body=file_data,
                    **extra_args
                )
            
            return f"/storage/s3/{unique_filename}"
        except Exception as e:
            logger.error(f"S3 storage upload failed: {str(e)}")
            return None
    
    async def download_file(self, file_path: str) -> Optional[bytes]:
        try:
            if file_path.startswith('/storage/s3/'):
                key = file_path[13:]  # 移除 '/storage/s3/' 前缀
            else:
                key = file_path
            
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            logger.error(f"S3 storage download failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"S3 storage download failed: {str(e)}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        try:
            if file_path.startswith('/storage/s3/'):
                key = file_path[13:]  # 移除 '/storage/s3/' 前缀
            else:
                key = file_path
            
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception as e:
            logger.error(f"S3 storage delete failed: {str(e)}")
            return False
    
    async def file_exists(self, file_path: str) -> bool:
        try:
            if file_path.startswith('/storage/s3/'):
                key = file_path[13:]  # 移除 '/storage/s3/' 前缀
            else:
                key = file_path
            
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"S3 storage exists check failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"S3 storage exists check failed: {str(e)}")
            return False


class MinIOStorageBackend(StorageBackend):
    """MinIO存储后端"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket_name: str, secure: bool = False):
        self.bucket_name = bucket_name
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        
        # 确保存储桶存在
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
    
    async def upload_file(self, file_data: Union[BinaryIO, bytes], filename: str, 
                         content_type: Optional[str] = None, metadata: Optional[dict] = None) -> Optional[str]:
        try:
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # 确定文件大小
            if hasattr(file_data, 'read'):
                # 如果是文件对象，需要获取大小
                file_data.seek(0, 2)  # 移动到文件末尾
                file_size = file_data.tell()
                file_data.seek(0)  # 移回开头
            else:
                # 如果是bytes
                file_size = len(file_data)

            # 设置默认内容类型
            if not content_type:
                if filename.lower().endswith(('.jpg', '.jpeg')):
                    content_type = 'image/jpeg'
                elif filename.lower().endswith('.png'):
                    content_type = 'image/png'
                elif filename.lower().endswith('.gif'):
                    content_type = 'image/gif'
                elif filename.lower().endswith('.pdf'):
                    content_type = 'application/pdf'
                else:
                    content_type = 'application/octet-stream'

            result = self.client.put_object(
                self.bucket_name,
                unique_filename,
                file_data,
                file_size,
                content_type=content_type,
                metadata=metadata
            )

            return f"/storage/minio/{unique_filename}"
        except S3Error as e:
            logger.error(f"MinIO storage upload failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"MinIO storage upload failed: {str(e)}")
            return None
    
    async def download_file(self, file_path: str) -> Optional[bytes]:
        try:
            if file_path.startswith('/storage/minio/'):
                object_name = file_path[15:]  # 移除 '/storage/minio/' 前缀
            else:
                object_name = file_path

            response = self.client.get_object(self.bucket_name, object_name)
            try:
                data = response.read()
                return data
            finally:
                response.close()
                response.release_conn()
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return None
            logger.error(f"MinIO storage download failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"MinIO storage download failed: {str(e)}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        try:
            if file_path.startswith('/storage/minio/'):
                object_name = file_path[15:]  # 移除 '/storage/minio/' 前缀
            else:
                object_name = file_path

            self.client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            logger.error(f"MinIO storage delete failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"MinIO storage delete failed: {str(e)}")
            return False
    
    async def file_exists(self, file_path: str) -> bool:
        try:
            if file_path.startswith('/storage/minio/'):
                object_name = file_path[15:]  # 移除 '/storage/minio/' 前缀
            else:
                object_name = file_path

            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return False
            logger.error(f"MinIO storage exists check failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"MinIO storage exists check failed: {str(e)}")
            return False


class UnifiedStorageService:
    """统一存储服务，支持多种存储后端"""
    
    def __init__(self):
        self.backends: Dict[str, StorageBackend] = {}
        self._initialize_backends()
    
    def _initialize_backends(self):
        """根据配置初始化存储后端"""
        storage_type = settings.STORAGE_TYPE.lower()
        
        if storage_type == "local":
            self.backends["default"] = LocalStorageBackend()
        elif storage_type == "s3":
            self.backends["default"] = S3StorageBackend(
                endpoint_url=os.getenv("S3_ENDPOINT_URL", "https://s3.amazonaws.com"),
                access_key=os.getenv("S3_ACCESS_KEY"),
                secret_key=os.getenv("S3_SECRET_KEY"),
                bucket_name=settings.STORAGE_BUCKET_NAME,
                region=os.getenv("S3_REGION", "us-east-1")
            )
        elif storage_type == "minio":
            self.backends["default"] = MinIOStorageBackend(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                bucket_name=settings.STORAGE_BUCKET_NAME,
                secure=settings.MINIO_SECURE
            )
        else:
            # 默认使用本地存储
            self.backends["default"] = LocalStorageBackend()
        
        # 可以配置多个后端用于不同的用途
        if os.getenv("MODEL_STORAGE_TYPE"):
            model_storage_type = os.getenv("MODEL_STORAGE_TYPE").lower()
            if model_storage_type == "s3":
                self.backends["models"] = S3StorageBackend(
                    endpoint_url=os.getenv("MODEL_S3_ENDPOINT_URL", "https://s3.amazonaws.com"),
                    access_key=os.getenv("MODEL_S3_ACCESS_KEY"),
                    secret_key=os.getenv("MODEL_S3_SECRET_KEY"),
                    bucket_name=os.getenv("MODEL_STORAGE_BUCKET_NAME", "lansee-models"),
                    region=os.getenv("MODEL_S3_REGION", "us-east-1")
                )
            elif model_storage_type == "minio":
                self.backends["models"] = MinIOStorageBackend(
                    endpoint=os.getenv("MODEL_MINIO_ENDPOINT", "localhost:9000"),
                    access_key=os.getenv("MODEL_MINIO_ACCESS_KEY", "minioadmin"),
                    secret_key=os.getenv("MODEL_MINIO_SECRET_KEY", "minioadmin"),
                    bucket_name=os.getenv("MODEL_STORAGE_BUCKET_NAME", "lansee-models"),
                    secure=os.getenv("MODEL_MINIO_SECURE", "false").lower() == "true"
                )
            else:
                self.backends["models"] = self.backends["default"]
    
    async def upload_file(
        self, 
        file_data: Union[BinaryIO, bytes], 
        filename: str, 
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
        storage_backend: str = "default"
    ) -> Optional[str]:
        """上传文件"""
        backend = self.backends.get(storage_backend, self.backends["default"])
        return await backend.upload_file(file_data, filename, content_type, metadata)
    
    async def download_file(self, file_path: str, storage_backend: str = "default") -> Optional[bytes]:
        """下载文件"""
        backend = self.backends.get(storage_backend, self.backends["default"])
        return await backend.download_file(file_path)
    
    async def delete_file(self, file_path: str, storage_backend: str = "default") -> bool:
        """删除文件"""
        backend = self.backends.get(storage_backend, self.backends["default"])
        return await backend.delete_file(file_path)
    
    async def file_exists(self, file_path: str, storage_backend: str = "default") -> bool:
        """检查文件是否存在"""
        backend = self.backends.get(storage_backend, self.backends["default"])
        return await backend.file_exists(file_path)
    
    def get_backend(self, storage_backend: str = "default") -> Optional[StorageBackend]:
        """获取指定的存储后端"""
        return self.backends.get(storage_backend, self.backends["default"])
    
    async def store_resource_file(
        self, 
        db: Session, 
        file_data: Union[BinaryIO, bytes], 
        original_name: str, 
        category_name: str, 
        user_id: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        version: str = "1.0.0"
    ) -> Optional[ResourceFile]:
        """存储资源文件并记录到数据库"""
        try:
            # 获取或创建资源类别
            category = db.query(ResourceCategory).filter(ResourceCategory.name == category_name).first()
            if not category:
                category = ResourceCategory(name=category_name, description=f"Category for {category_name} files")
                db.add(category)
                db.commit()
                db.refresh(category)
            
            # 上传文件
            content_type = self._get_content_type(original_name)
            storage_path = await self.upload_file(file_data, original_name, content_type)
            
            if not storage_path:
                return None
            
            # 计算文件大小
            if hasattr(file_data, 'read'):
                file_data.seek(0, 2)  # 移动到文件末尾
                file_size = file_data.tell()
                file_data.seek(0)  # 移回开头
            else:
                file_size = len(file_data)
            
            # 创建资源文件记录
            resource_file = ResourceFile(
                name=f"{uuid.uuid4()}_{original_name}",
                original_name=original_name,
                category_id=category.id,
                file_path=storage_path,
                file_size=file_size,
                mime_type=content_type,
                description=description,
                tags={"tags": tags} if tags else {},
                metadata_info={"version": version},
                uploaded_by=user_id,
                version=version
            )
            
            db.add(resource_file)
            db.commit()
            db.refresh(resource_file)
            
            return resource_file
        except Exception as e:
            logger.error(f"Failed to store resource file: {str(e)}")
            db.rollback()
            return None
    
    def _get_content_type(self, filename: str) -> Optional[str]:
        """根据文件扩展名推断内容类型"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'zip': 'application/zip',
            'rar': 'application/x-rar-compressed',
            'tar': 'application/x-tar',
            'gz': 'application/gzip',
            'py': 'text/x-python',
            'json': 'application/json',
            'xml': 'application/xml',
            'csv': 'text/csv'
        }
        return content_types.get(ext, 'application/octet-stream')


# 全局存储服务实例
storage_service = UnifiedStorageService()