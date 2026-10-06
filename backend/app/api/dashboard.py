from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Conversation, Document
from app.schemas.api import StatsOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    return StatsOut(
        document_count=db.scalar(select(func.count(Document.id))) or 0,
        chunk_count=db.scalar(select(func.coalesce(func.sum(Document.chunk_count), 0))) or 0,
        conversation_count=db.scalar(select(func.count(Conversation.id))) or 0,
        recent_documents=list(db.scalars(select(Document).order_by(Document.created_at.desc(), Document.id.desc()).limit(5))),
    )
