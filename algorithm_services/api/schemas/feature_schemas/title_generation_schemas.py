from pydantic import BaseModel, Field
from ..base_schemas import BaseRequest, BaseResponse
from typing import Optional, List

# -------------- 请求体 --------------
class TitleGenerationRequest(BaseRequest):
    """意图澄清请求模型"""
    user_input: str = Field(..., description="用户本次输入")

class TitleGenerationResponseData(BaseModel):
    """意图澄清响应数据"""
    title: str = Field(..., description="生成的应用标题")

class TitleGenerationResponse(BaseResponse[TitleGenerationResponseData]):
    """意图澄清响应模型"""
    code: int = Field(200)
    msg: str = Field("title generation response success")
