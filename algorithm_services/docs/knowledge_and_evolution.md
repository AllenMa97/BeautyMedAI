# 知识系统与进化体系

## 一、知识系统架构

Lansee Chatbot 采用双轨知识系统：静态知识库 + 动态进化系统。

### 1.1 两套知识系统对比

| 系统 | 存储位置 | 数据来源 | 日志标识 |
|------|---------|---------|---------|
| **知识库系统** | `data/knowledge/` | 手动/自动积累 | `加载 behavior 知识: 120 条` |
| **运行时进化系统** | `data/evolution/` | 系统分析生成 | `加载进化状态: 知识0条, 行为0条` |

### 1.2 知识库分类

位置：`data/knowledge/`

| 类型 | 文件 | 用途 |
|------|------|------|
| `behavior` | behavior.json | 行为知识 |
| `feature` | feature.json | 特征知识 |
| `interaction` | interaction.json | 交互知识 |
| `correction` | correction.json | 纠正知识 |

---

## 二、知识库系统

### 2.1 KnowledgeStore

位置：`core/managers/knowledge_store.py`

```python
class KnowledgeStore:
    """统一的知识存储管理"""
    def __init__(self, knowledge_type: str):
        # 支持类型: behavior|feature|interaction|correction
        self.items: Dict[str, KnowledgeItem] = {}

    def add(self, content, embedding=None, source="system"):
        """添加知识"""

    def get_all(self):
        """获取所有知识"""
```

### 2.2 知识条目结构

```python
@dataclass
class KnowledgeItem:
    content: str                    # 知识内容
    embedding: Optional[List[float]] # 向量表示
    metadata: KnowledgeMetadata     # 元数据

@dataclass
class KnowledgeMetadata:
    type: str           # knowledge_type
    source: str         # 来源
    created_at: str     # 创建时间
    usage_count: int    # 使用次数
```

---

## 三、运行时进化系统

### 3.1 SelfEvolutionManager

位置：`core/managers/self_evolution_manager.py`

**启动两个后台线程**：

1. **系统分析线程**（每10分钟）
2. **知识管理线程**（每30分钟）

### 3.2 系统分析流程

```python
async def perform_system_analysis(self):
    # 1. 获取所有活跃session
    sessions = session_manager.sessions.values()

    # 2. 提取需要分析的数据
    user_profile = session.user_profile
    error_records = session.error_records
    recent_dialogs = session.turns[-5:]

    # 3. 调用进化服务分析
    evolution_results = await self_evolution_service.analyze_system_performance(
        user_profile=user_profile,
        error_records=error_records,
        recent_dialogs=recent_dialogs
    )

    # 4. 应用进化结果
    if evolution_results:
        await self._apply_evolution_results(evolution_results)
```

### 3.3 进化结果类型

```python
evolution_results = {
    "knowledge_updates": [...],      # 知识更新
    "behavior_improvements": [...], # 行为改进
    "interaction_adjustments": [...], # 交互调整
    "feature_enhancements": [...]    # 特征增强
}
```

---

## 四、知识管理（去重与相似度检测）

### 4.1 去重机制

位置：`core/managers/self_evolution_manager.py`

**每30分钟执行一次**：

1. **MD5去重**：基于内容哈希去重
2. **向量相似度去重**：基于embedding相似度（阈值0.8）

```python
def _remove_duplicate_knowledge(self) -> int:
    """MD5去重"""
    unique_knowledge = {}
    for key, value in all_knowledge.items():
        content_hash = hashlib.md5(str(value.content).encode()).hexdigest()
        if content_hash not in unique_knowledge:
            unique_knowledge[content_hash] = (key, value)

async def _remove_similar_knowledge(self) -> int:
    """向量相似度去重（阈值0.8）"""
    # 计算余弦相似度
    similarity_matrix = torch.mm(embeddings_norm, embeddings_norm.t())
    # 移除相似度 > 0.8 的条目
```

---

## 五、自进化服务

### 5.1 SelfEvolutionService

位置：`core/services/self_evolution_service.py`

```python
class SelfEvolutionService:
    """运行时进化服务"""

    def __init__(self):
        # 运行时知识/行为存储
        self._runtime_knowledge = {}  # 知识
        self._runtime_behavior = {}   # 行为
```

**分析维度**：
- 用户画像特征提取
- 错误模式分析
- 对话质量评估
- 交互策略优化

---

## 六、相关文件索引

| 文件 | 说明 |
|------|------|
| `core/managers/knowledge_store.py` | 知识存储管理 |
| `core/managers/self_evolution_manager.py` | 自进化管理 |
| `core/services/self_evolution_service.py` | 进化服务 |
| `data/knowledge/behavior.json` | 行为知识库 |
| `data/knowledge/feature.json` | 特征知识库 |
| `data/knowledge/interaction.json` | 交互知识库 |
| `data/knowledge/correction.json` | 纠正知识库 |

---

## 七、注意事项

1. **两套系统独立**：知识库系统(`data/knowledge/`)和运行时进化系统(`data/evolution/`)是分开的
2. **日志区分**：
   - `加载 behavior 知识: 120 条` → 知识库系统
   - `加载进化状态: 知识0条, 行为0条` → 运行时进化系统
3. **进化触发**：需要系统运行一段时间后才会积累运行时进化数据
