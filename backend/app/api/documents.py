from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.api import DocumentOut
from app.services.document_service import add_document, delete_document, list_documents

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def get_documents(db: Session = Depends(get_db)):
    return list_documents(db)


@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await add_document(file, db)


@router.delete("/{document_id}", status_code=204)
def remove_document(document_id: int, db: Session = Depends(get_db)):
    delete_document(document_id, db)
