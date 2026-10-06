import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import SessionLocal, get_db
from app.models import Conversation, Message
from app.schemas.api import ChatRequest
from app.services.llm_service import stream_answer
from app.services.rag_service import retrieve

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/stream")
async def chat_stream(body: ChatRequest, db: Session = Depends(get_db)):
    if not get_settings().openai_api_key or get_settings().openai_api_key == "replace-me":
        raise AppError(503, "请先在 backend/.env 配置 OPENAI_API_KEY")
    conversation = db.get(Conversation, body.conversation_id) if body.conversation_id else None
    if body.conversation_id and not conversation:
        raise AppError(404, "会话不存在")
    context, sources = await run_in_threadpool(retrieve, body.question)
    if not conversation:
        conversation = Conversation(title=body.question[:60])
        db.add(conversation)
        db.flush()
    db.add(Message(conversation_id=conversation.id, role="user", content=body.question))
    db.commit()
    conversation_id = conversation.id
    source_data = [source.model_dump() for source in sources]

    async def events():
        yield sse("meta", {"conversation_id": conversation_id, "sources": source_data})
        answer = ""
        try:
            async for token in stream_answer(body.question, context):
                answer += token
                yield sse("token", {"text": token})
            with SessionLocal() as session:
                session.add(Message(conversation_id=conversation_id, role="assistant", content=answer,
                                    sources_json=json.dumps(source_data, ensure_ascii=False)))
                session.commit()
            yield sse("done", {})
        except Exception:
            logger.exception("Chat stream failed")
            yield sse("error", {"message": "回答生成失败，请检查模型配置或稍后重试"})

    return StreamingResponse(events(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache", "X-Accel-Buffering": "no",
    })
