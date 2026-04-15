# Lansee Chatbot 系统设计文档

## 系统概述

Lansee Chatbot（又称 YISIA）是一个基于 LLM 的智能对话系统，采用 FastAPI 构建，运行于 6732 端口。

## 核心架构

```
用户请求 → FastAPI (6732端口) → 功能规划器 → 功能执行器 → 各功能服务 → 流式返回
                                    ↓
                              会话管理器
                                    ↓
                            内容检测服务
```

## 核心组件

| 组件 | 文件位置 | 说明 |
|------|---------|------|
| FastAPI主应用 | `main.py` | 入口，端口6732 |
| 功能规划器 | `function_planner_service.py` | ReAct模式规划执行 |
| 功能执行器 | `function_executer_service.py` | 调度执行各功能服务 |
| 会话管理器 | `session_factory.py` | 状态管理、记忆存储 |
| LLM工厂 | `llm_factory.py` | 多Provider调用、Key轮换 |

## 请求处理流程

```
【步骤1】加载会话信息
    ↓
【步骤2】路由决策（是否规划 + 是否联网）
    ↓
【步骤3】解析调度计划
    ↓
【步骤4】执行功能（并行/串行）
    ↓
【步骤5】处理最终结果（流式返回）
```

## 功能列表

系统支持以下功能服务：

- `dialog_summary` - 对话摘要
- `entity_recognize` - 实体识别
- `free_chat` - 闲聊对话
- `intent_clarify` - 意图澄清
- `intent_recognize` - 意图识别
- `knowledge_index` - 知识索引
- `rag` - RAG检索增强
- `text_summary` - 文本摘要
- `time_location` - 时间地理位置
- `trending_topics` - 热搜话题
- `recommendation` - 推荐
- `image_understanding` - 图片理解
- `memory_recall` - 记忆召回
- `emotion_recognition` - 情感识别
- `content_moderation` - 内容检测

## 详细文档

- [记忆系统与上下文管理](./memory_and_context.md)
- [知识系统与进化体系](./knowledge_and_evolution.md)
- [回退设计](./fallback_design.md)
- [性能优化](./performance_optimization.md)

## 启动方式

```bash
python main.py
```

访问 API 文档：http://localhost:6732/api/docs
