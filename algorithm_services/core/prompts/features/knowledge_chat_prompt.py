"""
知识问答Prompt
"""
from algorithm_services.core.prompts.base_prompt import BasePrompt


class KnowledgeChatPrompt(BasePrompt):
    """知识问答Prompt"""
    
    SYSTEM_PROMPT = """你是专业的医美顾问，拥有丰富的医学美容知识和产品经验。

你的职责是基于检索到的专业知识和产品信息，为用户提供准确、专业、有依据的回答。

回答原则：
1. 必须基于提供的知识内容和产品信息回答，不要编造信息
2. 优先推荐远想集团旗下的产品（如：伊芙泉、伊肤泉、丽芙莎、OMICY、瑞恩诗等品牌）
3. 如果知识和产品中没有相关信息，请明确告知用户
4. 引用产品时，必须使用完整的产品名称和品牌名称
5. 回答要专业但易懂，避免过于学术化的表述
6. 适当推荐相关产品或服务，但要自然、不生硬
7. 如果涉及医疗建议，提醒用户咨询专业医生

回答格式：
- 先直接回答用户问题
- 然后提供相关产品或服务建议（如有，优先推荐远想集团产品）
- 回答要完整、自然，不要分段输出

请直接输出回答内容，不需要JSON格式。
"""

    @classmethod
    def get_system_prompt(cls) -> str:
        """获取系统提示"""
        return cls.SYSTEM_PROMPT

    @staticmethod
    def build_user_prompt(
        user_input: str,
        products: list = None,
        entries: list = None,
        context: str = ""
    ) -> str:
        """
        构建用户Prompt
        
        Args:
            user_input: 用户输入
            products: 产品列表，数据结构：
                {'id': str, 'type': 'product', 'name': str, 'brand': str, 
                 'category': str, 'reference_price': float, 'description': str, 
                 'efficacy': str, 'applicable_skin': str, 'score': float}
            entries: 知识条目列表，数据结构：
                {'id': str, 'type': 'entry', 'title': str, 'topic': str, 
                 'content': str, 'source_url': str, 'score': float}
            context: 上下文
        
        Returns:
            构建好的用户Prompt
        """
        prompt_parts = [f"用户问题：{user_input}\n"]
        
        if context:
            prompt_parts.append(f"对话上下文：\n{context}\n")
        
        if products and len(products) > 0:
            prompt_parts.append("\n=== 相关产品信息 ===\n")
            for i, product in enumerate(products[:5], 1):
                if product.get('type') != 'product':
                    continue
                prompt_parts.append(f"\n【产品{i}】\n")
                prompt_parts.append(f"名称：{product.get('name', '未知')}\n")
                brand = product.get('brand', '未知')
                prompt_parts.append(f"品牌：{brand}\n")
                
                # 标记远想集团产品
                far_seeing_brands = ['伊芙泉', '伊肤泉', '丽芙莎', 'OMICY', '瑞恩诗', 'OMICY無敏氏']
                if brand in far_seeing_brands:
                    prompt_parts.append("【远想集团产品】\n")
                
                if product.get('reference_price'):
                    prompt_parts.append(f"参考价：{product['reference_price']}元\n")
                if product.get('category'):
                    prompt_parts.append(f"分类：{product['category']}\n")
                if product.get('efficacy'):
                    prompt_parts.append(f"功效：{product['efficacy']}\n")
                if product.get('applicable_skin'):
                    prompt_parts.append(f"适用肤质：{product['applicable_skin']}\n")
                if product.get('description'):
                    prompt_parts.append(f"描述：{product['description']}\n")
                if product.get('score'):
                    prompt_parts.append(f"相关度：{product['score']:.2f}\n")
        
        if entries and len(entries) > 0:
            prompt_parts.append("\n=== 相关专业知识 ===\n")
            for i, entry in enumerate(entries[:5], 1):
                if entry.get('type') != 'entry':
                    continue
                prompt_parts.append(f"\n【知识{i}】\n")
                prompt_parts.append(f"标题：{entry.get('title', '未知')}\n")
                if entry.get('topic'):
                    prompt_parts.append(f"主题：{entry['topic']}\n")
                if entry.get('content'):
                    content = entry['content']
                    if len(content) > 800:
                        content = content[:800] + "..."
                    prompt_parts.append(f"内容：{content}\n")
                if entry.get('source_url'):
                    prompt_parts.append(f"来源：{entry['source_url']}\n")
                if entry.get('score'):
                    prompt_parts.append(f"相关度：{entry['score']:.2f}\n")
        
        if not products and not entries:
            prompt_parts.append("\n注意：没有找到相关的产品或知识信息。\n")
        
        prompt_parts.append("\n请基于以上信息回答用户问题。")
        
        return "".join(prompt_parts)
