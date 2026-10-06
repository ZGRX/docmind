from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.session import get_db
from app.models import Conversation
from app.schemas.api import ConversationDetail, ConversationOut, MessageOut

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db)):
    return list(db.scalars(select(Conversation).order_by(Conversation.created_at.desc(), Conversation.id.desc())))


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise AppError(404, "会话不存在")
    return ConversationDetail(
        id=conversation.id, title=conversation.title, created_at=conversation.created_at,
        messages=[MessageOut.from_entity(item) for item in conversation.messages],
    )


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise AppError(404, "会话不存在")
    db.delete(conversation)
    db.commit()
