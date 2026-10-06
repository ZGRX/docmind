import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import chat, conversations, dashboard, documents
from app.core.config import get_settings
from app.db.session import Base, engine
from app import models  # noqa: F401 - imports SQLAlchemy models before create_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Study Assistant", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins,
                   allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(documents.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.exception_handler(HTTPException)
async def http_error(_request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exc: RequestValidationError):
    details = [{"field": ".".join(map(str, item["loc"])), "message": item["msg"]}
               for item in exc.errors()]
    return JSONResponse(status_code=422, content={"error": "请求参数无效", "details": details})


@app.exception_handler(Exception)
async def unexpected_error(_request: Request, exc: Exception):
    logger.exception("Unexpected API error", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": "服务器内部错误"})
