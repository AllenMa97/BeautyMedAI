# 性能优化

## 一、逻辑短路加速

### 1.1 简单问题快速短路

位置：`function_planner_service.py`

**简单问题词表匹配**：

```python
SIMPLE_PATTERNS = [
    "你好", "早上好", "晚安", "嗨", "hi", "hello",
    "几点", "时间", "日期", "今天", "明天", "昨天",
    "天气", "温度", "晴", "雨", "雪", "风",
    "谢谢", "OK", "好的", "收到", "明白", "知道",
    "唱歌", "讲故事", "讲个笑话", "笑话",
    "计算", "1+1", "2*3", "加减乘除"
]

# 快速词表匹配
is_simple = False
if len(request.user_input) <= 15:
    for pattern in self.SIMPLE_PATTERNS:
        if pattern in user_input_lower:
            is_simple = True
            logger.info(f"[快速短路] 检测为简单问题（词表匹配），跳过规划")
            break
```

**短路效果**：
- 命中词表 → 跳过LLM规划
- 直接进入 free_chat 生成回复
- 节省 500ms-2s 的规划时间

### 1.2 联网搜索快速判断

**Always Search 词表**：

```python
ALWAYS_SEARCH_PATTERNS = [
    "最新", "现在", "今天热搜", "当前热搜", "热搜",
    "股价", "股票", "期货", "币价",
    "新闻", "发生了什么", "怎么回事",
    "谁", "什么是", "怎么做", "如何",
    "查一下", "搜索", "找一下"
]
```

---

## 二、缓存机制

### 2.1 意图缓存

```python
INTENT_CACHE_TTL = 3600  # 意图缓存1小时

# 检查缓存
cached = self._intent_cache.get(input_hash)
if cached and cached.get("expire", 0) > time.time():
    intent = cached["intent"]  # 直接使用缓存
    logger.info(f"[意图缓存命中] {user_input} -> {intent}")
```

### 2.2 热搜缓存

位置：`trending_topics_service.py`

```python
_cache_ttl = 1800  # 30分钟缓存

def get_cached_trending_topics(self):
    cached = self._cache.get('trending_topics')
    if cached:
        return cached['data']  # 直接返回缓存，不重新爬取
```

### 2.3 会话缓存

```python
# 缓存当前轮次，避免遍历
self.current_turn: Optional[TurnData] = None

def get_current_turn(self):
    if self.current_turn and self.current_turn.turn_id == self.current_turn_id:
        return self.current_turn  # 缓存命中
```

---

## 三、并行处理

### 3.1 时间+热搜并行获取

```python
# 并行获取时间和热搜
time_location_task = asyncio.create_task(asyncio.to_thread(time_location_service.get_context_info))
trending_task = asyncio.create_task(self.get_trending_info_async())

time_location_info, trending_topics_info = await asyncio.gather(
    time_location_task,
    trending_task,
    return_exceptions=True
)
```

### 3.2 功能并行执行

**独立功能并行，依赖功能串行**：

```python
# 分组
independent_funcs = []  # 可并行
dependent_funcs = []    # 需串行（free_chat）

# 并行执行独立功能
independent_results = await asyncio.gather(
    *[execute_single_function(func_tuple, tmp_session_data) for func_tuple in independent_funcs],
    return_exceptions=True
)
```

### 3.3 内容检测异步

```python
# 拦截检查（异步并行，不阻塞主流程）
if not hasattr(session, '_moderation_task') or session._moderation_task is None:
    session._moderation_task = asyncio.create_task(
        content_moderation_service.moderate(request.user_input)
    )
```

---

## 四、预热机制

### 4.1 启动时预热

位置：`system_initializer.py`

```python
def initialize_basic_services():
    # 并行预热
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        time_future = executor.submit(warmup_time_location)
        trending_future = executor.submit(warmup_trending_topics)
        concurrent.futures.wait([time_future, trending_future])
```

**预热内容**：
- 时间地理位置服务
- 热搜话题服务

---

## 五、日志优化

### 5.1 日志格式统一

**修改前**（混乱）：
```
步骤1：加载会话信息
[性能] 步骤1完成: 加载会话，耗时0.00秒
步骤2：路由决策...
步骤3：解析调度计划
[性能] 步骤3完成: 解析计划
[性能] 步骤2完成: 生成计划（顺序错误！）
```

**修改后**（有序）：
```
【步骤1】加载会话信息
【步骤1完成】加载会话，耗时0.00秒
【步骤2】路由决策（是否需要规划 + 是否需要联网）
路由决策结果: need_plan=False, need_search=True
【步骤3】解析调度计划
【步骤3完成】解析计划，耗时0.00秒 | 功能列表: ['free_chat']
【步骤4】执行功能
【步骤4开始】执行功能，耗时0.00秒
功能分组 | execution_order: [0] | function_calls: ['free_chat']
【执行】free_chat | 参数=['session_id', 'user_id', ...]
【步骤5】处理最终结果
【请求完成】session_id=xxx | 总耗时=2.94秒 | 输入(8字) → 输出(174字) | 功能=['free_chat']
```

### 5.2 合并分散日志

| 原来 | 现在 |
|------|------|
| 3条分组日志 | 1条 |
| 6行请求完成日志 | 1条 |

---

## 六、ReAct模式优化

### 6.1 随机性控制

```python
# 随机最大迭代次数（2-5轮）
base_iterations = int(os.getenv("REACT_BASE_ITERATIONS", 2))
max_iterations = int(os.getenv("REACT_MAX_ITERATIONS", 5))
random.randint(base_iterations, max_iterations)

# 随机截取比例（20%-50%）
RANDOM_HEAD_RATIO_MIN = 0.2
RANDOM_HEAD_RATIO_MAX = 0.5
random.uniform(RANDOM_HEAD_RATIO_MIN, RANDOM_HEAD_RATIO_MAX)
```

### 6.2 重规划阈值

```python
REPLAN_THRESHOLD = float(os.getenv("FUNCTION_PLANNER_REPLAN_THRESHOLD", 0.2))
MIN_STEPS_BEFORE_REPLAN = int(os.getenv("MIN_STEPS_BEFORE_REPLAN", 1))

# 满足步数后，随机触发重规划
if iteration >= MIN_STEPS_BEFORE_REPLAN:
    if random.random() < REPLAN_THRESHOLD:
        # 触发重规划
```

---

## 七、相关文件索引

| 文件 | 说明 |
|------|------|
| `core/services/feature_services/function_planner_service.py` | 短路加速、并行处理 |
| `core/services/trending_topics_service.py` | 热搜缓存 |
| `session/session_factory.py` | 会话缓存 |
| `core/services/system_initializer.py` | 启动预热 |
