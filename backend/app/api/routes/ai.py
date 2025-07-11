from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from app.core.database import get_db
from app.services.ai_service_direct import AIService
from app.services.document_intelligence import DocumentIntelligenceService
from app.services.conversation_service import ConversationService
from app.services.prompt_service import DocumentType
from app.models.schemas import WebSocketMessage
from app.services.websocket_service import WebSocketManager
from app.agents.document_orchestrator import DocumentOrchestrator
from app.agents.agent_config import agent_config_manager
from app.agents.agent_states import agent_state_manager
from pydantic import BaseModel
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/health")
async def health_check():
    """AI routes health check"""
    return {"status": "healthy", "service": "ai"}


class ChatRequest(BaseModel):
    message: str
    document_id: Optional[int] = None
    conversation_id: Optional[int] = None
    provider: str = "openai"
    model: Optional[str] = None


class DocumentGenerationRequest(BaseModel):
    prompt: str
    document_type: DocumentType
    provider: str = "openai"
    model: Optional[str] = None


class ContentExpansionRequest(BaseModel):
    section_title: str
    current_content: str
    user_request: str
    provider: str = "openai"
    model: Optional[str] = None


class StyleAdjustmentRequest(BaseModel):
    document_content: Dict[str, Any]
    style_request: str
    provider: str = "openai"
    model: Optional[str] = None


class IntentAnalysisRequest(BaseModel):
    user_input: str
    document_id: Optional[int] = None


class StreamChatRequest(BaseModel):
    message: str
    document_id: Optional[int] = None
    conversation_id: Optional[int] = None
    provider: str = "openai"
    model: Optional[str] = None


websocket_manager = WebSocketManager()


@router.get("/providers")
async def get_available_providers():
    """Get list of available AI providers"""
    try:
        ai_service = AIService()
        providers = ai_service.get_available_providers()
        
        provider_info = {}
        for provider in providers:
            provider_info[provider] = {
                "name": provider.title(),
                "models": ai_service.get_provider_models(provider),
                "available": True
            }
        
        return {
            "providers": provider_info,
            "default": ai_service.default_provider
        }
    except Exception as e:
        print(f"Error in get_available_providers: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get providers: {str(e)}"
        )


@router.post("/chat")
async def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Chat with AI assistant"""
    try:
        intelligence_service = DocumentIntelligenceService(db)
        conversation_service = ConversationService(db)
        
        # Process conversational request
        if request.document_id and request.conversation_id:
            result = await intelligence_service.process_conversational_request(
                request.message,
                request.document_id,
                request.conversation_id,
                request.provider
            )
            
            # Save conversation
            conversation_service.add_message(
                request.conversation_id,
                "user",
                request.message
            )
            conversation_service.add_message(
                request.conversation_id,
                "assistant",
                result["response"]
            )
            
            # Broadcast to WebSocket if document_id provided
            if request.document_id:
                await websocket_manager.broadcast_to_document(
                    request.document_id,
                    WebSocketMessage(
                        type="chat_message",
                        data={
                            "role": "assistant",
                            "content": result["response"],
                            "intent": result["intent"]
                        }
                    )
                )
            
            return result
            
        else:
            # Simple AI chat without document context
            ai_service = AIService()
            messages = [{"role": "user", "content": request.message}]
            response = await ai_service.generate_response(
                messages,
                provider=request.provider,
                model=request.model
            )
            
            return {
                "response": response,
                "intent": {"intent": "chat", "confidence": 0.8}
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.post("/chat/stream")
async def stream_chat_with_ai(
    request: StreamChatRequest,
    db: Session = Depends(get_db)
):
    """Stream chat response from AI"""
    try:
        ai_service = AIService()
        
        # Get conversation context if available
        messages = [{"role": "user", "content": request.message}]
        conversation_service = ConversationService(db) if request.conversation_id else None
        
        if request.conversation_id and conversation_service:
            context = conversation_service.get_conversation_context(request.conversation_id)
            messages = context + [{"role": "user", "content": request.message}]
        
        async def generate_stream():
            full_response = ""
            async for chunk in ai_service.stream_response(
                messages,
                provider=request.provider,
                model=request.model
            ):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            # Save conversation if conversation_id provided
            if request.conversation_id and conversation_service:
                conversation_service.add_message(
                    request.conversation_id,
                    "user",
                    request.message
                )
                conversation_service.add_message(
                    request.conversation_id,
                    "assistant",
                    full_response
                )
            
            yield f"data: {json.dumps({'done': True})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stream chat failed: {str(e)}"
        )


@router.post("/analyze-intent")
async def analyze_user_intent(
    request: IntentAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze user intent from input"""
    try:
        intelligence_service = DocumentIntelligenceService(db)
        intent_data = await intelligence_service.analyze_user_intent(
            request.user_input,
            request.document_id
        )
        
        return intent_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intent analysis failed: {str(e)}"
        )


@router.post("/generate-document")
async def generate_document_structure(
    request: DocumentGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate document structure from prompt"""
    try:
        intelligence_service = DocumentIntelligenceService(db)
        structure = await intelligence_service.generate_document_structure(
            request.prompt,
            request.document_type,
            request.provider
        )
        
        return structure
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document generation failed: {str(e)}"
        )


@router.post("/expand-content")
async def expand_section_content(
    request: ContentExpansionRequest,
    db: Session = Depends(get_db)
):
    """Expand or modify section content"""
    try:
        intelligence_service = DocumentIntelligenceService(db)
        expanded_content = await intelligence_service.expand_section_content(
            request.section_title,
            request.current_content,
            request.user_request,
            request.provider
        )
        
        return {"expanded_content": expanded_content}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content expansion failed: {str(e)}"
        )


@router.post("/adjust-style")
async def adjust_document_style(
    request: StyleAdjustmentRequest,
    db: Session = Depends(get_db)
):
    """Adjust document style/tone"""
    try:
        intelligence_service = DocumentIntelligenceService(db)
        adjusted_content = await intelligence_service.adjust_document_style(
            request.document_content,
            request.style_request,
            request.provider
        )
        
        return {"adjusted_content": adjusted_content}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Style adjustment failed: {str(e)}"
        )


@router.post("/suggest-images")
async def suggest_document_images(
    document_content: Dict[str, Any],
    section_title: Optional[str] = None,
    provider: str = "openai",
    db: Session = Depends(get_db)
):
    """Suggest relevant images for document"""
    try:
        intelligence_service = DocumentIntelligenceService(db)
        suggestions = await intelligence_service.suggest_document_images(
            document_content,
            section_title,
            provider
        )
        
        return {"image_suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image suggestion failed: {str(e)}"
        )


@router.post("/summarize")
async def generate_document_summary(
    document_content: Dict[str, Any],
    provider: str = "openai",
    db: Session = Depends(get_db)
):
    """Generate document summary"""
    try:
        intelligence_service = DocumentIntelligenceService(db)
        summary = await intelligence_service.generate_document_summary(
            document_content,
            provider
        )
        
        return {"summary": summary}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {str(e)}"
        )


@router.get("/conversation/{conversation_id}/context")
async def get_conversation_context(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Get conversation context for AI"""
    try:
        conversation_service = ConversationService(db)
        context = conversation_service.get_conversation_context(conversation_id)
        stats = conversation_service.get_conversation_stats(conversation_id)
        
        return {
            "context": context,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation context: {str(e)}"
        )


@router.post("/conversation/{document_id}/create")
async def create_conversation(
    document_id: int,
    initial_message: str,
    db: Session = Depends(get_db)
):
    """Create new conversation for document"""
    try:
        conversation_service = ConversationService(db)
        conversation = conversation_service.create_conversation(
            document_id,
            initial_message
        )
        
        return {
            "conversation_id": conversation.id,
            "document_id": conversation.document_id,
            "created_at": conversation.created_at
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )


# Agent Orchestration Routes

@router.post("/agents/chat")
async def agent_chat(
    request: StreamChatRequest,
    db: Session = Depends(get_db)
):
    """Chat using agent orchestration system"""
    try:
        if not request.document_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document ID is required for agent chat"
            )
        
        # Initialize orchestrator for this document
        orchestrator = DocumentOrchestrator(
            document_id=request.document_id,
            config=agent_config_manager.get_config(request.document_id)
        )
        
        # Get conversation context
        conversation_service = ConversationService(db)
        conversation = conversation_service.get_or_create_conversation(request.document_id)
        conversation_history = conversation_service.get_conversation_context(conversation.id)
        
        # Process request with orchestrator
        result = await orchestrator.process_user_request(
            user_message=request.message,
            conversation_id=conversation.id,
            conversation_history=conversation_history
        )
        
        if result["success"]:
            # Save conversation messages
            conversation_service.add_message(conversation.id, "user", request.message)
            conversation_service.add_message(conversation.id, "assistant", result["response"])
            
            # Broadcast agent messages via WebSocket
            for agent_message in result.get("messages", []):
                await websocket_manager.broadcast_to_document(
                    request.document_id,
                    WebSocketMessage(
                        type="agent_message",
                        data=agent_message.to_dict()
                    )
                )
            
            return {
                "response": result["response"],
                "plan_updated": result.get("plan_updated", False),
                "preview_ready": result.get("preview_ready", False),
                "agent_state": agent_state_manager.get_state_info(),
                "processing_time": result.get("processing_time", 0)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Agent processing failed")
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent chat failed: {str(e)}"
        )


@router.post("/agents/chat/stream")
async def agent_stream_chat(
    request: StreamChatRequest,
    db: Session = Depends(get_db)
):
    """Stream chat response using agent orchestration"""
    try:
        if not request.document_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document ID is required for agent chat"
            )
        
        # Initialize services
        from app.services.document_service import DocumentService
        document_service = DocumentService(db)
        
        # Initialize orchestrator
        orchestrator = DocumentOrchestrator(
            document_id=request.document_id,
            config=agent_config_manager.get_config(request.document_id),
            document_service=document_service,
            websocket_manager=websocket_manager
        )
        
        # Get conversation context
        conversation_service = ConversationService(db)
        conversation = conversation_service.get_or_create_conversation(request.document_id)
        conversation_history = conversation_service.get_conversation_context(conversation.id)
        
        async def generate_agent_stream():
            try:
                # Setup activity callback to yield agent process events in real-time
                activity_queue = asyncio.Queue()
                
                async def activity_callback(activity):
                    await activity_queue.put(activity)
                
                orchestrator.add_activity_callback(activity_callback)
                
                # Process request and capture activities
                full_response = ""
                
                # Send initial activity to show processing has started
                from datetime import datetime
                initial_activity = {
                    "agent": "orchestrator",
                    "action": "Analyzing your request",
                    "status": "in_progress",
                    "startTime": datetime.utcnow().isoformat(),
                    "input": request.message,
                    "output": None,
                    "error": None,
                    "metadata": {}
                }
                yield f"data: {json.dumps({'agent_activity': initial_activity})}\n\n"
                
                # Create a task to process the orchestrator request
                async def process_orchestrator():
                    result = await orchestrator.process_user_request(
                        user_message=request.message,
                        conversation_id=conversation.id,
                        conversation_history=conversation_history
                    )
                    # Signal completion
                    await activity_queue.put({"_type": "orchestrator_done", "result": result})
                
                # Start orchestrator processing
                orchestrator_task = asyncio.create_task(process_orchestrator())
                
                # Stream activities as they happen
                while True:
                    try:
                        # Wait for next activity with timeout
                        activity = await asyncio.wait_for(activity_queue.get(), timeout=0.1)
                        
                        if activity.get("_type") == "orchestrator_done":
                            # Orchestrator completed, get the result
                            result = activity["result"]
                            break
                        else:
                            # Yield real-time activity
                            yield f"data: {json.dumps({'agent_activity': activity})}\n\n"
                    except asyncio.TimeoutError:
                        # No activity yet, continue waiting
                        continue
                    except Exception as e:
                        logger.error(f"Error processing activity: {e}")
                        break
                
                # Wait for orchestrator to complete if not already done
                if not orchestrator_task.done():
                    await orchestrator_task
                
                # Now stream the actual response content
                if result.get("success", False):
                    response = result["response"]
                    words = response.split()
                    
                    for word in words:
                        chunk = word + " "
                        full_response += chunk
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                        await asyncio.sleep(0.02)  # Small delay for streaming effect
                else:
                    error_msg = result.get('error', 'Unknown error occurred')
                    logger.error(f"Agent processing failed: {error_msg}")
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    full_response = f"I apologize, but I encountered an error: {error_msg}"
                
                # Save conversation
                conversation_service.add_message(conversation.id, "user", request.message)
                conversation_service.add_message(conversation.id, "assistant", full_response)
                
                # Send final state
                yield f"data: {json.dumps({'done': True, 'agent_state': agent_state_manager.get_state_info()})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in agent stream: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_agent_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent stream chat failed: {str(e)}"
        )


@router.get("/agents/state/{document_id}")
async def get_agent_state(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get current agent state for a document"""
    try:
        orchestrator = DocumentOrchestrator(document_id)
        state = orchestrator.get_current_state()
        
        return {
            "document_id": document_id,
            "agent_state": state,
            "global_state": agent_state_manager.get_state_info()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent state: {str(e)}"
        )


@router.post("/agents/config/{document_id}")
async def update_agent_config(
    document_id: int,
    config_updates: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update agent configuration for a document"""
    try:
        agent_config_manager.update_config(config_updates, document_id)
        
        return {
            "success": True,
            "message": "Agent configuration updated",
            "config": agent_config_manager.get_config(document_id).to_dict()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent config: {str(e)}"
        )


@router.get("/agents/config/{document_id}")
async def get_agent_config(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get agent configuration for a document"""
    try:
        config = agent_config_manager.get_config(document_id)
        
        return {
            "document_id": document_id,
            "config": config.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent config: {str(e)}"
        )