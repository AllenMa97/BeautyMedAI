from algorithm_services.api.schemas.feature_schemas.knowledge_retrieval_schemas import (
    KnowledgeRetrievalRequest,
    KnowledgeRetrievalResponse,
    KnowledgeRetrievalData,
    ProductItem,
    KnowledgeEntry,
)
from algorithm_services.core.services.knowledge_base_client import knowledge_base_client
from algorithm_services.utils.logger import get_logger
from algorithm_services.utils.performance_monitor import monitor_async

logger = get_logger(__name__)


class KnowledgeRetrievalService:
    description = "知识检索，从知识库检索相关产品和知识条目"
    
    @monitor_async(name="knowledge_retrieval_retrieve", log_threshold=1.0)
    async def retrieve(self, request: KnowledgeRetrievalRequest) -> KnowledgeRetrievalResponse:
        """
        知识检索服务
        
        调用 Knowledge Base Service 的检索接口
        返回: products + entries（区分产品和知识条目）
        
        注意：这里只负责 Retrieval，不负责 Augmentation 和 Generation
        """
        try:
            entities = request.entities
            if entities:
                entities = [
                    {"entity_value": e, "entity_type": "unknown"} if isinstance(e, str) else e
                    for e in entities
            ]
            
            result = await knowledge_base_client.search_knowledge(
                query=request.user_input,
                top_k=request.top_k,
                search_mode="hybrid",  # 混合检索模式
                use_ann=True,  # 启用ANN向量检索
                threshold=0.3,  # 设置合适的阈值
                search_type=request.search_type,
            )
            
            if result.get("code") != 200:
                logger.warning(f"知识检索失败: {result.get('msg')}")
                return KnowledgeRetrievalResponse(
                    code=500,
                    msg=result.get("msg", "知识检索失败"),
                    data=KnowledgeRetrievalData(
                        products=[],
                        entries=[],
                        total_products=0,
                        total_entries=0,
                        query=request.user_input,
                    )
                )
            
            data = result.get("data", {})
            results = data.get("results", [])
            
            products = []
            entries = []
            
            for item in results:
                item_type = item.get("type", "entry")
                
                if item_type == "product":
                    products.append(ProductItem(
                        id=item.get("id", ""),
                        type="product",
                        name=item.get("name", ""),
                        brand=item.get("brand"),
                        category=item.get("category"),
                        reference_price=item.get("reference_price"),
                        description=item.get("description"),
                        efficacy=item.get("efficacy"),
                        applicable_skin=item.get("applicable_skin"),
                        score=item.get("vector_score") or item.get("score"),
                    ))
                else:
                    entries.append(KnowledgeEntry(
                        id=item.get("id", ""),
                        type="entry",
                        title=item.get("title", ""),
                        topic=item.get("topic"),
                        content=item.get("content"),
                        source_url=item.get("source_url"),
                        score=item.get("vector_score") or item.get("score"),
                    ))
            
            return KnowledgeRetrievalResponse(
                code=200,
                msg="知识检索成功",
                data=KnowledgeRetrievalData(
                    products=products,
                    entries=entries,
                    total_products=len(products),
                    total_entries=len(entries),
                    query=request.user_input,
                )
            )
        except Exception as e:
            logger.error(f"知识检索异常: {e}")
            return KnowledgeRetrievalResponse(
                code=500,
                msg=f"知识检索异常: {str(e)}",
                data=KnowledgeRetrievalData(
                    products=[],
                    entries=[],
                    total_products=0,
                    total_entries=0,
                    query=request.user_input,
                )
            )


knowledge_retrieval_service = KnowledgeRetrievalService()
