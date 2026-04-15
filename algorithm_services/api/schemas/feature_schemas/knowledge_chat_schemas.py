from pydantic import BaseModel, Field
from ..base_schemas import BaseRequest, BaseResponse
from typing import List, Optional, Dict, Any


class KnowledgeChatRequest(BaseRequest):
    user_input: str = Field(..., description="用户本次输入")
    context: Optional[str] = Field("", description="对话上下文")
    data: Optional[Dict[str, Any]] = Field(None, description="包含 knowledge_retrieval 的结果")


class KnowledgeChatData(BaseModel):
    answer: str = Field("", description="生成的回答")
    sources: List[str] = Field([], description="引用来源")
    confidence: float = Field(0.0, description="置信度")
    has_knowledge: bool = Field(False, description="是否有知识支撑")


class KnowledgeChatResponse(BaseResponse[KnowledgeChatData]):
    code: int = Field(200)
    msg: str = Field("知识问答成功")
    data: KnowledgeChatData = Field(
        default_factory=lambda: KnowledgeChatData(
            answer="", sources=[], confidence=0.0, has_knowledge=False
        )
    )
