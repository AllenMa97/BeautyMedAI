from algorithm_services.api.schemas.feature_schemas.entity_recognize_schemas import (
    EntityRecognizeRequest, EntityRecognizeResponseData, EntityRecognizeResponse, RecognizedEntity
)
from algorithm_services.core.prompts.features.entity_recognize_prompt import get_entity_recognize_prompt
from algorithm_services.large_model.llm_factory import llm_client_singleton, LLMRequest
from algorithm_services.utils.logger import get_logger

logger = get_logger(__name__)

# 可配置当前Service的默认服务商/模型（也可从配置文件读取）
DEFAULT_PROVIDER = "aliyun"
DEFAULT_MODEL = "qwen-flash"  # 快速
LLM_REQUEST_MAX_TOKENS = int(512) # 32768是Qwen flash模型的输入+输出的总token上限


# DEFAULT_PROVIDER = "lansee"
# DEFAULT_MODEL = "Qwen/Qwen2.5-32B-Instruct-AWQ"
# LLM_REQUEST_MAX_TOKENS = int(512)



LLM_REQUEST_TEMPERATURE = float(0.2)

class EntityRecognizeService:
    """实体识别Service"""
    description = "实体识别，提取用户输入中的关键实体"
    
    async def recognize(self, request: EntityRecognizeRequest) -> EntityRecognizeResponse:
        """执行实体识别"""
        # 1. 获取Prompt
        prompt = get_entity_recognize_prompt(
            user_input=request.user_input,
            context=request.context,
        )

        # 2. 调用LLM（指定服务商和模型，低温度保证稳定性）
        llm_request = LLMRequest(
            system_prompt=prompt["system_prompt"],
            user_prompt=prompt["user_prompt"],
            temperature=LLM_REQUEST_TEMPERATURE,
            max_tokens=LLM_REQUEST_MAX_TOKENS,
            response_format={"type": "json_object"},
            provider=DEFAULT_PROVIDER,
            model=DEFAULT_MODEL
        )
        try:
            llm_result = await llm_client_singleton.call_llm(llm_request)
            logger.info(f"实体识别LLM返回结果：{llm_result}")

            # 3. 转换为结构化数据（容错处理）
            entities_list = []
            raw_entities = llm_result.get("entities", [])
            for item in raw_entities:
                try:
                    entity = RecognizedEntity(
                        entity_name=item.get("entity_name", ""),
                        entity_type=item.get("entity_type", ""),
                        confidence=float(item.get("confidence", 0.0))
                    )
                    entities_list.append(entity)
                except Exception as e:
                    logger.warning(f"单个实体解析失败：{str(e)}，跳过该实体")
                    continue

            # 自动计算entity_count（依赖validator）
            response_data = EntityRecognizeResponseData(
                entities=entities_list
            )

            return EntityRecognizeResponse(
                code=200,
                msg="entity recognize success",
                data=response_data
            )

        except Exception as e:
            logger.error(f"实体识别结果解析失败：{str(e)}")
            # 降级返回空数据
            tmp_data = EntityRecognizeResponseData(entities=[], entity_count=0)
            return EntityRecognizeResponse(
                code=500,
                msg=f"实体识别结果解析失败：{str(e)}",
                data=tmp_data
            )


entity_recognize_service = EntityRecognizeService()