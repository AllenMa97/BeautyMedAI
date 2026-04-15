# 评估指标与监控方案

## 一、核心评估指标

### 1.1 API成本统计

| 指标 | 计算方式 | 数据来源 |
|------|---------|---------|
| **输入Token** | 每次请求的 input_tokens 求和 | LLM API 返回 |
| **输出Token** | 每次请求的 output_tokens 求和 | LLM API 返回 |
| **总Token** | input + output | 自动计算 |
| **API调用次数** | 统计LLM请求次数 | 代码埋点 |
| **成本估算** | token数 × 单价 | 需配置模型单价 |

**模型单价参考（阿里云）**：
```
qwen-flash:     0.0003元/千输入   0.0006元/千输出
qwen-plus:      0.004元/千输入    0.012元/千输出
qwen-long:      0.002元/千输入    0.008元/千输出
```

### 1.2 性能指标

| 指标 | 计算方式 | 用途 |
|------|---------|------|
| **平均响应时间** | 总耗时/请求数 | 性能监控 |
| **P99响应时间** | 第99百分位耗时 | 慢请求分析 |
| **各步骤耗时** | 步骤耗时日志 | 性能瓶颈定位 |
| **并发请求数** | 实时统计 | 容量规划 |

### 1.3 质量指标

| 指标 | 计算方式 | 用途 |
|------|---------|------|
| **请求成功率** | 成功请求数/总请求数 | 稳定性监控 |
| **错误率** | 错误请求数/总请求数 | 故障预警 |
| **功能调用成功率** | 各功能成功数/调用数 | 功能健康度 |
| **内容拦截率** | 被拦截数/总请求数 | 安全监控 |

---

## 二、数据埋点方案

### 2.1 LLM调用统计

在 `llm_factory.py` 中埋点：

```python
@dataclass
class LLMCostRecord:
    """LLM调用成本记录"""
    timestamp: str
    provider: str          # aliyun/glm/lansee
    model: str             # qwen-flash/qwen-plus
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: int
    success: bool
    error_type: str = None
    session_id: str = None
    request_source: str = None  # 哪个功能触发的
```

### 2.2 请求级别统计

在 `function_planner_service.py` 中埋点：

```python
@dataclass
class RequestRecord:
    """请求级别统计"""
    timestamp: str
    session_id: str
    user_input_len: int
    output_len: int
    total_latency_ms: int
    steps_latency: Dict[str, int]  # 各步骤耗时
    functions_called: List[str]     # 调用的功能
    success: bool
    error_message: str = None
```

---

## 三、数据存储

### 3.1 轻量方案：JSON文件

```
data/
  metrics/
    2026-04-07/
      llm_cost.jsonl    # 每次LLM调用一行
      request.jsonl     # 每次请求一行
```

格式示例：
```json
{"timestamp":"2026-04-07 14:50:24","provider":"aliyun","model":"qwen-flash","input_tokens":120,"output_tokens":180,"total_tokens":300,"latency_ms":500,"success":true,"session_id":"abc123"}
```

### 3.2 中等方案：SQLite

```python
# 创建数据库
CREATE TABLE llm_costs (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    provider TEXT,
    model TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    latency_ms INTEGER,
    success BOOLEAN
);

CREATE TABLE requests (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    session_id TEXT,
    total_latency_ms INTEGER,
    success BOOLEAN
);
```

---

## 四、API接口设计

### 4.1 成本统计接口

```
GET /api/v1/metrics/cost?start_date=2026-04-01&end_date=2026-04-07

Response:
{
  "period": "2026-04-01 ~ 2026-04-07",
  "total_requests": 1000,
  "total_input_tokens": 500000,
  "total_output_tokens": 300000,
  "total_tokens": 800000,
  "estimated_cost": 0.45,  # 元
  "by_model": {
    "qwen-flash": {"input": 400000, "output": 200000, "cost": 0.24},
    "qwen-plus": {"input": 100000, "output": 100000, "cost": 0.21}
  },
  "by_day": [
    {"date": "2026-04-01", "tokens": 100000, "cost": 0.06},
    ...
  ]
}
```

### 4.2 性能统计接口

```
GET /api/v1/metrics/performance?start_date=2026-04-07

Response:
{
  "date": "2026-04-07",
  "total_requests": 500,
  "success_rate": 0.98,
  "avg_latency_ms": 2500,
  "p50_latency_ms": 2000,
  "p99_latency_ms": 8000,
  "by_step": {
    "步骤1_加载会话": {"avg_ms": 10, "count": 500},
    "步骤2_路由决策": {"avg_ms": 1500, "count": 500},
    "步骤3_解析计划": {"avg_ms": 5, "count": 500},
    "步骤4_执行功能": {"avg_ms": 800, "count": 500},
    "步骤5_处理结果": {"avg_ms": 20, "count": 500}
  }
}
```

### 4.3 实时状态接口

```
GET /api/v1/metrics/realtime

Response:
{
  "active_sessions": 15,
  "requests_last_hour": 120,
  "errors_last_hour": 3,
  "avg_latency_last_hour": 2100,
  "token_usage_today": 50000,
  "cost_today_estimate": 0.03
}
```

---

## 五、可视化方案

### 5.1 简单方案：独立HTML页面

```
admin/
  index.html    # 仪表盘页面
  api.js        # 调用后端API
```

展示内容：
- 今日/本周/本月Token用量
- 成本估算曲线
- 各功能调用成功率
- 响应时间分布

### 5.2 后续扩展

如果需要更专业的监控，可以接入：
- **Grafana** + **Prometheus**
- **DataV** 大屏
- **自建BI系统**

---

## 六、实施步骤

### 第一阶段：数据埋点（1天）
- [ ] 修改 llm_factory.py，记录每次LLM调用
- [ ] 修改 function_planner_service.py，记录请求级别数据
- [ ] 确定存储方案（JSON文件起步）

### 第二阶段：API接口（1天）
- [ ] 新增 metrics 路由
- [ ] 实现 /cost 接口
- [ ] 实现 /performance 接口
- [ ] 实现 /realtime 接口

### 第三阶段：可视化（1天）
- [ ] 简单HTML页面
- [ ] 展示关键指标
- [ ] 日期筛选功能

---

## 七、配置文件

### 模型单价配置（config/metrics.yaml）

```yaml
pricing:
  aliyun:
    qwen-flash:
      input_per_1k: 0.0003
      output_per_1k: 0.0006
    qwen-plus:
      input_per_1k: 0.004
      output_per_1k: 0.012
    qwen-long:
      input_per_1k: 0.002
      output_per_1k: 0.008
  glm:
    glm-4-flash:
      input_per_1k: 0.0001
      output_per_1k: 0.0001
```

---

## 八、注意事项

1. **数据量**：如果请求量大，考虑定期归档或清理历史数据
2. **隐私**：session_id等敏感信息注意脱敏
3. **准确性**：成本仅为估算，实际以阿里云账单为准
4. **性能**：统计查询避免全表扫描，建议按日期分目录/分表
