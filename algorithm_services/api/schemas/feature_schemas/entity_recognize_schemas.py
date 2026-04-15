from pydantic import BaseModel, Field, field_validator
from algorithm_services.api.schemas.base_schemas import BaseRequest, BaseResponse
from typing import Optional, List, Dict


# -------------- 请求体 --------------
class EntityRecognizeRequest(BaseRequest):
    """实体识别请求模型"""
    user_input: str = Field(..., description="用户本次输入（口语化）")
    context: Optional[str] = Field("", description="对话上下文")

# -------------- 响应数据体（专属data结构） --------------
class RecognizedEntity(BaseModel):
    """识别出的单个实体信息"""
    entity_name: str = Field(..., description="实体名称")
    entity_type: str = Field(..., description="实体类型")
    confidence: float = Field(..., ge=0, le=1, description="实体识别置信度")

class EntityRecognizeResponseData(BaseModel):
    """实体识别响应data结构"""
    entities: List[RecognizedEntity] = Field([], description="识别出的实体列表")
    entity_count: int = Field(0, description="识别的实体总数（自动计算，无需手动赋值）")

    # 自动计算 entity_count
    @field_validator("entity_count", mode="before")
    @classmethod
    def calculate_entity_count(cls, v, values):
        """
        触发时机：赋值 entity_count 前，自动计算 entities 列表长度
        values：包含已解析的其他字段（此处取 entities）
        """
        # 兼容 entities 未传的情况
        entities = values.data.get("entities", []) if hasattr(values, "data") else values.get("entities", [])
        return len(entities)

# -------------- 响应体 --------------
class EntityRecognizeResponse(BaseResponse[EntityRecognizeResponseData]):
    """实体识别响应体"""
    code: int = Field(200)
    msg: str = Field("entity recognize response success")
