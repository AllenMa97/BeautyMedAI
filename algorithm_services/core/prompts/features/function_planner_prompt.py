import json

from typing import Dict, List, Any, Optional

from algorithm_services.core.prompts.base_prompt import get_base_system_prompt, fill_prompt_template
from algorithm_services.api.schemas.schema_kit import get_schema_by_func_name

PLANNER_BASIC_PROMPT = '''
你是智能规划器，负责决定调用哪些函数来处理用户输入。

用户最新输入：{user_input}
对话上下文：{context}
之前函数执行结果：{intermediate_results_info}

会话状态标签(feature_stage)：
- COMPANIONSHIP_MODE 陪伴倾听
- ADVICE_MODE 提供建议
- CASUAL_CHAT_MODE 闲聊
- EMOTIONAL_SUPPORT_MODE 情感支持
- LEARNING_MODE 知识学习
- BEAUTY_CONSULTATION_MODE 美学咨询
- PRODUCT_CONSULTATION_MODE 产品咨询
- MEDICAL_CONSULTATION_MODE 医美咨询
- SKINCARE_CONSULTATION_MODE 护肤咨询
'''


PLANNER_FUNCTION_REGISTRATION_PROMPT = '''
### 可调用功能列表 与 调用时传入的参数规范
{
  # 知识检索 - 从知识库检索相关知识片段（医美/产品/成分/功效等）
  "knowledge_retrieval": {
    "user_input": "字符串 | 必填 | 用户本次输入",
    "intent": "字符串 | 非必填 | 用户意图",
    "entities": "列表 | 非必填 | 识别的实体",
    "top_k": "整数 | 非必填 | 检索结果数量，默认5",
    "search_type": "字符串 | 非必填 | 检索类型: all/products/entries"
  },
  # 对话摘要生成器
  "dialog_summary": {
    "dialog_content": "列表【字符串】 | 必填 | 对话内容列表，每个项为一次用户输入和 Agent 回答",
    "summary_length": "整数 | 非必填 | 摘要长度限制",
    "summary_type": "字符串 | 非必填 | 摘要类型：brief(简洁)/detail(详细)",
    "data": 其他参考信息
  },
  # 实体识别
  "entity_recognize": {
    "user_input": "字符串 | 必填 | 用户本次输入",
    "context": "字符串 | 非必填 | 对话上下文",
    "data": 其他参考信息
  },
  # 意图澄清
  "intent_clarify": {
    "user_input": "字符串 | 必填 | 用户本次输入",
    "recognized_intent": "字符串 | 必填 | 已识别的意图（JSON 字符串）",
    "recognized_entities": "字符串 | 必填 | 已识别的实体（JSON 字符串）",
    "context": "字符串 | 非必填 | 对话上下文",
    "data": 其他参考信息
  },   
  # 文本摘要生成器
  "text_summary": {
    "user_input": "字符串 | 必填 | 用户本次输入",
    "data": 其他参考信息
  },
}

### 功能选择规则

## 核心原则：医美/护肤/产品相关问题 → 必须调用 knowledge_retrieval

### 1. 必须调用 knowledge_retrieval 的场景（优先级最高）
以下关键词/场景出现时，必须调用 knowledge_retrieval：
- **皮肤问题**: 色斑、雀斑、晒斑、黄褐斑、老年斑、痘印、疤痕、皱纹、细纹、松弛、毛孔粗大、黑头、粉刺、痤疮、痘痘、敏感、红血丝、暗沉、肤色不均、干燥、出油、黑眼圈、眼袋、泪沟、法令纹、抬头纹、鱼尾纹
- **医美项目**: 玻尿酸、肉毒素、水光针、热玛吉、超声刀、激光、光子嫩肤、皮秒、点阵激光、黄金微针、Fotona4D、嗨体、童颜针、少女针、双眼皮、隆鼻、吸脂、填充
- **护肤成分**: 玻尿酸、烟酰胺、维C、视黄醇、A醇、水杨酸、果酸、神经酰胺、角鲨烷、胶原蛋白、胜肽、熊果苷、传明酸
- **产品咨询**: 有什么产品、推荐产品、哪个好、怎么选、效果怎么样、多少钱、价格、品牌
- **功效需求**: 美白、淡斑、祛痘、抗衰、紧致、补水、保湿、修复、抗敏、控油、收缩毛孔
- **追问场景**: 用户追问"有什么好用的"、"哪个效果好"、"最近有什么"等，结合上下文是医美/护肤相关

### 2. 调用 intent_clarify 的场景（仅限以下情况）
- 用户输入完全模糊，无法判断任何意图（如"那个"、"这个"、"嗯"）
- 用户输入与医美/护肤完全无关，且无法确定用户想要什么
- 重要：如果用户提到了任何皮肤问题、产品、成分、医美项目，不要调用 intent_clarify，而是调用 knowledge_retrieval

### 重要提示
- 如果不需要任何功能调用，返回空的 function_calls: []
'''

PLANNER_OUTPUT_FORMAT_PROMPT = '''
### 输出格式（严格JSON）
{
  "feature_stage": "会话特征状态标签",
  "function_calls": [
      {
          "function_name": "功能名0",
          "function_params": {
            "参数名1": "参数值1",
            "参数名2": "参数值2",...
          }
        },
        {
          "function_name": "功能名1",
          "function_params": {
            "参数名1": "参数值1",
            "参数名2": "参数值2", ...
          }
        },
        {
          "function_name": "功能名2",
          "function_params": {
            "参数名1": "参数值1",
          }
        }, ...
  ],
  "execution_order": [0,1,2...], # 哪怕只调用一个函数，也要填入0
  "explanation": "函数调度逻辑说明" # 哪怕只调用一个函数，也要填入原因
}'''


YISIA_PLANNER_RULES = PLANNER_BASIC_PROMPT + PLANNER_FUNCTION_REGISTRATION_PROMPT + PLANNER_OUTPUT_FORMAT_PROMPT


PLANNER_USER_TEMPLATE = """
会话ID：{session_id}
用户最新对话：{user_input}
对话上下文：{context}
已执行的函数及结果:{executed_functions_and_results}
已生成的函数调度逻辑说明：{explanation}
请根据上述信息，生成功能调度计划。
"""


def get_yisia_function_planner_prompt(
    session_id: str,
    user_input: str,
    context: str,
    executed_functions_and_results: Optional[List[Dict[str, Any]]],
    explanation: str,
    time_location_info: Optional[Dict[str, Any]] = None,
    trending_topics_info: Optional[Dict[str, Any]] = None,
    intermediate_results: Optional[Dict[str, Any]] = None
) -> dict:
    """获取YISIA规划器Prompt（支持会话状态）"""
    if time_location_info is None:
        time_location_info = {
            "time_info": {},
            "location_info": {},
            "combined_context": "无法获取当前时间和位置信息"
        }
    
    if trending_topics_info is None:
        trending_topics_info = {
            "weibo_hot": [],
            "baidu_hot": [],
            "xiaohongshu_hot": [],
            "combined_context": "无法获取当前热搜信息"
        }
    
    if intermediate_results is None:
        intermediate_results = {}

    try:
        intermediate_results_str = json.dumps(intermediate_results, ensure_ascii=False)
    except Exception as e:
        intermediate_results_str = str(intermediate_results)
    
    system_prompt_with_context = PLANNER_BASIC_PROMPT.format(
        user_input=user_input,
        context=context,
        intermediate_results_info=intermediate_results_str
    )
    
    full_prompt = system_prompt_with_context + PLANNER_FUNCTION_REGISTRATION_PROMPT + PLANNER_OUTPUT_FORMAT_PROMPT
    system_prompt = full_prompt

    try:
        executed_functions_and_results_str = json.dumps(
            executed_functions_and_results,
            ensure_ascii=False,
        )
    except Exception as e:
        executed_functions_and_results_str = ""

    user_prompt = fill_prompt_template(
            PLANNER_USER_TEMPLATE,
            session_id=session_id,
            user_input=user_input,
            context=context,
            executed_functions_and_results=executed_functions_and_results_str,
            explanation=explanation,
    )

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt
    }
