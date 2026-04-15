from pydantic import Field
from ..base_schemas import BaseRequest, BaseResponse

# -------------- 请求体 --------------
class LanguageSettingRequest(BaseRequest):
    user_input: str = Field(..., description="用户本次输入想设置的语言")

# -------------- 响应体 --------------
class LanguageSettingResponse(BaseResponse):
    code: int = Field(200)
    msg: str = Field("language setting response success")
