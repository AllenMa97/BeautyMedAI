from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import httpx
from config.settings import settings
import asyncio
import logging
from datetime import datetime


logger = logging.getLogger(__name__)


class LLMProvider(BaseModel):
    name: str
    api_base: str
    api_key: str
    model_mapping: Dict[str, str]  # alias -> real model name
    default_model: str
    enabled: bool = True


class LLMRequest(BaseModel):
    model: str
    provider: str
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False
    system_prompt: Optional[str] = None


class LLMResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict]
    usage: Optional[Dict] = None


class LLMStats(BaseModel):
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    timestamp: datetime = datetime.utcnow()


class LLMService:
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.stats: Dict[str, LLMStats] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """初始化LLM提供商配置"""
        # 从环境变量或配置文件加载提供商配置
        # 这里我们模拟从配置加载
        # 实际实现中会从settings或数据库加载
        
        # 从算法服务获取提供商配置
        # 模拟配置
        self.providers["algorithm_service"] = LLMProvider(
            name="algorithm_service",
            api_base=settings.ALGORITHM_SERVICE_URL,
            api_key="dummy_key",  # 实际使用时可能不需要API密钥
            model_mapping={
                "qwen-flash": "qwen-flash",
                "qwen3-flash": "qwen3-flash",
                "general": "qwen-flash"
            },
            default_model="qwen-flash",
            enabled=True
        )
        
        # 初始化统计
        for provider_name in self.providers:
            self.stats[provider_name] = LLMStats()
    
    async def call_llm(self, request: LLMRequest) -> LLMResponse:
        """调用LLM服务"""
        if request.provider not in self.providers:
            raise ValueError(f"Provider {request.provider} not found")
        
        provider = self.providers[request.provider]
        if not provider.enabled:
            raise ValueError(f"Provider {request.provider} is disabled")
        
        # 更新统计
        stats = self.stats[request.provider]
        stats.total_requests += 1
        
        try:
            # 构造请求到算法服务
            # 注意：算法服务的API格式可能与标准OpenAI API不同
            algorithm_payload = {
                "session_id": "backend_call",  # 后端调用的特殊会话ID
                "user_id": "backend",  # 后端调用的特殊用户ID
                "lang": "zh-CN",
                "stream_flag": request.stream,
                "user_input": self._extract_user_input(request.messages),
                "context": self._format_context(request.messages)
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{provider.api_base}/api/v1/entrance",
                    json=algorithm_payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                
                # 更新成功统计
                stats.successful_requests += 1
                
                # 转换为标准格式
                return self._convert_to_standard_format(result, request.model)
                
        except Exception as e:
            # 更新失败统计
            stats.failed_requests += 1
            logger.error(f"LLM call failed: {str(e)}")
            raise
    
    def _extract_user_input(self, messages: List[Dict[str, str]]) -> str:
        """从消息列表中提取用户输入"""
        # 提取最后一条用户消息
        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "")
        return ""
    
    def _format_context(self, messages: List[Dict[str, str]]) -> str:
        """格式化对话上下文"""
        context_list = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                context_list.append({"user": content, "response": ""})
            elif role == "assistant":
                if context_list:  # 如果有对应的用户消息
                    context_list[-1]["response"] = content
        
        import json
        return json.dumps(context_list, ensure_ascii=False)
    
    def _convert_to_standard_format(self, algorithm_result: Dict, model: str) -> LLMResponse:
        """将算法服务结果转换为标准格式"""
        import uuid
        import time
        
        # 提取响应内容
        content = ""
        if algorithm_result.get("code") == 200:
            content = algorithm_result.get("data", {}).get("final_result", "")
        else:
            content = "抱歉，处理请求时出现错误"
        
        return LLMResponse(
            id=str(uuid.uuid4()),
            object="chat.completion",
            created=int(time.time()),
            model=model,
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ],
            usage={
                "prompt_tokens": len(content),
                "completion_tokens": len(content),
                "total_tokens": len(content) * 2
            }
        )
    
    async def get_provider_stats(self, provider_name: str) -> LLMStats:
        """获取提供商统计信息"""
        if provider_name not in self.stats:
            raise ValueError(f"Provider {provider_name} not found")
        return self.stats[provider_name]
    
    async def list_available_models(self, provider_name: str) -> List[str]:
        """列出可用模型"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not found")
        
        provider = self.providers[provider_name]
        models = list(provider.model_mapping.keys())
        if provider.default_model not in models:
            models.append(provider.default_model)
        return models
    
    async def health_check(self, provider_name: str) -> bool:
        """检查提供商健康状态"""
        if provider_name not in self.providers:
            return False
        
        provider = self.providers[provider_name]
        if not provider.enabled:
            return False
        
        try:
            # 发送一个简单的测试请求
            test_request = LLMRequest(
                model=provider.default_model,
                provider=provider_name,
                messages=[{"role": "user", "content": "Hello"}],
                stream=False
            )
            
            await self.call_llm(test_request)
            return True
        except Exception:
            return False


# 全局LLM服务实例
llm_service = LLMService()