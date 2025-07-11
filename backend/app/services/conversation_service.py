from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.document import Conversation, Document
from app.models.schemas import MessageBase, ConversationCreate, ConversationResponse
from datetime import datetime
import json


class ConversationService:
    def __init__(self, db: Session):
        self.db = db
        self.max_context_length = 4000  # Token limit for context
        self.max_messages_in_context = 20

    def create_conversation(self, document_id: int, initial_message: str) -> Conversation:
        """Create a new conversation for a document (1:1 relationship)"""
        
        # Check if conversation already exists for this document
        existing_conversation = self.db.query(Conversation).filter(
            Conversation.document_id == document_id
        ).first()
        
        if existing_conversation:
            # Return existing conversation or update it
            if initial_message:
                self.add_message(existing_conversation.id, "user", initial_message)
            return existing_conversation
        
        messages = [
            MessageBase(
                role="user",
                content=initial_message,
                timestamp=datetime.utcnow()
            )
        ]
        
        conversation = Conversation(
            document_id=document_id,
            messages=[msg.dict() for msg in messages]
        )
        
        try:
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            return conversation
        except IntegrityError:
            # Handle race condition - conversation was created by another process
            self.db.rollback()
            existing_conversation = self.db.query(Conversation).filter(
                Conversation.document_id == document_id
            ).first()
            return existing_conversation

    def add_message(self, conversation_id: int, role: str, content: str) -> Conversation:
        """Add a message to existing conversation"""
        try:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                raise ValueError("Conversation not found")
            
            # Create message with serializable timestamp
            timestamp = datetime.utcnow()
            new_message = {
                "role": role,
                "content": content,
                "timestamp": timestamp.isoformat()  # Convert to ISO string for JSON serialization
            }
            
            messages = conversation.messages or []
            messages.append(new_message)
            
            conversation.messages = messages
            self.db.commit()
            self.db.refresh(conversation)
            
            return conversation
            
        except Exception as e:
            self.db.rollback()
            # Log error but don't crash the entire system
            print(f"Error adding message to conversation {conversation_id}: {e}")
            # Return the conversation without the new message to allow system to continue
            return conversation if 'conversation' in locals() else None

    def get_conversation_history(self, document_id: int) -> List[Conversation]:
        """Get all conversations for a document"""
        return self.db.query(Conversation).filter(
            Conversation.document_id == document_id
        ).order_by(Conversation.created_at.desc()).all()

    def get_conversation_context(self, conversation_id: int) -> List[Dict[str, str]]:
        """Get conversation context optimized for LLM"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return []
        
        messages = conversation.messages or []
        
        # Convert to LLM format and limit context
        context_messages = []
        total_tokens = 0
        
        for msg in reversed(messages[-self.max_messages_in_context:]):
            message_dict = {
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }
            
            # Rough token estimation (4 characters ≈ 1 token)
            estimated_tokens = len(message_dict["content"]) // 4
            
            if total_tokens + estimated_tokens > self.max_context_length:
                break
                
            context_messages.insert(0, message_dict)
            total_tokens += estimated_tokens
        
        return context_messages

    def summarize_conversation(self, conversation_id: int) -> str:
        """Create a summary of conversation for context compression"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return ""
        
        messages = conversation.messages or []
        
        # Create summary of key points
        summary_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if len(content) > 200:
                content = content[:200] + "..."
            summary_parts.append(f"{role}: {content}")
        
        return "\n".join(summary_parts)

    def get_document_conversations(self, document_id: int) -> List[ConversationResponse]:
        """Get all conversations for a document with response format"""
        conversations = self.db.query(Conversation).filter(
            Conversation.document_id == document_id
        ).order_by(Conversation.created_at.desc()).all()
        
        return [
            ConversationResponse(
                id=conv.id,
                document_id=conv.document_id,
                messages=[MessageBase(**msg) for msg in conv.messages],
                created_at=conv.created_at
            )
            for conv in conversations
        ]

    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return False
        
        self.db.delete(conversation)
        self.db.commit()
        return True

    def get_recent_messages(self, document_id: int, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent messages across all conversations for a document"""
        conversations = self.db.query(Conversation).filter(
            Conversation.document_id == document_id
        ).order_by(Conversation.created_at.desc()).all()
        
        all_messages = []
        for conv in conversations:
            messages = conv.messages or []
            for msg in messages:
                all_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                    "timestamp": msg.get("timestamp", conv.created_at.isoformat()),
                    "conversation_id": conv.id
                })
        
        # Sort by timestamp and limit
        all_messages.sort(key=lambda x: x["timestamp"], reverse=True)
        return all_messages[:limit]

    def estimate_tokens(self, text: str) -> int:
        """Rough estimation of tokens in text"""
        return len(text) // 4

    def truncate_context(self, messages: List[Dict[str, str]], max_tokens: int) -> List[Dict[str, str]]:
        """Truncate conversation context to fit within token limit"""
        truncated = []
        total_tokens = 0
        
        for msg in reversed(messages):
            msg_tokens = self.estimate_tokens(msg["content"])
            if total_tokens + msg_tokens > max_tokens:
                break
            truncated.insert(0, msg)
            total_tokens += msg_tokens
        
        return truncated

    def get_conversation_stats(self, document_id: int) -> Dict[str, Any]:
        """Get statistics about conversations for a document"""
        conversations = self.db.query(Conversation).filter(
            Conversation.document_id == document_id
        ).all()
        
        total_messages = 0
        total_characters = 0
        user_messages = 0
        ai_messages = 0
        
        for conv in conversations:
            messages = conv.messages or []
            total_messages += len(messages)
            
            for msg in messages:
                content = msg.get("content", "")
                total_characters += len(content)
                
                if msg.get("role") == "user":
                    user_messages += 1
                else:
                    ai_messages += 1
        
        return {
            "total_conversations": len(conversations),
            "total_messages": total_messages,
            "user_messages": user_messages,
            "ai_messages": ai_messages,
            "total_characters": total_characters,
            "avg_message_length": total_characters / total_messages if total_messages > 0 else 0
        }
    
    def get_or_create_conversation(self, document_id: int) -> Conversation:
        """Get existing conversation or create new one for document (1:1 relationship)"""
        
        # Try to get existing conversation
        existing_conversation = self.db.query(Conversation).filter(
            Conversation.document_id == document_id
        ).first()
        
        if existing_conversation:
            return existing_conversation
        
        # Create new conversation with empty messages
        conversation = Conversation(
            document_id=document_id,
            messages=[]
        )
        
        try:
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            return conversation
        except IntegrityError:
            # Handle race condition
            self.db.rollback()
            existing_conversation = self.db.query(Conversation).filter(
                Conversation.document_id == document_id
            ).first()
            return existing_conversation