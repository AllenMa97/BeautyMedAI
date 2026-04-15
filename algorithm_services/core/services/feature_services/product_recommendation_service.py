from algorithm_services.api.schemas.feature_schemas.recommendation_schemas import (
    RecommendationRequest, RecommendationResponse, RecommendationResponseData
)
from algorithm_services.core.services.knowledge_base_client import knowledge_base_client
from algorithm_services.utils.logger import get_logger

logger = get_logger(__name__)


class ProductRecommendationService:
    """产品推荐服务 - 调用 Knowledge Base Service 推荐API"""

    async def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        logger.info(f"产品推荐服务收到请求: {request.user_input}")
        
        try:
            response = await knowledge_base_client.recommend_products(
                query=request.user_input,
                user_context=request.context or {},
                strategy=request.recommendation_type or "hybrid",
                top_k=5,
            )
            
            if response.get("code") == 200:
                data = response.get("data", {})
                items = data.get("items", [])
                
                recommendations = []
                for item in items:
                    recommendations.append({
                        "id": item.get("id", ""),
                        "name": item.get("name", ""),
                        "brand": item.get("brand", ""),
                        "category": item.get("category", ""),
                        "price": item.get("price", 0),
                        "efficacy": item.get("efficacy", ""),
                        "score": item.get("score", 0),
                        "reason": item.get("reason", ""),
                    })
                
                overall_advice = data.get("overall_advice", "")
                routine_suggestion = data.get("routine_suggestion", "")
                
                reason = overall_advice if overall_advice else f"为您推荐{len(recommendations)}款产品"
                
                response_data = RecommendationResponseData(
                    recommendations=recommendations,
                    reason=reason
                )
                
                return RecommendationResponse(data=response_data)
            else:
                logger.warning(f"推荐服务返回错误: {response}")
                return RecommendationResponse(
                    data=RecommendationResponseData(
                        recommendations=[],
                        reason="推荐服务暂时不可用"
                    )
                )
                
        except Exception as e:
            logger.error(f"产品推荐服务调用失败: {e}")
            return RecommendationResponse(
                data=RecommendationResponseData(
                    recommendations=[],
                    reason=f"推荐服务调用失败: {str(e)}"
                )
            )


product_recommendation_service = ProductRecommendationService()
