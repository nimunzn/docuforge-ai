from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


class DocumentBase(BaseModel):
    title: str
    type: str
    content: Optional[Dict[str, Any]] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    content: Optional[Dict[str, Any]] = None


class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentVersionBase(BaseModel):
    content: Dict[str, Any]
    version_number: int
    change_description: Optional[str] = None


class DocumentVersionCreate(DocumentVersionBase):
    document_id: int


class DocumentVersionResponse(DocumentVersionBase):
    id: int
    document_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    role: str
    content: str
    timestamp: datetime


class ConversationBase(BaseModel):
    messages: List[MessageBase]


class ConversationCreate(ConversationBase):
    document_id: int


class ConversationResponse(ConversationBase):
    id: int
    document_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentImageBase(BaseModel):
    prompt: str
    url: str


class DocumentImageCreate(DocumentImageBase):
    document_id: int


class DocumentImageResponse(DocumentImageBase):
    id: int
    document_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExportRequest(BaseModel):
    format: str
    include_images: bool = True


class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]