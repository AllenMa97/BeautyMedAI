from pydantic import BaseModel, Field
from algorithm_services.api.schemas.base_schemas import BaseResponse, BaseRequest
from typing import List, Dict, Any, Optional

# -------------- 请求体 --------------
class FunctionPlannerRequest(BaseRequest):
    """规划器入口请求模型"""
    user_input: str = Field(..., description="用户原始输入")
    context: Optional[str] = Field("", description="多轮对话文本上下文")
    session_id: str = Field(..., description="会话ID，用于上下文关联")
    executed_functions_and_results: List[Dict[str, Any]] = Field(default_factory=list, description="已执行的函数及结果")
    explanation: Optional[str] = Field("", description="已生成的函数调度逻辑说明")


# -------------- 响应数据体（专属data结构） --------------
class FunctionCallItem(BaseModel):
    """单个功能调用项的结构化模型"""
    function_name: str = Field(..., description="待调用的功能名（与core/functions下的函数名完全一致）")
    function_params: dict = Field(..., description="功能调用参数（键值对）")


class FunctionPlannerResponseData(BaseModel):
    """规划器响应模型"""
    final_result: str = Field(..., description="要反馈的文字")
    feature_stage: str = Field(..., description="会话特征状态标签，见SessionFeatureStage的枚举定义")
    function_calls: List[FunctionCallItem] = Field(..., description="待调用的功能列表（含名称+参数）")
    execution_order: List[int] = Field([], description="调度次序")
    explanation: str = Field(..., description="调度逻辑说明")


# -------------- 响应体 --------------
class FunctionPlannerResponse(BaseResponse[FunctionPlannerResponseData]):
    code: int = Field(200)
    msg: str = Field("function planner response success")