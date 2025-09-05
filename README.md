# KX智能内容创作系统

基于AutoGen的智能内容创作系统，支持网页爬取、内容分析、文章创作和微信公众号发布。

## 🚀 功能特性

- **🕷️ 智能爬取**: 自动爬取网页内容，提取标题、正文、图片、链接等信息
- **🔍 内容分析**: 使用AI分析内容结构，识别关键信息和主题
- **✍️ 智能写作**: 基于分析结果创作高质量文章，支持多种风格
- **📱 一键发布**: 直接发布到微信公众号，支持草稿和正式发布
- **🤖 多Agent协作**: 基于AutoGen的多智能体协作架构
- **⚡ 异步处理**: 支持异步任务处理，提升系统性能

## 📋 系统架构

### Multi-Agent架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CrawlerAgent  │───▶│  AnalyzerAgent  │───▶│   WriterAgent   │───▶│ PublisherAgent  │
│   网页爬取      │    │   内容分析      │    │   文章创作      │    │   内容发布      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 技术栈

- **后端框架**: FastAPI + Uvicorn
- **AI框架**: AutoGen + 千问大模型
- **爬虫**: aiohttp + BeautifulSoup
- **微信API**: wechatpy
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx

## 🛠️ 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo-url>
cd kx-creation

# 复制环境变量文件
cp client/.env.example client/.env
```

### 2. 配置环境变量

编辑 `client/.env` 文件：

```bash
# 千问API配置（必需）
QWEN_API_KEY=your_qwen_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-turbo

# 微信公众号配置（可选）
WECHAT_APP_ID=your_wechat_app_id_here
WECHAT_APP_SECRET=your_wechat_app_secret_here
```

### 3. 启动服务

```bash
# 使用Docker Compose启动
./deploy.sh

# 或者手动启动
docker compose up --build -d
```

### 4. 访问服务

- **API文档**: http://localhost/docs
- **健康检查**: http://localhost/health

## 📚 API文档

### 核心接口

#### 1. URL到文章 (推荐)

```http
POST /api/url-to-article
Content-Type: application/json

{
  "url": "https://example.com/article",
  "article_style": "professional",
  "target_audience": "general",
  "word_count": 1000,
  "extract_images": true,
  "extract_links": true
}
```

#### 2. URL到微信发布 (一键发布)

```http
POST /api/url-to-wechat
Content-Type: application/json

{
  "url": "https://example.com/article",
  "article_style": "professional",
  "target_audience": "general",
  "author": "KX智能创作",
  "draft_only": false
}
```

#### 3. 任务状态查询

```http
GET /api/task/{task_id}/status
```

#### 4. 任务结果获取

```http
GET /api/task/{task_id}/result
```

### 分步接口

如需更精细的控制，可使用以下分步接口：

- `POST /api/crawl` - 网页爬取
- `POST /api/analyze` - 内容分析
- `POST /api/write` - 文章创作
- `POST /api/publish` - 微信发布

## 🔧 配置说明

### 文章风格 (article_style)

- `professional` - 专业风格（默认）
- `casual` - 轻松风格
- `news` - 新闻风格

### 目标受众 (target_audience)

- `general` - 普通读者（默认）
- `technical` - 技术人员
- `business` - 商务人士

## 📁 项目结构

```
kx-creation/
├── client/                 # 主应用
│   ├── agents/            # 多Agent模块
│   │   ├── base_agent.py
│   │   ├── crawler_agent.py
│   │   ├── analyzer_agent.py
│   │   ├── writer_agent.py
│   │   ├── publisher_agent.py
│   │   └── orchestrator.py
│   ├── services/          # 服务层
│   │   ├── crawler.py
│   │   └── wechat.py
│   ├── models/            # 数据模型
│   │   └── schemas.py
│   ├── config/            # 配置管理
│   │   └── config.py
│   ├── main.py           # FastAPI应用
│   ├── requirements.txt  # Python依赖
│   └── Dockerfile       # 应用镜像
├── nginx/                # Nginx配置
├── docker-compose.yml   # 服务编排
└── deploy.sh           # 部署脚本
```

## 🔍 使用示例

### Python客户端示例

```python
import requests
import time

# 1. 提交URL处理任务
response = requests.post("http://localhost/api/url-to-article", json={
    "url": "https://example.com/article",
    "article_style": "professional",
    "target_audience": "general"
})

task_id = response.json()["task_id"]

# 2. 轮询任务状态
while True:
    status_response = requests.get(f"http://localhost/api/task/{task_id}/status")
    status = status_response.json()
    
    if status["status"] == "completed":
        # 3. 获取结果
        result_response = requests.get(f"http://localhost/api/task/{task_id}/result")
        article = result_response.json()["data"]["article_result"]["article"]
        print(f"文章标题: {article['title']}")
        print(f"文章内容: {article['content']}")
        break
    elif status["status"] == "failed":
        print(f"任务失败: {status['message']}")
        break
    
    time.sleep(2)
```

### curl示例

```bash
# 提交任务
curl -X POST "http://localhost/api/url-to-article" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "article_style": "professional"
  }'

# 查询状态
curl "http://localhost/api/task/{task_id}/status"

# 获取结果
curl "http://localhost/api/task/{task_id}/result"
```

## 🚨 注意事项

1. **API密钥安全**: 请妥善保管千问API密钥和微信公众号密钥
2. **网站爬取**: 请遵守目标网站的robots.txt规则
3. **内容版权**: 请确保有权使用和转载爬取的内容
4. **微信限制**: 微信公众号发布有频率限制，请合理使用
5. **资源消耗**: AI分析和创作会消耗较多计算资源

## 📈 性能优化

- 使用异步处理提升并发能力
- 合理设置超时时间避免长时间等待
- 监控系统资源使用情况
- 定期清理任务状态缓存

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目基于MIT许可证开源。