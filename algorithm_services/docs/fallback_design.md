# 回退设计

## 一、LLM API 回退机制

### 1.1 多Provider支持

位置：`large_model/llm_factory.py`

支持的LLM服务商：
- `aliyun` - 阿里云
- `glm` - 智谱AI
- `lansee` - 本地部署

### 1.2 API Key轮换

**触发条件**：400/403错误

```python
# 400/403错误时尝试切换API Key
if ("400" in error_str or "403" in error_str) and not key_switched:
    if self._switch_to_backup_key():
        key_switched = True
        logger.info(f"[LLM] 提供商[{provider}] Key[{key_preview}] 模型[{model}] 切换API Key后重试")
        continue
```

### 1.3 模型回退

**触发条件**：403配额不足

```python
# 403配额错误时尝试模型回退
if "403" in error_str or "free" in error_str.lower() or "quota" in error_str.lower():
    if not model_switched and fallback_models:
        fallback_model = fallback_models[current_fallback_index]
        logger.warning(f"[LLM] 提供商[{provider}] Key[{key_preview}] 模型[{model}] 配额不足，切换到备用模型: {fallback_model}")
        request.model = fallback_model
        continue
```

### 1.4 Provider回退

**触发条件**：当前Provider所有Key都失败

```python
# 主Provider失败后尝试备用Provider
try:
    result = await self.call_llm(request)
except Exception as primary_error:
    for fallback_provider in ["glm", "lansee"]:
        try:
            client = llm_client_factory.get_client(fallback_provider)
            result = await client.call_llm(request)
        except Exception as fallback_error:
            continue
```

---

## 二、热搜数据回退

### 2.1 多级降级机制

位置：`core/services/trending_topics_service.py`

**优先级**：
1. 免费API (`uapis.cn`) - 最快最稳定
2. 浏览器自动化 (Playwright) - 处理动态页面
3. requests网页抓取 - 降级方案

### 2.2 微博热搜特殊处理

由于微博需要登录，跳过微博热搜抓取：
- 仅保留百度、小红书等无需登录的平台
- API失败时返回空列表而非爬取

```python
# 微博直接返回空，不尝试抓取
trending_data['weibo_hot'] = []
logger.info("微博热搜跳过（需要登录），仅获取百度和小红书")
```

---

## 三、内容检测回退

### 3.1 三层检测架构

位置：`core/processors/content_moderation_service.py`

| 层级 | 检测方式 | 失败处理 |
|------|---------|---------|
| L1 | 词表检测 | 同步，几乎不失败 |
| L2 | 公共API | 异步，失败不影响其他层 |
| L3 | LLM语义分析 | 异步，失败时降级到L1 |

### 3.2 检测模式

- **Fast模式**：仅关键词检测
- **Accurate模式**：仅LLM检测
- **Parallel模式**：关键词+LLM并行

---

## 四、自进化回退

### 4.1 定时任务失败处理

位置：`core/managers/scheduled_update_manager.py`

- 定时任务失败不影响主流程
- 每个任务独立try-catch
- 失败后等待一段时间再重试

---

## 五、日志优化

### 5.1 403错误日志改进

修改后日志包含完整错误定位信息：

```
修改前：
[LLM] 请求失败状态码: 403
[LLM] 服务商[aliyun] 切换到备用API Key 2/2
[LLM] 切换API Key后重试

修改后：
[LLM] 提供商[aliyun] Key[sk-abc1...xyzh] 模型[qwen3-flash] 调用失败（重试1/30）...
[LLM] 提供商[aliyun] Key[sk-abc1...xyzh] 模型[qwen3-flash] 配额不足，切换到备用模型: qwen-plus
```

---

## 六、相关文件索引

| 文件 | 说明 |
|------|------|
| `large_model/llm_factory.py` | LLM API回退逻辑 |
| `core/services/trending_topics_service.py` | 热搜数据回退 |
| `core/processors/content_moderation_service.py` | 内容检测回退 |
| `core/managers/scheduled_update_manager.py` | 定时任务回退 |
