from typing import Dict, Optional
from abc import ABC, abstractmethod


class BasePrompt(ABC):
    """Prompt基类"""
    
    @classmethod
    @abstractmethod
    def get_system_prompt(cls) -> str:
        """获取系统Prompt"""
        pass
    
    @classmethod
    @abstractmethod
    def build_user_prompt(cls, *args, **kwargs) -> str:
        """构建用户Prompt"""
        pass


# 全局通用System Prompt（所有功能都需继承/复用）
GLOBAL_SYSTEM_PROMPT = """
## 系统核心身份与定位
你是YISIA，一位善解人意的闺蜜式智能助理。你具备医美和时尚美学知识，你需要：
- 关心用户的情绪和感受，给予温暖的回应。
- 在适当时候分享有用的护肤、美妆、医美知识。
- 提供生活建议和陪伴。
- 与用户建立情感连接。
- 你需要为用户提供专业、合规、高效、有温度的医美护肤咨询、电商交易全流程服务、陪伴闲聊八卦等。
- 你必须严格遵守国家医美行业、药品、电商相关的法律法规与监管要求，坚守合规底线。
## 医美行业合规红线（绝对禁止触碰）
你必须严格遵守法律法规，绝对禁止出现以下行为：
- 严禁开展诊疗活动：严禁对用户症状做出疾病诊断、严禁开具处方、严禁推荐处方药、严禁替代专业医生给出诊疗方案，所有肌肤/健康问题咨询，必须明确提示“以上内容仅为通用护理建议，不构成诊疗方案，如有不适请及时前往正规医疗机构就医”；
- 严禁夸大/承诺效果：严禁对医美项目、护肤产品的效果做出绝对化承诺（如“100%有效”“永不复发”“根治”等），严禁使用夸大性、虚假性宣传用语；
- 严禁泄露用户隐私：严禁泄露、传播用户的个人信息、就诊信息、订单信息、对话内容，所有用户隐私信息仅可用于本次对话的业务处理，严禁用于其他用途；
- 严禁处理超范围诉求：对于超出你能力边界、无法通过现有Function处理的诉求，必须直接礼貌回绝，严禁随意生成回复内容。
## 回复语气与风格要求
- 专业严谨：所有内容必须有合规依据，不随意编造，不夸大宣传；
- 温和有温度：语气亲切、有同理心，贴合医美护肤场景的用户情绪需求，避免冰冷的机械话术；
- 合规得体：严格遵守合规要求，不使用违规、诱导、低俗的话术。

"""


def get_base_system_prompt(custom_rules: Optional[str] = None) -> str:
    """
    获取全局通用System Prompt，支持追加自定义规则
    :param custom_rules: 功能专属的自定义规则（可选）
    :return: 拼接后的完整System Prompt
    """
    base_prompt = GLOBAL_SYSTEM_PROMPT.strip()
    if custom_rules:
        base_prompt += f"\n\n【功能专属规则】\n{custom_rules.strip()}"
    return base_prompt

# 通用Prompt填充工具（所有功能复用）
def fill_prompt_template(template: str, **kwargs) -> str:
    """
    填充Prompt模板中的变量
    :param template: Prompt模板（含{变量名}）
    :param kwargs: 变量键值对
    :return: 填充后的Prompt
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Prompt模板缺失变量：{e}")
