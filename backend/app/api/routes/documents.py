from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.document import Document, DocumentVersion, DocumentImage
from app.models.schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse,
    DocumentVersionResponse, DocumentImageResponse,
    ExportRequest
)
from app.services.document_service import DocumentService
from app.services.export_service import ExportService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    return await service.create_document(document)


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    return await service.get_documents(skip=skip, limit=limit)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    document = await service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    document = await service.update_document(document_id, document_update)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    success = await service.delete_document(document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )


@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
async def get_document_versions(
    document_id: int,
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    return await service.get_document_versions(document_id)


@router.post("/{document_id}/export")
async def export_document(
    document_id: int,
    export_request: ExportRequest,
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    document = await service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    export_service = ExportService()
    file_bytes = await export_service.export_document(
        document, 
        export_request.format, 
        export_request.include_images
    )
    
    return {"download_url": f"/api/downloads/{document_id}/{export_request.format}"}


@router.get("/{document_id}/images", response_model=List[DocumentImageResponse])
async def get_document_images(
    document_id: int,
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    return await service.get_document_images(document_id)