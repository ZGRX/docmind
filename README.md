# DocMind · AI Study Assistant

一个适合学习和简历展示的 Vue 3 + FastAPI 文档知识库。上传 PDF、TXT 或 Markdown，系统提取文本并建立向量索引；提问时先检索相关片段，再调用兼容 OpenAI API 的模型，流式显示回答与引用来源。

## 功能

- 文档上传、列表、删除；删除时同步清理 Chroma 向量和原文件
- PDF 文本提取、清洗、重叠分块、Embedding、Chroma 检索
- 逐段流式回答、Markdown 和代码块显示、文件名与 chunk 引用
- SQLite 会话历史、首页文档 / chunk / 会话统计
- 深色响应式界面；无登录，适合本地学习演示

## 技术栈与目录

```text
.
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI 路由
│   │   ├── core/         # 配置与应用错误
│   │   ├── db/           # SQLAlchemy 连接
│   │   ├── models/       # SQLite 表
│   │   ├── schemas/      # 请求与响应校验
│   │   ├── services/     # 文档、Embedding、检索、LLM
│   │   └── main.py
│   ├── .env.example
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/{api,assets,components,router,stores,views}/
│   ├── .env.example
│   └── Dockerfile
├── docs/
│   ├── learning-guide.md
│   ├── interview-questions.md
│   └── improvement-roadmap.md
└── docker-compose.yml
```

## 本地启动

建议 Python 3.11、Node.js 20.19+。在仓库根目录运行：

```bash
cd backend
cp .env.example .env
# 编辑 .env，填写真实的 OPENAI_API_KEY，并确认模型名和 API 地址
python -m venv venv
source venv/bin/activate  # Windows PowerShell: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

另开终端：

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173。API 文档在 http://localhost:8000/docs。Vite 默认将 `/api` 代理到 `localhost:8000`；远程前端可用 `VITE_API_BASE_URL` 指定完整 API 前缀（例如 `https://example.com/api`）。

首次启动时自动创建 `backend/data/app.db`、`backend/data/chroma/` 和 `backend/data/uploads/`，不需要手动迁移。数据目录和 `.env` 已被 Git 忽略。若将 SQLite 切换为 PostgreSQL，修改 `DATABASE_URL` 并安装对应 SQLAlchemy 驱动；生产升级还应引入 Alembic 迁移。

### 环境变量

| 变量 | 用途 |
| --- | --- |
| `OPENAI_API_KEY` | 必填，兼容服务的 API Key；示例 `replace-me` 不能用于请求 |
| `OPENAI_BASE_URL` | 兼容 OpenAI API 的 `/v1` 地址 |
| `CHAT_MODEL` | 聊天模型名 |
| `EMBEDDING_MODEL` | 向量模型名；该服务必须提供 Embeddings API |
| `DATABASE_URL` | SQLAlchemy 数据库连接串 |
| `CHROMA_PATH`, `UPLOAD_DIR` | 本地向量库与原文件目录 |
| `CORS_ORIGINS` | 允许跨域的前端地址，多个用逗号隔开 |
| `MAX_UPLOAD_MB` | 单文件大小上限 |
| `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K` | 分块长度、重叠字符数、检索片段数 |

`frontend/.env.example` 给出可选的 `VITE_API_BASE_URL=/api`。更换 Embedding 模型后旧向量与新问题可能维度或语义不兼容，应重新上传文档建立索引。

## 项目工作流程

用户上传文档 → 前端 `POST /api/documents` → FastAPI 路由调用 `document_service` → PyMuPDF 解析 PDF 或读取 UTF-8 文本 → 清洗 → 按字符分块并保留 overlap → `embedding_service` 调用 Embeddings API → 连同 `document_id`、`file_name`、`chunk_index`、`content` 存入 ChromaDB。

用户提问 → 前端 `POST /api/chat/stream` → 问题转 Embedding → ChromaDB 查询 top-k chunks → `rag_service` 构建上下文 → `llm_service` 构建 Prompt 并调用聊天模型 → FastAPI `StreamingResponse` 发送 SSE 事件 → 前端 `fetch` + `ReadableStream` 逐段展示 → 同时显示引用的文件名、chunk 编号和文本片段。会话与消息保存在 SQLite。

向量索引与 SQLite 各有职责：SQLite 管理文档清单、统计、会话及消息；Chroma 管理 chunk 内容、元数据与向量。上传过程发生错误会清理已写入的向量和原文件。

## 手动测试

1. 在“文档管理”上传 UTF-8 TXT 或 MD（例如写一行“本课程的期末项目是知识库系统”），确认文档和 chunk 数增加。
2. 在“文档问答”输入“期末项目是什么？”，观察回答逐段出现，展开回答下方的引用查看文件名、chunk 编号和原文。
3. 打开“历史会话”并回到该会话，确认提问与回答存在；新建对话或删除会话。
4. 删除刚上传的文档，确认列表与 chunk 统计减少；同样的问题此后不应再引用这份文档。

也可直接访问 `http://localhost:8000/docs` 调用接口。健康检查：`GET /api/health`。

离线验证（集成测试用假的 Embedding 与 LLM 响应，不会调用付费 API）：

```bash
cd backend
python -m unittest discover -s tests -v
cd ../frontend
npm run build
```

## Docker

先复制并填写 `backend/.env`，再在仓库根目录运行：

```bash
docker compose up --build
```

浏览器打开 http://localhost:5173。Compose 使用持久卷保存 SQLite、Chroma 与上传文件。容器中的前端 Nginx 将 `/api` 代理到后端，并关闭该路径的代理缓冲，以便 SSE 实时显示。

## 当前边界

扫描版 PDF 没有可提取文本时需要先 OCR。默认单文件上限 15 MB，解析与 embedding 在上传请求内完成，适合小型本地知识库。项目未加入用户鉴权，因此不应直接公开部署到互联网。API 服务必须同时支持聊天流式接口和 Embeddings API。生产扩展路线见 [升级路线](docs/improvement-roadmap.md)。

## 学习资料

- [按十阶段阅读代码](docs/learning-guide.md)
- [项目面试问题与简答](docs/interview-questions.md)
- [升级路线](docs/improvement-roadmap.md)
