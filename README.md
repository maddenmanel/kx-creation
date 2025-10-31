# KX Intelligent Content Creation System

**AI-powered content creation system using AgentScope + Qwen (Qianwen)**

Transform any web article into high-quality content with multi-agent AI collaboration.

---

## 🚀 Features

- **🕷️ Smart Web Scraping** - Extract content, images, links from any URL
- **🔍 AI Content Analysis** - Analyze structure, themes, key points using Qwen
- **✍️ Intelligent Writing** - Generate articles in multiple styles (professional/casual/news)
- **📱 WeChat Publishing** - One-click publish to WeChat Official Accounts
- **🤖 Multi-Agent System** - AgentScope framework with 4 specialized agents
- **⚡ Async Processing** - FastAPI with background task management

---

## 📋 Architecture

```
User Request → FastAPI → Orchestrator → [Agents] → Response
                              ↓
                    CrawlerAgent  (Web Scraping)
                         ↓
                    AnalyzerAgent (AI Analysis via Qwen)
                         ↓
                    WriterAgent   (AI Writing via Qwen)
                         ↓
                    PublisherAgent (WeChat Publishing)
```

**Tech Stack**: FastAPI + AgentScope 1.0.6 + Qwen + BeautifulSoup + wechatpy

---

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Qwen API Key ([Get here](https://dashscope.console.aliyun.com/))

### Quick Setup

```bash
# 1. Clone repository
git clone <your-repo>
cd kx-creation

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Install dependencies
cd client
pip install -r requirements.txt

# 4. Create .env file
# Create client/.env with:
QWEN_API_KEY=your_api_key_here
QWEN_MODEL=qwen-turbo
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

---

## 🚀 Usage

### Start Server

```bash
# From client directory
cd client
python main.py

# Server runs at http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Test Health

```bash
curl http://localhost:8000/health
```

### Run Demo

```bash
cd client
python tests/demo.py
```

---

## 📚 API Endpoints

### Core Workflows

**1. URL to Article** (Complete pipeline)1
```bash
POST /api/url-to-article
{
  "url": "https://example.com/article",
  "article_style": "professional",  # or "casual", "news"
  "target_audience": "general",     # or "technical", "business"
  "word_count": 1000
}
```
Returns: `task_id`

**2. URL to WeChat** (One-click publishing)
```bash
POST /api/url-to-wechat
{
  "url": "https://example.com/article",
  "article_style": "professional",
  "author": "Your Name",
  "draft_only": false
}
```

**3. Check Task Status**
```bash
GET /api/task/{task_id}/status
GET /api/task/{task_id}/result
```

### Step-by-Step

- `POST /api/crawl` - Crawl URL
- `POST /api/analyze` - Analyze content
- `POST /api/write` - Write article
- `POST /api/publish` - Publish to WeChat

---

## 💡 Example Usage

### Python Client

```python
import requests
import time

# Submit task
response = requests.post(
    "http://localhost:8000/api/url-to-article",
    json={
        "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "article_style": "professional",
        "word_count": 800
    }
)
task_id = response.json()["task_id"]

# Poll for completion
while True:
    status = requests.get(f"http://localhost:8000/api/task/{task_id}/status")
    if status.json()["status"] == "completed":
        result = requests.get(f"http://localhost:8000/api/task/{task_id}/result")
        article = result.json()["data"]["article_result"]
        print(f"Title: {article['title']}")
        print(f"Content: {article['content'][:500]}...")
        break
    time.sleep(2)
```

---

## 📁 Project Structure

```
kx-creation/
├── client/
│   ├── agents/              # Multi-agent system
│   │   ├── base_agent.py    # Base agent class
│   │   ├── crawler_agent.py # Web scraping
│   │   ├── analyzer_agent.py# Content analysis
│   │   ├── writer_agent.py  # Article generation
│   │   ├── publisher_agent.py# Publishing
│   │   └── orchestrator.py  # Workflow coordinator
│   ├── services/            # Service layer
│   │   ├── crawler.py       # Web crawling
│   │   └── wechat.py        # WeChat API
│   ├── models/              # Data models
│   │   └── schemas.py       # Pydantic models
│   ├── config/              # Configuration
│   │   └── config.py        # Settings
│   ├── tests/               # Tests
│   │   └── demo.py          # Demo script
│   ├── main.py              # FastAPI app
│   ├── requirements.txt     # Dependencies
│   └── .env                 # Config (create this)
├── docker-compose.yml       # Docker setup
└── README.md                # This file
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `QWEN_API_KEY` | ✅ Yes | - | Your Qwen API key |
| `QWEN_MODEL` | No | qwen-turbo | Model: qwen-turbo/plus/max |
| `QWEN_BASE_URL` | No | dashscope URL | API endpoint |
| `WECHAT_APP_ID` | No | - | WeChat App ID |
| `WECHAT_APP_SECRET` | No | - | WeChat App Secret |
| `HOST` | No | 0.0.0.0 | Server host |
| `PORT` | No | 8000 | Server port |

### Article Styles
- **professional** - Formal, authoritative, data-driven
- **casual** - Friendly, conversational, accessible
- **news** - Objective, factual, inverted pyramid

### Target Audiences
- **general** - General public
- **technical** - Technical professionals
- **business** - Business professionals

---

## 🔧 Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### Port already in use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Server won't start
1. Check virtual environment is activated
2. Verify `.env` file exists in `client/` directory
3. Confirm Qwen API key is valid
4. Check Python version (3.9+)

---

## 🚀 Docker Deployment (Optional)

```bash
# Build and run
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 📊 Dependencies

**Core**:
- fastapi==0.116.1
- uvicorn==0.38.0
- agentscope==1.0.6
- openai>=1.0.0

**Scraping**:
- requests==2.31.0
- beautifulsoup4==4.12.3
- lxml==5.3.0

**WeChat**:
- wechatpy==1.8.18

**Utilities**:
- pydantic-settings==2.5.2
- loguru==0.7.2
- aiohttp==3.10.5

See `client/requirements.txt` for complete list.

---

## 🎯 Key Features Explained

### Multi-Agent Architecture (AgentScope)
- **CrawlerAgent**: Intelligent web scraping with content extraction
- **AnalyzerAgent**: AI-powered content analysis using Qwen LLM
- **WriterAgent**: Article generation with style adaptation using Qwen LLM
- **PublisherAgent**: Multi-platform publishing (WeChat)

### Asynchronous Processing
- Background task execution
- Non-blocking API endpoints
- Real-time status tracking
- Result caching

### Qwen Integration
- OpenAI-compatible API
- Multiple model options (turbo/plus/max)
- Configurable temperature and tokens
- Error handling and retries

---

## 📝 API Response Example

```json
{
  "success": true,
  "crawl_result": {
    "title": "Artificial Intelligence",
    "content": "AI is...",
    "images": ["url1", "url2"],
    "links": ["link1", "link2"]
  },
  "analysis_result": {
    "summary": "This article discusses...",
    "key_points": ["Point 1", "Point 2"],
    "themes": ["AI", "Technology"],
    "sentiment": "neutral"
  },
  "article_result": {
    "title": "Understanding Artificial Intelligence",
    "content": "Full article content...",
    "word_count": 1000,
    "style": "professional",
    "tags": ["AI", "Technology", "Innovation"]
  }
}
```

---

## ⚠️ Important Notes

1. **API Key Security**: Keep your Qwen API key secure in `.env` file
2. **Respect robots.txt**: Follow website scraping policies
3. **Content Rights**: Ensure you have rights to use scraped content
4. **WeChat Limits**: Official Account publishing has rate limits
5. **API Costs**: Qwen API usage incurs costs based on tokens

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 📞 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: This README
- **API Docs**: http://localhost:8000/docs (when running)

---

## 🎉 Quick Test

```bash
# 1. Start server
cd client && python main.py

# 2. In another terminal, test:
curl -X POST http://localhost:8000/api/url-to-article \
  -H "Content-Type: application/json" \
  -d '{"url": "https://en.wikipedia.org/wiki/Python_(programming_language)", "article_style": "casual", "word_count": 500}'

# 3. Check result (use task_id from response):
curl http://localhost:8000/api/task/{task_id}/result
```

---

**Built with ❤️ using AgentScope + Qwen**

**Status**: ✅ Production Ready | Version: 1.0.0
