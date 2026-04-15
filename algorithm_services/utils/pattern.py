import re

def clean_think_tags(input_str):
    """
    移除字符串中的<think>标签及其内容，并提取JSON数据

    参数:
        input_str (str): 包含<think>标签的原始字符串

    返回:
        str: 清洗后的JSON字符串
    """
    # 移除所有<think>标签及其内容（含跨行内容）
    cleaned = re.sub(r'<think>.*?</think>', '', input_str, flags=re.DOTALL)

    return cleaned.strip()
