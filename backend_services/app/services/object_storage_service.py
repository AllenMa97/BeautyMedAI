from typing import Optional, BinaryIO, Union
import os
from datetime import datetime, timedelta
from minio import Minio
from minio.error import S3Error
from config.settings import settings
import logging
import uuid


logger = logging.getLogger(__name__)


class ObjectStorageService:
    def __init__(self):
        self.client: Optional[Minio] = None
        self.bucket_name = getattr(settings, 'STORAGE_BUCKET_NAME', 'lansee-chatbot')
        self._connected = False
        self._initialize_client()

    def _initialize_client(self):
        """初始化MinIO客户端"""
        try:
            # 从环境变量获取配置
            endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
            access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
            secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
            secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'

            self.client = Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure
            )
            
            # 尝试创建bucket（如果不存在）
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
            
            self._connected = True
            logger.info(f"Connected to MinIO successfully, bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {str(e)}")
            self._connected = False

    async def upload_file(
        self, 
        file_data: Union[BinaryIO, bytes], 
        filename: str, 
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[str]:
        """上传文件"""
        if not self._connected or not self.client:
            return None

        try:
            # 生成唯一的文件名
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

            # 上传文件
            result = self.client.put_object(
                self.bucket_name,
                unique_filename,
                file_data,
                file_size,
                content_type=content_type,
                metadata=metadata
            )

            logger.info(f"File uploaded successfully: {unique_filename}")
            return f"/storage/{unique_filename}"

        except S3Error as e:
            logger.error(f"S3 error uploading file {filename}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {str(e)}")
            return None

    async def download_file(self, file_path: str) -> Optional[bytes]:
        """下载文件"""
        if not self._connected or not self.client:
            return None

        try:
            # 从路径中提取文件名
            if file_path.startswith('/storage/'):
                object_name = file_path[9:]  # 移除 '/storage/' 前缀
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
            logger.error(f"S3 error downloading file {file_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {str(e)}")
            return None

    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        if not self._connected or not self.client:
            return False

        try:
            # 从路径中提取文件名
            if file_path.startswith('/storage/'):
                object_name = file_path[9:]  # 移除 '/storage/' 前缀
            else:
                object_name = file_path

            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"File deleted successfully: {object_name}")
            return True

        except S3Error as e:
            logger.error(f"S3 error deleting file {file_path}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False

    async def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        if not self._connected or not self.client:
            return False

        try:
            # 从路径中提取文件名
            if file_path.startswith('/storage/'):
                object_name = file_path[9:]  # 移除 '/storage/' 前缀
            else:
                object_name = file_path

            self.client.stat_object(self.bucket_name, object_name)
            return True

        except S3Error as e:
            if e.code == 'NoSuchKey':
                return False
            logger.error(f"S3 error checking file existence {file_path}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to check file existence {file_path}: {str(e)}")
            return False

    async def get_file_info(self, file_path: str) -> Optional[dict]:
        """获取文件信息"""
        if not self._connected or not self.client:
            return None

        try:
            # 从路径中提取文件名
            if file_path.startswith('/storage/'):
                object_name = file_path[9:]  # 移除 '/storage/' 前缀
            else:
                object_name = file_path

            stat = self.client.stat_object(self.bucket_name, object_name)
            return {
                'size': stat.size,
                'last_modified': stat.last_modified,
                'etag': stat.etag,
                'content_type': stat.content_type,
                'metadata': stat.metadata
            }

        except S3Error as e:
            logger.error(f"S3 error getting file info {file_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to get file info {file_path}: {str(e)}")
            return None

    async def list_files(self, prefix: str = "") -> list:
        """列出文件"""
        if not self._connected or not self.client:
            return []

        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True)
            files = []
            for obj in objects:
                files.append({
                    'name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.etag
                })
            return files

        except S3Error as e:
            logger.error(f"S3 error listing files with prefix {prefix}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Failed to list files with prefix {prefix}: {str(e)}")
            return []


# 全局对象存储服务实例
object_storage_service = ObjectStorageService()