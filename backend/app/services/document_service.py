import re
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

import chromadb
import pymupdf as fitz
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models import Document
from app.services.embedding_service import embed_texts

ALLOWED_TYPES = {".pdf", ".txt", ".md", ".markdown"}


@lru_cache
def get_collection():
    client = chromadb.PersistentClient(path=get_settings().chroma_path)
    return client.get_or_create_collection("document_chunks", metadata={"hnsw:space": "cosine"})


def extract_text(path: Path, suffix: str) -> str:
    if suffix == ".pdf":
        with fitz.open(path) as pdf:
            return "\n\n".join(page.get_text() for page in pdf)
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AppError(400, "文本文件必须使用 UTF-8 编码") from exc


def clean_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def split_chunks(text: str, size: int, overlap: int) -> list[str]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("CHUNK_SIZE 必须大于 CHUNK_OVERLAP 且两者均为非负整数")
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        # Prefer a paragraph or sentence boundary near the end of a chunk.
        if end < len(text):
            boundary = max(text.rfind("\n\n", start + size // 2, end),
                           text.rfind("。", start + size // 2, end),
                           text.rfind(". ", start + size // 2, end))
            if boundary > start + overlap:
                end = boundary + (2 if text[boundary:boundary + 2] in ("\n\n", ". ") else 1)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


async def add_document(upload: UploadFile, db: Session) -> Document:
    settings = get_settings()
    file_name = Path(upload.filename or "").name
    suffix = Path(file_name).suffix.lower()
    if not file_name or suffix not in ALLOWED_TYPES:
        raise AppError(400, "只支持 PDF、TXT 和 Markdown (.md) 文件")
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{suffix}"
    path = upload_dir / stored_name
    size = 0
    document = None
    try:
        with path.open("wb") as target:
            while data := await upload.read(1024 * 1024):
                size += len(data)
                if size > settings.max_upload_mb * 1024 * 1024:
                    raise AppError(413, f"文件不能超过 {settings.max_upload_mb} MB")
                target.write(data)
        if not size:
            raise AppError(400, "文件不能为空")
        try:
            chunks = split_chunks(clean_text(extract_text(path, suffix)), settings.chunk_size, settings.chunk_overlap)
        except (fitz.FileDataError, ValueError) as exc:
            raise AppError(400, f"无法解析文件：{exc}") from exc
        if not chunks:
            raise AppError(400, "没有提取到文本；扫描版 PDF 需要先经过 OCR")
        document = Document(file_name=file_name[:255], file_type=suffix[1:], stored_name=stored_name, chunk_count=len(chunks))
        db.add(document)
        db.flush()
        collection = get_collection()
        for start in range(0, len(chunks), 50):
            batch = chunks[start:start + 50]
            collection.add(
                ids=[f"{document.id}:{i}" for i in range(start, start + len(batch))],
                documents=batch,
                embeddings=embed_texts(batch),
                metadatas=[{"document_id": document.id, "file_name": document.file_name, "chunk_index": i}
                           for i in range(start, start + len(batch))],
            )
        db.commit()
        db.refresh(document)
        return document
    except Exception:
        db.rollback()
        if document and document.id is not None:
            get_collection().delete(where={"document_id": document.id})
        path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()


def delete_document(document_id: int, db: Session) -> None:
    document = db.get(Document, document_id)
    if not document:
        raise AppError(404, "文档不存在")
    # Delete vectors before the SQL row so a vector error cannot leave a hidden orphan.
    get_collection().delete(where={"document_id": document_id})
    db.delete(document)
    db.commit()
    (Path(get_settings().upload_dir) / document.stored_name).unlink(missing_ok=True)


def list_documents(db: Session) -> list[Document]:
    return list(db.scalars(select(Document).order_by(Document.created_at.desc(), Document.id.desc())))
