import json
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TimeStampedOut(BaseModel):
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def sqlite_time_is_utc(cls, value: datetime) -> datetime:
        # SQLite returns naive datetimes even when the column is timezone aware.
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


class DocumentOut(TimeStampedOut):
    model_config = ConfigDict(from_attributes=True)
    id: int
    file_name: str
    file_type: str
    chunk_count: int


class StatsOut(BaseModel):
    document_count: int
    chunk_count: int
    conversation_count: int
    recent_documents: list[DocumentOut]


class SourceOut(BaseModel):
    document_id: int
    file_name: str
    chunk_index: int
    content: str


class MessageOut(TimeStampedOut):
    id: int
    role: str
    content: str
    sources: list[SourceOut]

    @classmethod
    def from_entity(cls, message):
        return cls(id=message.id, role=message.role, content=message.content,
                   created_at=message.created_at, sources=json.loads(message.sources_json))


class ConversationOut(TimeStampedOut):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: int | None = Field(default=None, gt=0)

    @field_validator("question")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("问题不能为空")
        return value
