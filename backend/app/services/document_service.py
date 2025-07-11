from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import desc, select
from typing import List, Optional, Union
from app.models.document import Document, DocumentVersion, DocumentImage
from app.models.schemas import DocumentCreate, DocumentUpdate
from datetime import datetime
import asyncio
from functools import wraps


def sync_fallback(func):
    """Decorator to provide sync fallback for async methods"""
    @wraps(func)
    async def async_wrapper(self, *args, **kwargs):
        if isinstance(self.db, AsyncSession):
            return await func(self, *args, **kwargs)
        else:
            # For sync sessions, run in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: func.__wrapped__(self, *args, **kwargs))
    return async_wrapper


class DocumentService:
    def __init__(self, db: Union[Session, AsyncSession]):
        self.db = db
        self.is_async = isinstance(db, AsyncSession)

    async def create_document(self, document: DocumentCreate) -> Document:
        db_document = Document(
            title=document.title,
            type=document.type,
            content=document.content or {}
        )
        
        if self.is_async:
            self.db.add(db_document)
            await self.db.commit()
            await self.db.refresh(db_document)
            
            version = DocumentVersion(
                document_id=db_document.id,
                content=db_document.content,
                version_number=1,
                change_description="Initial version"
            )
            self.db.add(version)
            await self.db.commit()
        else:
            self.db.add(db_document)
            self.db.commit()
            self.db.refresh(db_document)
            
            version = DocumentVersion(
                document_id=db_document.id,
                content=db_document.content,
                version_number=1,
                change_description="Initial version"
            )
            self.db.add(version)
            self.db.commit()
        
        return db_document

    async def get_documents(self, skip: int = 0, limit: int = 100) -> List[Document]:
        if self.is_async:
            stmt = select(Document).order_by(desc(Document.updated_at)).offset(skip).limit(limit)
            result = await self.db.execute(stmt)
            return result.scalars().all()
        else:
            return self.db.query(Document).order_by(desc(Document.updated_at)).offset(skip).limit(limit).all()

    async def get_document(self, document_id: int) -> Optional[Document]:
        if self.is_async:
            stmt = select(Document).where(Document.id == document_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        else:
            return self.db.query(Document).filter(Document.id == document_id).first()

    async def update_document(self, document_id: int, document_update: DocumentUpdate) -> Optional[Document]:
        if self.is_async:
            # Async version
            stmt = select(Document).where(Document.id == document_id)
            result = await self.db.execute(stmt)
            document = result.scalar_one_or_none()
            
            if not document:
                return None
            
            update_data = document_update.dict(exclude_unset=True)
            
            if update_data.get("content"):
                version_stmt = select(DocumentVersion).where(
                    DocumentVersion.document_id == document_id
                ).order_by(desc(DocumentVersion.version_number))
                version_result = await self.db.execute(version_stmt)
                latest_version = version_result.scalar_one_or_none()
                
                new_version_number = (latest_version.version_number + 1) if latest_version else 1
                
                version = DocumentVersion(
                    document_id=document_id,
                    content=update_data["content"],
                    version_number=new_version_number,
                    change_description="Document updated"
                )
                self.db.add(version)
            
            for field, value in update_data.items():
                setattr(document, field, value)
            
            document.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(document)
            
            return document
        else:
            # Sync version
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return None
            
            update_data = document_update.dict(exclude_unset=True)
            
            if update_data.get("content"):
                latest_version = self.db.query(DocumentVersion).filter(
                    DocumentVersion.document_id == document_id
                ).order_by(desc(DocumentVersion.version_number)).first()
                
                new_version_number = (latest_version.version_number + 1) if latest_version else 1
                
                version = DocumentVersion(
                    document_id=document_id,
                    content=update_data["content"],
                    version_number=new_version_number,
                    change_description="Document updated"
                )
                self.db.add(version)
            
            for field, value in update_data.items():
                setattr(document, field, value)
            
            document.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(document)
            
            return document

    async def delete_document(self, document_id: int) -> bool:
        if self.is_async:
            stmt = select(Document).where(Document.id == document_id)
            result = await self.db.execute(stmt)
            document = result.scalar_one_or_none()
            
            if not document:
                return False
            
            await self.db.delete(document)
            await self.db.commit()
            return True
        else:
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return False
            
            self.db.delete(document)
            self.db.commit()
            return True

    async def get_document_versions(self, document_id: int) -> List[DocumentVersion]:
        if self.is_async:
            stmt = select(DocumentVersion).where(
                DocumentVersion.document_id == document_id
            ).order_by(desc(DocumentVersion.version_number))
            result = await self.db.execute(stmt)
            return result.scalars().all()
        else:
            return self.db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).order_by(desc(DocumentVersion.version_number)).all()

    async def get_document_images(self, document_id: int) -> List[DocumentImage]:
        if self.is_async:
            stmt = select(DocumentImage).where(
                DocumentImage.document_id == document_id
            ).order_by(desc(DocumentImage.created_at))
            result = await self.db.execute(stmt)
            return result.scalars().all()
        else:
            return self.db.query(DocumentImage).filter(
                DocumentImage.document_id == document_id
            ).order_by(desc(DocumentImage.created_at)).all()

    async def add_document_image(self, document_id: int, prompt: str, url: str) -> DocumentImage:
        image = DocumentImage(
            document_id=document_id,
            prompt=prompt,
            url=url
        )
        
        if self.is_async:
            self.db.add(image)
            await self.db.commit()
            await self.db.refresh(image)
        else:
            self.db.add(image)
            self.db.commit()
            self.db.refresh(image)
            
        return image