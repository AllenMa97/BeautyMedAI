"""
知识库服务客户端
统一调用 knowledge_base_service 的接口
"""
import httpx
import os
from typing import Dict, Optional, List, Any
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../config/KNOWLEDGE.env"))


class KnowledgeBaseClient:
    """调用 knowledge_base_service 的客户端"""
    
    def __init__(self):
        self.base_url = os.getenv("KNOWLEDGE_BASE_SERVICE_URL", "http://localhost:8002")
        self.api_prefix = "/api/v1"
        
        self.default_db_type = os.getenv("KNOWLEDGE_DEFAULT_DB_TYPE", "group")
        self.default_db_id = os.getenv("KNOWLEDGE_DEFAULT_DB_ID", "yuanxiang")
        self.default_search_mode = os.getenv("KNOWLEDGE_DEFAULT_SEARCH_MODE", "hybrid")
        self.default_top_k = int(os.getenv("KNOWLEDGE_DEFAULT_TOP_K", "10"))
        self.default_threshold = float(os.getenv("KNOWLEDGE_DEFAULT_THRESHOLD", "0.1"))
        self.default_search_type = os.getenv("KNOWLEDGE_DEFAULT_SEARCH_TYPE", "all")
    
    def _get_database_key(self, db_type: str = None, db_id: str = None) -> str:
        """
        获取数据库键
        
        Args:
            db_type: 数据库类型 (full/group/brand)
            db_id: 数据库ID
        
        Returns:
            数据库键 (如: full, group_yuanxiang, brand_yifuquan)
        """
        db_type = db_type or self.default_db_type
        db_id = db_id or self.default_db_id
        
        if db_type == "full":
            return "full"
        elif db_type == "group":
            return f"group_{db_id}"
        elif db_type == "brand":
            return f"brand_{db_id}"
        else:
            return "current"
    
    async def rag_query(
        self,
        query: str,
        top_k: int = 10,
        search_mode: str = "hybrid",
        use_ann: bool = True,
        threshold: float = 0.3,
        intent: str = None,
        entities: List[Dict[str, Any]] = None,
        constraints: List[Dict[str, Any]] = None,
    ) -> Dict:
        """
        RAG 统一查询接口
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            search_mode: 搜索模式 (vector/keyword/hybrid)
            use_ann: 是否使用 ANN 索引加速
            threshold: 相似度阈值
            intent: 查询意图（可选）
            entities: 实体列表（可选）
            constraints: 约束条件（可选）
        
        Returns:
            {
                "code": 200,
                "msg": "RAG查询完成",
                "data": {
                    "augmented_context": "组装后的上下文",
                    "chunks": [...],  # 检索结果列表
                    "total_chunks": 10,
                    "total_tokens": 500,
                    "sources": [...],  # 来源列表
                    "retrieval_metadata": {...}
                }
            }
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                payload = {
                    "query": query,
                    "top_k": top_k,
                    "search_mode": search_mode,
                    "use_ann": use_ann,
                    "threshold": threshold,
                }
                
                if intent:
                    payload["intent"] = intent
                if entities:
                    payload["entities"] = entities
                if constraints:
                    payload["constraints"] = constraints
                
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/rag/query",
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"code": 500, "msg": f"本次RAG查询（{self.base_url}{self.api_prefix}/rag/query）失败，请求体：{str(payload)}，报错信息: {str(e)}", "data": {}}
    
    async def query_rag(self, query: str, search_type: str = "all", top_k: int = 5) -> Dict:
        """查询知识库（兼容旧接口）"""
        return await self.rag_query(query=query, top_k=top_k)
    
    async def search_knowledge(
        self,
        query: str,
        top_k: int = 10,
        search_mode: str = "hybrid",
        use_ann: bool = True,
        threshold: float = 0.3,
        search_type: str = "all",
    ) -> Dict:
        """
        搜索知识库（使用 /knowledge/search 接口）
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            search_mode: 搜索模式 (vector/keyword/hybrid)
            use_ann: 是否使用 ANN 索引加速
            threshold: 相似度阈值
            search_type: 检索类型 (all/products/entries)
        
        Returns:
            {
                "code": 200,
                "msg": "搜索完成",
                "data": {
                    "query": "查询文本",
                    "results": [
                        {"type": "product", "name": "...", ...},
                        {"type": "entry", "title": "...", ...}
                    ],
                    "total_found": 10
                }
            }
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                payload = {
                    "query": query,
                    "top_k": top_k,
                    "search_mode": search_mode,
                    "use_ann": use_ann,
                    "threshold": threshold,
                    "search_type": search_type,
                }
                
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/knowledge/search",
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"code": 500, "msg": f"搜索失败: {str(e)}", "data": {}}
    
    async def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any] = None,
    ) -> Dict:
        """添加文档到知识库"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                payload = {
                    "doc_id": doc_id,
                    "content": content,
                }
                if metadata:
                    payload["metadata"] = metadata
                
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/rag/documents",
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"code": 500, "msg": f"添加文档失败: {str(e)}", "data": {}}
    
    async def add_knowledge(
        self,
        title: str,
        content: str,
        layer: str = "specific",
        source_url: str = "",
        tags: List[str] = None,
    ) -> Dict:
        """添加知识条目"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                payload = {
                    "title": title,
                    "content": content,
                    "layer": layer,
                    "source_url": source_url,
                    "tags": tags or [],
                }
                
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/knowledge/add_knowledge",
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"code": 500, "msg": f"添加知识失败: {str(e)}", "data": {}}
    
    async def add_product(self, product: Dict) -> Dict:
        """添加产品"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/knowledge/add_product",
                    json=product
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"code": 500, "msg": f"添加产品失败: {str(e)}", "data": {}}
    
    async def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}{self.api_prefix}/rag/stats"
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"code": 500, "msg": f"获取统计信息失败: {str(e)}", "data": {}}
    
    async def build_ann_index(self) -> Dict:
        """构建 ANN 索引"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/rag/build-ann-index"
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"code": 500, "msg": f"构建索引失败: {str(e)}", "data": {}}
    
    async def get_ann_stats(self) -> Dict:
        """获取 ANN 索引统计信息"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}{self.api_prefix}/rag/ann-stats"
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"code": 500, "msg": f"获取索引统计失败: {str(e)}", "data": {}}
    
    async def health_check(self) -> Dict:
        """健康检查"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}{self.api_prefix}/rag/health"
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"status": "unhealthy", "error": str(e)}


knowledge_base_client = KnowledgeBaseClient()
