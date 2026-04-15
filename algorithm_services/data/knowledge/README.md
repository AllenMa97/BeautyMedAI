# 知识存储目录

本目录存放算法服务的各类知识数据，采用 JSON 文件格式持久化存储。

## 文件说明

| 文件名 | 知识类型 | 说明 | 管理服务 |
|--------|----------|------|----------|
| `behavior.json` | 行为知识 | 用户行为模式、习惯等知识 | `KnowledgeStore` |
| `feature.json` | 特征知识 | 用户特征、属性等知识 | `KnowledgeStore` |
| `interaction.json` | 交互知识 | 交互模式、对话策略等知识 | `KnowledgeStore` |
| `correction.json` | 纠正知识 | 错误纠正、反馈等知识 | `KnowledgeStore` |
| `trending.json` | 热搜知识 | 各平台热搜数据缓存 | `TrendingTopicsService` |
| `user_styles.json` | 用户风格 | 用户语言风格特征 | `UserStyleLearningService` |
| `user_knowledge_graphs.json` | 用户知识图谱 | 用户实体关系图谱 | `UserKnowledgeGraphService` |

## 数据结构

### 1. 行为/特征/交互/纠正知识 (KnowledgeStore)

```json
{
  "knowledge_type": "behavior",
  "updated_at": "2026-04-13T10:00:00",
  "items": {
    "abc123def456": {
      "content": "知识内容",
      "embedding": [0.1, 0.2, ...],
      "metadata": {
        "type": "behavior",
        "source": "system",
        "created_at": "2026-04-13T10:00:00",
        "usage_count": 0,
        "source_session": null
      }
    }
  }
}
```

### 2. 热搜知识 (TrendingTopicsService)

```json
{
  "knowledge_type": "trending",
  "updated_at": "2026-04-13T10:00:00",
  "trending_topics": {
    "data": {
      "baidu_hot": [...],
      "zhihu_hot": [...],
      "douyin_hot": [...],
      "fetch_time": "2026-04-13 10:00:00",
      "success": true
    },
    "timestamp": 1712985600.0
  }
}
```

### 3. 用户风格 (UserStyleLearningService)

```json
{
  "knowledge_type": "user_styles",
  "updated_at": "2026-04-13T10:00:00",
  "user_styles": {
    "user_123": {
      "language_style": "简洁幽默",
      "vocabulary_preferences": ["哈哈", "嗯嗯"],
      "sentence_patterns": ["疑问句", "感叹句"],
      "emotional_expressions": ["感叹", "疑问"],
      "common_topics": ["美妆", "穿搭"],
      "interaction_style": "活泼"
    }
  }
}
```

### 4. 用户知识图谱 (UserKnowledgeGraphService)

```json
{
  "knowledge_type": "user_knowledge_graphs",
  "updated_at": "2026-04-13T10:00:00",
  "user_knowledge_graphs": {
    "user_123": {
      "user_id": "user_123",
      "entities": [
        {
          "id": "entity_uuid",
          "name": "口红",
          "entity_type": "topic",
          "description": "用户感兴趣的化妆品",
          "source": "conversation",
          "properties": {}
        }
      ],
      "relationships": [
        {
          "id": "rel_uuid",
          "source_entity": "entity_uuid_1",
          "target_entity": "entity_uuid_2",
          "relationship_type": "interested_in",
          "description": "用户对某话题感兴趣",
          "source": "conversation"
        }
      ],
      "last_updated": "2026-04-13T10:00:00"
    }
  }
}
```

## 更新机制

| 知识类型 | 更新时机 | 更新方式 |
|----------|----------|----------|
| 行为/特征/交互/纠正知识 | 调用 `add()` 方法时 | 即时写入 |
| 热搜知识 | 预热、后台刷新、异步刷新时 | 定时更新 (TTL: 30分钟) |
| 用户风格 | 调用 `set_user_style()` 时 | 即时写入 |
| 用户知识图谱 | 调用 `set_user_kg()` 时 | 即时写入 |

## 相关代码位置

- **KnowledgeStore**: `core/managers/knowledge_store.py`
- **TrendingTopicsService**: `core/services/trending_topics_service.py`
- **UserStyleLearningService**: `core/services/feature_services/user_style_service.py`
- **UserKnowledgeGraphService**: `core/services/feature_services/user_knowledge_graph_service.py`
