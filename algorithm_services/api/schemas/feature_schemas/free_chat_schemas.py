from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from algorithm_services.api.schemas.base_schemas import BaseRequest, BaseResponse


class FreeChatRequest(BaseRequest):
    user_input: str = Field(..., description="用户输入文本")
    lang: Optional[str] = Field(None, description="所需语言（bcp47）")
    context: Optional[str] = Field("", description="对话上下文")



class FreeChatResponseData(BaseModel):
    chat_response: str = Field(..., description="闲聊对话回复")
    emotional_tone: str = Field(..., description="回复的情感基调（温暖/活泼/安慰/鼓励等")

class FreeChatResponse(BaseResponse[FreeChatResponseData]):
    code: int = Field(200)
    msg: str = Field("free chat response success")


