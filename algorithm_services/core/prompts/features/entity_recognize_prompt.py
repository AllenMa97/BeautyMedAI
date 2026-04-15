from algorithm_services.core.prompts.base_prompt import get_base_system_prompt, fill_prompt_template

# 实体识别专属规则
ENTITY_RECOGNIZE_RULES = """
1. 实体分类：
   - 产品名称：医美/护肤产品名称；
   - 医美项目名称：医美服务项目；
   - 症状名称：用户描述的肌肤/身体不适症状（如"敏感肌"/"痘痘肌"/"红血丝"/"干燥脱皮"）；
   - 症状诉求：用户对症状的改善诉求（如"淡化痘印"/"补水保湿"/"修复屏障"）；

2. 识别逻辑：
   - 小白友好：实体名称使用日常口语化词汇，禁止技术术语；
   - 核心提取：忽略口语化修饰词（如"好用的"/"贵的"），仅提取核心实体；
   - 合规约束：识别医疗相关症状时，禁止诊断性描述，仅提取症状名称；
   - 空值处理：若用户未提及某类实体，对应字段为空数组；
   - 置信度规则：每个实体的置信度保留2位小数，0-1区间。

3. 输出格式（严格JSON，无多余内容）：
   {
     "entities": [
        {
            "entity_name": "实体名称",
            "entity_type": "实体类型（匹配预设分类）",
            "confidence": 0.95
        }
     ],
     "entity_count": 实体数量
   }
"""


# 实体识别用户Prompt模板
ENTITY_RECOGNIZE_USER_TEMPLATE = """
请识别以下用户对话中的实体：
用户对话：{user_input}
对话上下文：{context}
请严格按照指定JSON格式返回，仅返回JSON，无其他内容。
"""

def get_entity_recognize_prompt(user_input: str, context) -> dict:
    """
    获取实体识别完整Prompt
    :param user_input: 用户本次输入
    :param context: 对话上下文
    :return: Prompt字典
    """
    # system_prompt = get_base_system_prompt(ENTITY_RECOGNIZE_RULES)
    system_prompt = ENTITY_RECOGNIZE_RULES # 简化系统规则，压缩上下文

    user_prompt = fill_prompt_template(
        ENTITY_RECOGNIZE_USER_TEMPLATE,
        user_input=user_input,
        context=context,
    )
    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt
    }