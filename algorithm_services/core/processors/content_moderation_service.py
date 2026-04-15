"""
内容拦截服务
用于检测用户输入中的违规内容（黄赌毒暴政等）

三层拦截：
1. 违规词表（同步，快速失败）- 融合系统B的7类关键词
2. 公开 API（异步）- 预留接口
3. LLM 语义分析（异步）- 细粒度检测，qwen-flash提速
"""
import asyncio
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from algorithm_services.utils.logger import get_logger
from algorithm_services.large_model.llm_factory import llm_client_singleton, LLMRequest
from algorithm_services.core.prompts.features.content_moderation_prompt import get_content_moderation_prompt

logger = get_logger(__name__)

BLOCKLIST_FILE = "data/blocklist.txt"


@dataclass
class ModerateResult:
    """拦截结果"""
    blocked: bool
    reason: str = ""
    level: str = "pass"
    details: Optional[Dict[str, Any]] = None


@dataclass
class DetailedModerateResult(ModerateResult):
    """细粒度拦截结果（支持7类分类）"""
    violation_categories: List[str] = field(default_factory=list)
    detection_details: List[Dict[str, Any]] = field(default_factory=list)


class ContentModerationService:
    """
    内容拦截服务
    融合系统A和系统B的优势：
    - L1: 词表检测（系统A的blocklist + 系统B的7类关键词）
    - L2: 公开API（预留）
    - L3: LLM细粒度检测（7类分类）
    """

    CATEGORIES = ['political', 'violence', 'pornography', 'gambling', 'drug', 'hate', 'fake']

    def __init__(self):
        self.blocklist: set = set()
        self.keyword_detector = None
        self._load_blocklist()
        self._init_keyword_detector()

    def _load_blocklist(self):
        """加载违规词表"""
        if os.path.exists(BLOCKLIST_FILE):
            try:
                with open(BLOCKLIST_FILE, 'r', encoding='utf-8') as f:
                    words = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    self.blocklist = set(words)
                logger.info(f"加载违规词表: {len(self.blocklist)} 条")
            except Exception as e:
                logger.warning(f"加载违规词表失败: {e}")
                self.blocklist = set()
        else:
            logger.info("未找到违规词表文件")
            self.blocklist = set()

    def _init_keyword_detector(self):
        """初始化系统B的关键词检测器"""
        try:
            from core.moderation.keyword_detector import get_keyword_detector
            self.keyword_detector = get_keyword_detector()
            logger.info("关键词检测器初始化成功")
        except Exception as e:
            logger.warning(f"关键词检测器初始化失败: {e}")
            self.keyword_detector = None

    def check_blocklist(self, text: str) -> Optional[str]:
        """L1a: 通用违规词表匹配（同步，fast fail）"""
        if not self.blocklist:
            logger.debug("[内容检测-词表检测] 未加载词表，跳过检测")
            return None

        logger.info(f"[内容检测-词表检测] 开始检测文本: {text[:50]}...")
        text_lower = text.lower()
        for word in self.blocklist:
            if word.lower() in text_lower:
                logger.warning(f"[内容检测-词表检测] 检测到敏感词: {word}，文本: {text[:50]}...")
                return f"包含敏感词: {word}"

        logger.info(f"[内容检测-词表检测] 文本通过检测: {text[:50]}...")
        return None

    def check_category_keywords(self, text: str) -> List[Dict[str, Any]]:
        """L1b: 7类关键词检测（同步，快速）"""
        if not self.keyword_detector:
            return []

        logger.info(f"[内容检测-分类关键词] 开始检测文本: {text[:50]}...")
        keyword_results = self.keyword_detector.detect_with_details(text)

        detected_categories = []
        for category, detail in keyword_results.items():
            if category == 'overall':
                continue
            if detail.get('detected'):
                detected_categories.append({
                    'category': category,
                    'method': 'keyword',
                    'keywords': detail.get('keywords', []),
                    'confidence': 0.95
                })
                logger.warning(f"[内容检测-分类关键词] 检测到{category}违规，关键词: {detail.get('keywords')}")

        return detected_categories

    async def check_public_api(self, text: str) -> Optional[str]:
        """L2: 公开 API 检查（预留接口）"""
        logger.info(f"[内容检测-公共API检测] 开始检测文本: {text[:50]}...")
        await asyncio.sleep(0)
        logger.info(f"[内容检测-公共API检测] 文本通过检测: {text[:50]}...")
        return None

    async def check_llm_fast(self, text: str) -> Optional[str]:
        """L3a: LLM快速检测（判断是否违规，不区分类别）使用 qwen-flash 提速"""
        try:
            logger.info(f"[内容检测-LLM快速检测] 开始分析文本: {text[:50]}...")
            prompt = get_content_moderation_prompt(user_input=text)

            llm_request = LLMRequest(
                system_prompt=prompt["system_prompt"],
                user_prompt=prompt["user_prompt"],
                temperature=0.1,
                max_tokens=10,
                provider="aliyun",
                model="qwen-flash",
                source="content_moderation"
            )

            result = await llm_client_singleton.call_llm(llm_request)

            if isinstance(result, dict):
                response_text = result.get("text", "").strip()
                if response_text == "1":
                    logger.info(f"[内容检测-LLM快速检测] 文本通过检测: {text[:50]}...")
                    return None
                elif response_text == "0":
                    logger.warning(f"[内容检测-LLM快速检测] 检测到违规内容: {text[:50]}...")
                    return "LLM 判定违规"

            logger.info(f"[内容检测-LLM快速检测] 文本通过检测 (无明确结果): {text[:50]}...")
            return None

        except Exception as e:
            logger.warning(f"[内容检测-LLM快速检测] 语义分析失败: {e}，文本: {text[:50]}...")
            return None

    async def check_llm_category(self, text: str) -> List[Dict[str, Any]]:
        """L3b: LLM细粒度检测（判断具体违规类别）"""
        from core.prompts.features.moderation import (
            get_political_moderation_prompt,
            get_violence_moderation_prompt,
            get_pornography_moderation_prompt,
            get_gambling_moderation_prompt,
            get_drug_moderation_prompt,
            get_hate_moderation_prompt,
            get_fake_moderation_prompt,
        )

        category_prompts = {
            'political': get_political_moderation_prompt,
            'violence': get_violence_moderation_prompt,
            'pornography': get_pornography_moderation_prompt,
            'gambling': get_gambling_moderation_prompt,
            'drug': get_drug_moderation_prompt,
            'hate': get_hate_moderation_prompt,
            'fake': get_fake_moderation_prompt,
        }

        async def check_single_category(category: str, prompt_func) -> Optional[Dict[str, Any]]:
            try:
                prompt = prompt_func(text)
                llm_request = LLMRequest(
                    system_prompt=prompt["system_prompt"],
                    user_prompt=prompt["user_prompt"],
                    temperature=0.1,
                    max_tokens=10,
                    provider="aliyun",
                    model="qwen-flash",
                    source=f"content_moderation_{category}"
                )
                result = await llm_client_singleton.call_llm(llm_request)
                if isinstance(result, dict):
                    response_text = result.get("text", "").strip()
                    if response_text == "0":
                        return {'category': category, 'method': 'llm', 'confidence': 0.85}
            except Exception as e:
                logger.warning(f"[内容检测-LLM分类] {category}检测失败: {e}")
            return None

        tasks = [check_single_category(cat, func) for cat, func in category_prompts.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        detected = []
        for r in results:
            if isinstance(r, dict):
                detected.append(r)

        if detected:
            logger.warning(f"[内容检测-LLM分类] 检测到违规类别: {[d['category'] for d in detected]}")

        return detected

    async def moderate(self, user_input: str, detailed: bool = False) -> ModerateResult:
        """
        综合内容拦截检查

        Args:
            user_input: 待检测文本
            detailed: 是否返回细粒度结果（7类分类），默认False（快速模式）

        Returns:
            ModerateResult 或 DetailedModerateResult
        """
        logger.info(f"[内容检测-综合检测] 开始检测用户输入: {user_input[:50]}..., detailed={detailed}")

        block_reason = self.check_blocklist(user_input)
        if block_reason:
            logger.warning(f"[内容检测-综合检测] L1a 词表检测发现违规: {block_reason}")
            return ModerateResult(blocked=True, reason=block_reason, level="block")

        keyword_results = self.check_category_keywords(user_input)
        if keyword_results and not detailed:
            categories = [r['category'] for r in keyword_results]
            logger.warning(f"[内容检测-综合检测] L1b 关键词检测发现违规: {categories}")
            return DetailedModerateResult(
                blocked=True,
                reason=f"检测到违规类别: {', '.join(categories)}",
                level="keyword",
                violation_categories=categories,
                detection_details=keyword_results
            )

        api_task = asyncio.create_task(self.check_public_api(user_input))
        llm_task = asyncio.create_task(self.check_llm_fast(user_input))

        api_result = await api_task
        llm_result = await llm_task

        if api_result:
            logger.warning(f"[内容检测-综合检测] L2公共API检测发现违规: {api_result}")
            return ModerateResult(blocked=True, reason=api_result, level="api")

        if llm_result:
            if detailed:
                category_results = await self.check_llm_category(user_input)
                if category_results:
                    categories = [r['category'] for r in category_results]
                    return DetailedModerateResult(
                        blocked=True,
                        reason=f"LLM判定违规: {', '.join(categories)}",
                        level="llm",
                        violation_categories=categories,
                        detection_details=keyword_results + category_results
                    )
            logger.warning(f"[内容检测-综合检测] L3 LLM检测发现违规: {llm_result}")
            return ModerateResult(blocked=True, reason=llm_result, level="llm")

        if detailed and keyword_results:
            return DetailedModerateResult(
                blocked=False,
                reason="",
                level="pass",
                violation_categories=[],
                detection_details=keyword_results
            )

        logger.info(f"[内容检测-综合检测] 文本通过所有检测层级: {user_input[:50]}...")
        return ModerateResult(blocked=False, level="pass")


content_moderation_service = ContentModerationService()
