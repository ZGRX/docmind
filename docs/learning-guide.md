# 反向学习指南

建议先跑通一份短 TXT 的上传和提问，再按下面顺序追踪代码。每阶段都可以在浏览器开发者工具的 Network 面板或 FastAPI 的 `/docs` 中观察请求。

## 第一阶段：前端请求如何发送到 FastAPI

重点读：`frontend/src/api/client.js`、`frontend/vite.config.js`、`frontend/src/views/Documents.vue`。

文档页调用 Pinia store，store 用 Axios 向 `/api/documents` 发请求。开发服务器把 `/api` 代理到 8000 端口。先观察上传请求的 `multipart/form-data` 和返回的 JSON。

## 第二阶段：FastAPI 路由和 Service 层如何协作

重点读：`backend/app/main.py`、`backend/app/api/documents.py`、`backend/app/services/document_service.py`、`backend/app/schemas/api.py`。

`main.py` 注册路由和异常处理；路由负责接收、校验参数与返回结果；Service 负责业务处理。`Depends(get_db)` 为请求提供数据库会话。试着从上传按钮一路追到 `add_document()`。

## 第三阶段：文件上传和 PDF 解析

重点读：`backend/app/services/document_service.py` 中的 `add_document()`、`extract_text()`。

上传先检查扩展名和大小，再按块写磁盘。PDF 用 PyMuPDF 逐页提取文本；TXT/MD 用 UTF-8 读取。扫描版 PDF 是图片，当前实现不能 OCR。比较上传 TXT 与 PDF 后的 chunk 数量。

## 第四阶段：chunking 如何实现

重点读：`backend/app/services/document_service.py` 中的 `clean_text()`、`split_chunks()`；`backend/app/core/config.py`。

清洗换行和空格后，按字符长度切分，尽量在段落或句末截断。相邻块重叠 `CHUNK_OVERLAP` 个字符，以免边界附近的信息丢失。调整 `.env` 的 `CHUNK_SIZE`，重启并重新上传一份文档，观察 chunk 数变化。

## 第五阶段：embedding 是什么以及代码在哪里

重点读：`backend/app/services/embedding_service.py`、`backend/app/services/document_service.py`。

Embedding 是把文本转成一组浮点数，使语义相近的文本在向量空间里靠近。上传时对 chunks 批量调用 Embeddings API；提问时同一模型也对问题生成向量。换模型后需重建已有索引。

## 第六阶段：ChromaDB 如何保存和搜索数据

重点读：`backend/app/services/document_service.py` 中的 `get_collection()`、`add_document()`、`delete_document()`；`backend/app/services/rag_service.py`。

Chroma collection 持久化在 `backend/data/chroma`。每条向量带 `document_id`、`file_name`、`chunk_index`，正文存在 `documents` 字段。`query()` 用问题向量做余弦相似度检索；删除文档时按 `document_id` 清除向量。

## 第七阶段：完整 RAG 流程

重点读：`backend/app/api/chat.py`、`backend/app/services/rag_service.py`、`backend/app/services/llm_service.py`。

问题 → embedding → Chroma top-k → 把命中的 chunk 编号和正文组成上下文 → 构建 Prompt → 调用 LLM。模型被要求只依据资料回答并用 `[1]` 等编号引用。引用元数据由后端直接返回，不能把模型自称的引用当成真实检索结果。

## 第八阶段：流式响应如何实现

重点读：`backend/app/api/chat.py` 中的 `StreamingResponse`、`frontend/src/api/client.js` 中的 `streamChat()`、`frontend/src/stores/chat.js`。

后端把 `meta`、`token`、`done`、`error` 编成 SSE 帧。前端 `fetch()` 获取 `ReadableStream`，用 `TextDecoder` 处理 UTF-8 分片，再按空行拆帧。注意一个网络分片可能只包含半个汉字或半个事件，所以必须保留 `buffer`。

## 第九阶段：聊天历史如何存储

重点读：`backend/app/models/entities.py`、`backend/app/api/conversations.py`、`backend/app/api/chat.py`、`frontend/src/stores/chat.js`。

SQLite 有 `conversations` 和 `messages` 表，消息保存 role、content、created_at 和来源 JSON。提问先写入 user 消息；流完整结束后写入 assistant 消息。前端可以读取、清空当前界面、重新打开或删除历史会话。`清空对话` 开始新会话，不删除旧会话。

## 第十阶段：Docker 如何运行整个项目

重点读：`docker-compose.yml`、`backend/Dockerfile`、`frontend/Dockerfile`、`frontend/nginx.conf`。

Compose 启动两个容器，后端用 Uvicorn，前端经 Node 构建后由 Nginx 提供静态文件。Nginx 把 `/api` 转发给 `backend:8000`，同时关闭代理缓冲以支持流式输出。命名卷保存 `backend/data`，重建容器也能保留文档和会话。

## 自测顺序

1. 上传短 TXT，检查首页统计与 Chroma 中的 chunk 数对应。
2. 提一个能从 TXT 中找到答案的问题，观察 SSE `meta` 和多个 `token`。
3. 刷新页面，从历史会话打开回答并展开引用。
4. 删除文档，再问同一问题，检查不再引用已删除的文件。
