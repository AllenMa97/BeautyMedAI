# 知识库服务

一个综合性的知识库服务，支持网页爬取、文档处理和RAG（检索增强生成）功能。

## 功能特性

### 1. 网页爬虫
- 使用LLM生成智能搜索查询
- 支持用户自定义主题和爬取要求
- 提供实时爬取进度反馈
- 支持多种存储方式（数据库、文件或两者）
- 实现反爬虫措施（随机User-Agent、请求间隔）
- 支持并发查询，提高爬取效率
- 可配置每查询的最大结果数
- 优化爬取速度，支持并发爬取
- 扩展用户输入以获取更丰富的结果
- 优先从中国大陆可访问的网站爬取内容

### 2. 文档处理
- 支持多种文件格式：TXT、Word、Excel、PDF、PNG、JPG、JPEG
- 内置OCR功能，可识别图片中的文字
- PDF处理和表格识别
- 使用LLM提取关键信息

### 3. 知识管理
- SQLite数据库存储（支持未来迁移到PostgreSQL）
- 语义搜索功能
- 向量化存储和检索
- 支持标签分类
- 提供知识展示页面，方便用户浏览和查看知识条目
- 支持Markdown和纯文本格式的知识存储

### 4. RAG功能
- 基于检索增强生成的知识查询
- 语义相似度匹配
- 上下文感知回答

## 快速开始

### 环境准备

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置LLM API密钥：
```bash
cp algorithm_services/config/LLM_API.env knowledge_base_service/config/
```

3. 运行服务：
```bash
cd knowledge_base_service
python main.py
```

服务将在 `http://localhost:8002` 启动。

### 使用方法

#### 通过Web界面
访问 `http://localhost:8002`，使用图形化界面进行操作：

1. **网页爬虫**：
   - 输入爬取主题和具体要求
   - 选择存储方式（数据库、文件或两者）
   - 点击"开始爬取"

2. **文档上传**：
   - 选择要处理的文档
   - 点击"上传并处理"

#### 通过API
API文档可在 `http://localhost:8002/api/docs` 查看。

## API接口

### 网页爬虫
- `POST /api/v1/crawl` - 启动网页爬虫
- 请求体：
  ```json
  {
    "topic": "爬取主题",
    "requirements": "爬取要求",
    "storage_method": "database|file|both",
    "max_results_per_query": 10
  }
  ```

### 文档上传
- `POST /api/v1/upload` - 上传并处理文档
- 表单数据：`files[]` - 文档文件

### 知识检索
- `POST /api/v1/knowledge/search` - 搜索知识库
- `GET /api/v1/knowledge/list` - 列出所有知识条目

### RAG查询
- `POST /api/v1/rag/query` - RAG知识查询

## 存储方式

### 数据库存储
- 使用SQLite数据库（`knowledge_base.db`）
- 自动创建表结构
- 支持向量化搜索

### 文件存储
- 以JSON格式保存到 `knowledge_files/` 目录
- 按主题和时间戳命名
- 便于备份和迁移

## 技术栈

- **后端**: FastAPI
- **数据库**: SQLite (默认)，支持PostgreSQL
- **LLM集成**: OpenAI兼容接口（支持阿里云通义千问等）
- **文档处理**: PyPDF2, python-docx, pandas, Pillow, pytesseract
- **向量化**: sentence-transformers
- **前端**: HTML/CSS/JavaScript

## 配置

### 环境变量
在 `config/LLM_API.env` 文件中配置：

```env
ALIYUN_API_KEY=your_api_key
ALIYUN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
ALIYUN_DEFAULT_MODEL=qwen-flash
```

## 错误处理

- 网络请求超时
- LLM调用失败
- 文件处理错误
- 数据库连接问题

## 日志记录

系统会记录所有操作日志，便于调试和监控。

## 扩展性

- 易于添加新的文档格式支持
- 可扩展的LLM适配器
- 模块化的处理器设计
- 支持分布式部署

## 注意事项

1. 确保有足够的磁盘空间存储爬取的数据
2. 遵守网站的robots.txt规则
3. 合理设置爬取频率，避免对目标网站造成压力
4. 定期备份知识库数据