# 记忆系统与上下文管理

## 一、记忆系统架构

Lansee Chatbot 采用多层级记忆体系，平衡短期记忆容量与长期知识沉淀。

### 1.1 记忆层级

| 层级 | 存储位置 | 用途 | 生命周期 |
|------|---------|------|---------|
| **短期记忆** | `session.turns` | 当前会话的轮次历史 | 会话期间 |
| **压缩记忆** | `session.dialog_summary` | 长对话压缩摘要 | 会话期间 |
| **用户画像** | `session.user_profile` | 用户特征偏好 | 长期 |
| **错误纠正** | `session.error_records` | 用户纠正的信息 | 长期 |
| **知识图谱** | `user_knowledge_graph` | 结构化知识 | 长期 |

### 1.2 数据模型

**会话数据 (SessionData)** - `session_factory.py`

```python
class SessionData:
    # 状态/记忆相关字段
    feature_stage: str        # 会话特征状态标签
    context: str            # 全局对话上下文
    dialog_summary: str     # 对话摘要（长话短说）

    # 轮次列表（核心）
    turns: List[TurnData]   # 全会话的轮次数据列表

    # 用户画像（长期记忆）
    user_profile: Dict      # 存储用户画像信息
    error_records: List     # 存储用户纠正的信息
```

**轮次数据 (TurnData)**

```python
class TurnData:
    user_query: str              # 用户输入
    ai_response: str             # AI响应
    plan_functions: list         # 调用的功能列表
    user_query_intent: str       # 识别的意图
    user_query_entities: Dict    # 识别的实体
```

---

## 二、长上下文管理

### 2.1 对话摘要机制

**自动触发条件** - `function_planner_service.py`

```python
def should_execute_dialog_summary(self, request, session) -> bool:
    # 条件1: 用户输入长度 > 200字符
    if user_input_length >= 200:
        return True

    # 条件2: 会话历史 >= 2轮
    if history_length >= 2:
        return True

    # 条件3: 距离上次摘要 > 5分钟（避免重复摘要）
    if (current_time - last_summary_time) < 300:
        return False
```

### 2.2 上下文构建

在调用 free_chat 前，会构建精简上下文：

```python
def build_context(self, request, session) -> str:
    parts = []

    # 1. 对话摘要（精简版）
    if session.dialog_summary:
        parts.append(f"【之前对话摘要】{session.dialog_summary}")

    # 2. 最近3轮对话（保持新鲜感）
    if session.turns:
        recent = session.turns[-3:]
        for turn in recent:
            parts.append(f"用户: {turn.user_query}")
            parts.append(f"助手: {turn.ai_response}")

    return "\n".join(parts)
```

### 2.3 上下文流程图

```
用户输入
    │
    ▼
┌─────────────────────────────────────────┐
│          对话摘要判断                    │
│  (输入>200字符 或 历史>=2轮 或 间隔>5分钟)│
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│      生成对话摘要 (DialogSummary)        │
│   长对话 → 简短摘要，存入 dialog_summary │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│           构建上下文                       │
│  dialog_summary + 最近3轮对话            │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│           Free Chat 调用                  │
│       (保持上下文连续性)                  │
└─────────────────────────────────────────┘
```

---

## 三、记忆召回系统

### 3.1 MemoryRecallService

位置：`core/services/feature_services/memory_recall_service.py`

**支持的多维度检索**：

1. **关键词检索**：从用户输入提取实体/关键词
2. **时间线检索**：按时间顺序召回
3. **实体检索**：识别人名、地点、机构等
4. **向量检索**（预留接口）：基于embedding相似度

### 3.2 召回流程

```python
async def recall(self, request: MemoryRecallRequest):
    # 1. 从用户输入提取实体
    entities = await self._extract_entities(request.user_input)

    # 2. 根据实体和召回类型检索记忆
    memories = await self._recall_memories(
        user_id=request.user_id,
        entities=entities,
        recall_type=request.recall_type
    )

    return recalled_memories
```

---

## 四、用户画像（长期记忆）

### 4.1 UserProfileService

位置：`core/services/feature_services/user_profile_service.py`

**自动更新的用户特征**：
- 兴趣爱好
- 语言风格
- 交互偏好
- 情感倾向

### 4.2 触发条件

```python
def should_update_user_profile(self, request, session) -> bool:
    # 条件1: 会话历史 >= 5轮
    if history_length >= 5:
        return True

    # 条件2: 距离上次更新 > 5分钟
    if (current_time - last_update_time) < 300:
        return False
```

---

## 五、会话持久化

### 5.1 存储方式

- 本地文件存储：`sessions/` 目录
- 格式：Pickle序列化
- 文件命名：`session_{session_id}.pkl`

### 5.2 加载时机

每个请求进入时自动加载会话：
```python
session = await session_manager.get_session(request.session_id, request.user_id)
```

---

## 六、相关文件索引

| 文件 | 说明 |
|------|------|
| `session/session_factory.py` | 会话数据模型 |
| `core/services/feature_services/memory_recall_service.py` | 记忆召回服务 |
| `core/services/feature_services/dialog_summary_service.py` | 对话摘要服务 |
| `core/services/feature_services/user_profile_service.py` | 用户画像服务 |
| `core/services/feature_services/function_planner_service.py` | 上下文构建逻辑 |
