# ArXiv 论文搜索引擎 (RAG + Qwen)

一个基于本地部署的 Qwen 大模型和 RAG 技术的论文搜索引擎，支持 ArXiv 论文搜索和智能问答。

## 项目特性

- 🔍 **论文搜索**: 基于 ArXiv API 的实时论文搜索
- 🤖 **智能问答**: 基于 RAG 技术的论文内容问答
- 🏠 **本地部署**: 使用 Ollama 本地部署 Qwen 模型
- 📚 **引用溯源**: 问答结果支持引用来源追溯
- 🌐 **Web 界面**: 现代化的 React 前端界面
- 🚀 **一键部署**: 支持 Netlify 部署

## 技术栈

### 前端
- React 18 + Vite
- 现代化 UI 设计
- 响应式布局

### 后端
- FastAPI
- LangChain 0.3
- 本地 Ollama (Qwen 模型)
- ArXiv API
- FAISS 向量数据库
- Sentence Transformers

## 快速开始

### 1. 环境要求

- Python 3.8+
- Node.js 16+
- Ollama (已安装 Qwen 模型)

### 2. 安装 Ollama 和 Qwen 模型

```bash
# 安装 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 拉取 Qwen 模型
ollama pull qwen2.5:7b
```

### 3. 启动后端服务

```bash
cd backend

# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

后端服务将在 http://127.0.0.1:8001 启动

### 4. 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

前端服务将在 http://127.0.0.1:5173 启动

## API 接口

### 搜索论文
- **端点**: `POST /search`
- **参数**: 
  - `query`: 搜索关键词
  - `max_results`: 最大结果数 (默认20)
  - `sort_by`: 排序方式 (relevance/date/title)

### 智能问答
- **端点**: `POST /ask`
- **参数**:
  - `query`: 原始搜索关键词
  - `question`: 具体问题
  - `top_k`: 检索的文档数量

## 部署到 Netlify

### 1. 准备部署配置

确保 `frontend/netlify.toml` 配置正确：

```toml
[build]
  command = "npm run build"
  publish = "dist"

[template.environment]
  VITE_LOCAL_API_BASE = "https://your-backend-api.herokuapp.com"
```

### 2. 部署后端到支持平台

后端需要部署到支持 Python 的平台，如：
- Heroku
- Railway
- Render
- Vercel (需要调整配置)

### 3. 连接前后端

将部署的后端 API 地址更新到前端环境变量中。

## 项目结构

```
homework4/
├── frontend/                 # React 前端
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── backend/                  # FastAPI 后端
│   ├── main.py              # 主应用
│   ├── requirements.txt      # Python 依赖
│   ├── run.py               # 启动脚本
│   └── start.sh/start.bat   # 启动脚本
└── README.md
```

## 使用说明

1. **搜索论文**: 在搜索框输入关键词，系统会从 ArXiv 检索相关论文
2. **智能问答**: 基于搜索结果，可以向 AI 提问关于这些论文的问题
3. **引用溯源**: AI 回答时会引用具体的论文内容，支持溯源查看

## 开发说明

### 后端开发
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### 前端开发
```bash
cd frontend
npm install
npm run dev
```

## 故障排除

### 常见问题

1. **Ollama 连接失败**
   - 检查 Ollama 服务是否运行: `ollama serve`
   - 确认模型已下载: `ollama list`

2. **依赖安装失败**
   - 使用 Python 3.8+ 版本
   - 尝试使用清华镜像源

3. **CORS 错误**
   - 检查后端 CORS 配置
   - 确认前端 API 地址正确

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！