from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    content = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Agent-related fields
    agent_state = Column(String(50), default="idle")
    agent_config = Column(JSON, nullable=True)
    preview_version = Column(Integer, default=1)
    plan_data = Column(JSON, nullable=True)
    last_preview_update = Column(DateTime, default=datetime.utcnow)
    
    # Status tracking
    status = Column(String(50), default="draft")  # draft, in_progress, completed

    versions = relationship("DocumentVersion", back_populates="document")
    conversation = relationship("Conversation", back_populates="document", uselist=False)  # 1:1 relationship
    images = relationship("DocumentImage", back_populates="document")
    agent_messages = relationship("AgentMessage", back_populates="document")


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    content = Column(JSON, nullable=False)
    version_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    change_description = Column(Text, nullable=True)

    document = relationship("Document", back_populates="versions")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, unique=True)  # Enforce 1:1
    messages = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("Document", back_populates="conversation")


class DocumentImage(Base):
    __tablename__ = "document_images"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    url = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="images")


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    agent_type = Column(String(50), nullable=False)
    message_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="agent_messages")