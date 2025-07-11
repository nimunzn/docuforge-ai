"""
Document Orchestrator
Main coordinator for all agent activities in document creation and modification
"""
from typing import Dict, Any, List, Optional, AsyncGenerator
import asyncio
import logging
import json
from datetime import datetime

from app.agents.agent_config import AgentConfig, AgentType, agent_config_manager
from app.agents.llm_router import LLMRouter
from app.agents.agent_states import (
    AgentState, AgentAction, AgentMessage, DocumentPlan, AgentContext,
    agent_state_manager, preview_decision_engine
)
from app.agents.document_planner import DocumentPlanner
from app.agents.document_writer import DocumentWriter
from app.agents.document_reviewer import DocumentReviewer
from app.services.document_service import DocumentService
from app.services.websocket_service import WebSocketManager
from app.telemetry import trace_function, trace_agent, telemetry

logger = logging.getLogger(__name__)


class DocumentOrchestrator:
    """Main orchestrator that manages the document creation process"""
    
    def __init__(self, document_id: int, config: Optional[AgentConfig] = None, document_service: Optional[DocumentService] = None, websocket_manager: Optional[WebSocketManager] = None):
        self.document_id = document_id
        self.config = config or agent_config_manager.get_config(document_id)
        self.llm_router = LLMRouter(self.config)
        self.document_service = document_service
        self.websocket_manager = websocket_manager
        
        # Initialize specialized agents
        self.planner = DocumentPlanner(self.llm_router, self.config)
        self.writer = DocumentWriter(self.llm_router, self.config, document_service, websocket_manager)
        self.reviewer = DocumentReviewer(self.llm_router, self.config)
        
        # State management
        self.current_plan: Optional[DocumentPlan] = None
        self.context: Optional[AgentContext] = None
        
        # Performance tracking
        self.start_time: Optional[datetime] = None
        self.operation_count = 0
        
        # Process tracking for frontend visibility
        self.process_activities: List[Dict[str, Any]] = []
        self.activity_callbacks: List[callable] = []
    
    def add_activity_callback(self, callback: callable):
        """Add a callback to be notified of agent activities"""
        self.activity_callbacks.append(callback)
    
    async def _emit_activity(self, agent: str, action: str, status: str, 
                           input_data: str = None, output_data: str = None, 
                           error: str = None, metadata: Dict[str, Any] = None):
        """Emit an agent activity for frontend tracking"""
        
        activity = {
            "agent": agent,
            "action": action,
            "status": status,
            "startTime": datetime.utcnow().isoformat(),
            "input": input_data,
            "output": output_data,
            "error": error,
            "metadata": metadata or {}
        }
        
        if status in ['completed', 'error']:
            activity["endTime"] = datetime.utcnow().isoformat()
        
        self.process_activities.append(activity)
        
        # Notify callbacks
        for callback in self.activity_callbacks:
            try:
                await callback(activity)
            except Exception as e:
                logger.error(f"Error in activity callback: {e}")
    
    async def _update_activity_status(self, agent: str, action: str, status: str, 
                                    output_data: str = None, error: str = None):
        """Update the status of an existing activity"""
        
        for activity in reversed(self.process_activities):
            if activity["agent"] == agent and activity["action"] == action:
                activity["status"] = status
                if status in ['completed', 'error']:
                    activity["endTime"] = datetime.utcnow().isoformat()
                if output_data:
                    activity["output"] = output_data
                if error:
                    activity["error"] = error
                
                # Notify callbacks of update
                for callback in self.activity_callbacks:
                    try:
                        await callback(activity)
                    except Exception as e:
                        logger.error(f"Error in activity callback: {e}")
                break
    
    @trace_agent("orchestrator", "process_user_request")
    async def process_user_request(self, 
                                 user_message: str, 
                                 conversation_id: Optional[int] = None,
                                 conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a user request and coordinate agent activities"""
        
        try:
            self.start_time = datetime.utcnow()
            self.operation_count += 1
            
            logger.info(f"=== Starting Document Orchestrator Process ===")
            logger.info(f"User Message: {user_message}")
            logger.info(f"Document ID: {self.document_id}")
            logger.info(f"Conversation ID: {conversation_id}")
            logger.info(f"Operation Count: {self.operation_count}")
            
            # Create context for this operation
            self.context = AgentContext(
                document_id=self.document_id,
                conversation_id=conversation_id,
                user_message=user_message,
                conversation_history=conversation_history or [],
                metadata={"operation_id": self.operation_count}
            )
            
            # Transition to analyzing state
            agent_state_manager.transition_to(
                AgentState.ANALYZING, 
                AgentType.ORCHESTRATOR.value,
                "Starting analysis of user request"
            )
            
            # Step 1: Analyze the user request
            await self._emit_activity("orchestrator", "Analyzing user request", "in_progress", 
                                    input_data=user_message)
            analysis = await self._analyze_request()
            logger.info(f"User request analysis: {analysis}")
            await self._update_activity_status("orchestrator", "Analyzing user request", "completed",
                                             output_data=f"Intent: {analysis.get('intent', 'unknown')}")
            
            # Step 2: Create or update plan based on analysis
            plan_updated = await self._handle_planning(analysis)
            
            # Log agent handoff
            if plan_updated:
                await self._emit_activity("orchestrator", "Plan created, handing off to writer", "completed",
                                        output_data="Plan ready for content generation")
            
            # Step 3: Execute the plan
            execution_result = await self._execute_plan(analysis)
            
            # Step 4: Determine if preview should be updated
            should_update = await self._determine_preview_update(execution_result)
            
            # Log agent coordination decision
            if should_update:
                await self._emit_activity("orchestrator", "Coordinating preview update", "completed",
                                        output_data="Preview update scheduled")
            
            # Step 5: Generate final response
            await self._emit_activity("orchestrator", "Generating final response", "in_progress",
                                    input_data="Compiling agent results into user response")
            final_response = await self._generate_final_response(
                analysis, execution_result, should_update
            )
            await self._update_activity_status("orchestrator", "Generating final response", "completed",
                                             output_data=f"Response ready: {len(final_response.split())} words")
            
            # Return to idle state
            agent_state_manager.transition_to(
                AgentState.IDLE, 
                AgentType.ORCHESTRATOR.value,
                "Request processing complete"
            )
            
            return {
                "success": True,
                "response": final_response,
                "plan_updated": plan_updated,
                "preview_ready": should_update,
                "messages": agent_state_manager.get_messages(),
                "processing_time": (datetime.utcnow() - self.start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"=== ERROR in Document Orchestrator ===", exc_info=True)
            logger.error(f"Error processing user request: {e}")
            logger.error(f"User message was: {user_message}")
            logger.error(f"Document ID: {self.document_id}")
            
            agent_state_manager.transition_to(
                AgentState.ERROR, 
                AgentType.ORCHESTRATOR.value,
                f"Error: {str(e)}"
            )
            
            # Emit error activity for frontend
            await self._emit_activity("orchestrator", "Processing failed", "error",
                                    error=str(e))
            
            return {
                "success": False,
                "error": str(e),
                "messages": agent_state_manager.get_messages()
            }
    
    @trace_agent("orchestrator", "analyze_request")
    async def _analyze_request(self) -> Dict[str, Any]:
        """Analyze user request to determine intent and actions needed"""
        
        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt()
        
        # Use orchestrator LLM for analysis
        analysis_response = await self.llm_router.route_request(
            AgentType.ORCHESTRATOR,
            analysis_prompt
        )
        
        try:
            # Parse JSON response - try JSON first, then eval as fallback
            try:
                analysis = json.loads(analysis_response)
            except json.JSONDecodeError:
                analysis = eval(analysis_response)  # Fallback to eval
            
            # Add metadata
            analysis["analyzed_at"] = datetime.utcnow().isoformat()
            analysis["orchestrator_model"] = self.config.get_llm_for_agent(AgentType.ORCHESTRATOR)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error parsing analysis: {e}")
            # Fallback to improved analysis with better document creation detection
            user_message = self.context.user_message.lower().strip()
            
            # Check for simple greetings and conversations
            simple_phrases = ['hi', 'hello', 'hey', 'thanks', 'thank you', 'how are you', 'good morning', 'good afternoon']
            is_simple_greeting = (
                len(user_message.split()) <= 3 and  # Short messages
                any(phrase in user_message for phrase in simple_phrases)
            )
            
            # Check for document creation keywords
            document_creation_keywords = [
                'write', 'create', 'draft', 'generate', 'make', 'compose', 'develop',
                'structure', 'template', 'outline', 'proposal', 'report', 'document',
                'content', 'text', 'letter', 'email', 'plan', 'strategy', 'summary'
            ]
            
            requires_document_creation = any(keyword in user_message for keyword in document_creation_keywords)
            
            # Check if it's a simple template request (should not require planning)
            template_keywords = ['template', 'structure', 'outline', 'format', 'example']
            is_template_request = any(keyword in user_message for keyword in template_keywords)
            
            # Check for question patterns that don't require document creation
            question_patterns = [
                'what', 'how', 'why', 'when', 'where', 'who', 'explain', 'tell me',
                'can you help', 'how does', 'what is', 'what are'
            ]
            
            is_question_only = (
                any(pattern in user_message for pattern in question_patterns) and
                not requires_document_creation
            )
            
            if is_simple_greeting:
                return {
                    "intent": "conversation",
                    "action_needed": "respond",
                    "confidence": 0.8,
                    "requires_planning": False,
                    "requires_writing": False,
                    "requires_review": False
                }
            elif requires_document_creation:
                return {
                    "intent": "create_document",
                    "action_needed": "write",
                    "confidence": 0.7,
                    "requires_planning": False,  # Templates and simple documents don't need planning
                    "requires_writing": True,
                    "requires_review": True  # Enable review for document creation
                }
            elif is_question_only:
                return {
                    "intent": "ask_question",
                    "action_needed": "respond",
                    "confidence": 0.6,
                    "requires_planning": False,
                    "requires_writing": False,
                    "requires_review": False
                }
            else:
                return {
                    "intent": "general_assistance",
                    "action_needed": "respond",
                    "confidence": 0.5,
                    "requires_planning": False,
                    "requires_writing": True,  # Default to writing for ambiguous cases
                    "requires_review": True  # Enable review for content generation
                }
    
    def _build_analysis_prompt(self) -> List[Dict[str, str]]:
        """Build prompt for request analysis"""
        
        system_prompt = """
        You are an intelligent document assistant orchestrator. Analyze the user's request and determine:
        1. Intent (create_document, modify_content, ask_question, conversation, etc.)
        2. Action needed (plan, write, review, respond, etc.)
        3. Confidence level (0.0-1.0)
        4. Whether planning is required
        5. Whether writing is required
        6. Whether review is required
        
        IMPORTANT: Requests that ask to "write", "create", "draft", "generate", or "make" any kind of document, 
        content, structure, template, or text should have requires_writing: true.
        
        For simple content requests, set requires_planning: false. Only set requires_planning: true for 
        complex multi-section documents that need detailed structure.
        
        IMPORTANT: Template and structure requests should NOT require planning - they should be simple, 
        direct content generation.
        
        For REVIEW decisions:
        - Set requires_review: true for ANY content creation, document generation, or writing tasks
        - Set requires_review: false only for simple greetings, questions, or conversations without content creation
        - Review helps ensure quality and completeness of generated content
        
        Examples that require writing (but NOT planning) WITH review:
        - "write a proposal structure" → requires_writing: true, requires_review: true
        - "create a business plan template" → requires_writing: true, requires_review: true
        - "create a template" → requires_writing: true, requires_review: true
        - "draft an email" → requires_writing: true, requires_review: true
        - "generate a brief report" → requires_writing: true, requires_review: true
        - "make a simple document" → requires_writing: true, requires_review: true
        - "write a template for..." → requires_writing: true, requires_review: true
        
        Examples that require both writing and planning WITH review:
        - "create a comprehensive 50-page business plan" → requires_planning: true, requires_writing: true, requires_review: true
        - "write a detailed research report with analysis" → requires_planning: true, requires_writing: true, requires_review: true
        - "develop a multi-section strategy document with research" → requires_planning: true, requires_writing: true, requires_review: true
        
        Examples that do NOT require writing (just conversation):
        - "hi", "hello", "thanks"
        - "how are you?"
        - "what can you do?"
        - "explain how this works"
        
        Respond with a JSON object containing these fields:
        {
            "intent": "create_document|modify_content|ask_question|conversation|general_assistance",
            "action_needed": "plan|write|review|respond",
            "confidence": 0.0-1.0,
            "requires_planning": true|false,
            "requires_writing": true|false,
            "requires_review": true|false
        }
        """
        
        context_info = f"""
        Document ID: {self.document_id}
        Current plan exists: {self.current_plan is not None}
        Conversation history length: {len(self.context.conversation_history) if self.context else 0}
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context_info}"},
            {"role": "user", "content": f"User request: {self.context.user_message}"}
        ]
    
    async def _handle_planning(self, analysis: Dict[str, Any]) -> bool:
        """Handle planning based on analysis"""
        
        if not analysis.get("requires_planning", False):
            return False
        
        agent_state_manager.transition_to(
            AgentState.PLANNING,
            AgentType.PLANNER.value,
            "Creating document plan"
        )
        
        await self._emit_activity("planner", "Creating document plan", "in_progress",
                                input_data=self.context.user_message)
        
        if self.current_plan:
            # Update existing plan
            self.current_plan = await self.planner.update_plan(
                self.current_plan,
                self.context.user_message,
                analysis
            )
        else:
            # Create new plan
            self.current_plan = await self.planner.create_plan(
                self.context.user_message,
                analysis
            )
        
        # Update context with plan
        self.context.plan = self.current_plan
        
        # Track completion
        await self._update_activity_status("planner", "Creating document plan", "completed",
                                         output_data=f"Plan with {len(self.current_plan.sections)} sections")
        
        # Send plan message
        plan_message = AgentMessage(
            agent_type=AgentType.PLANNER.value,
            message_type="plan_created",
            content=f"Created plan with {len(self.current_plan.sections)} sections",
            metadata=self.current_plan.to_dict()
        )
        agent_state_manager.add_message(plan_message)
        
        return True
    
    async def _execute_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the planned actions"""
        
        result = {
            "content_generated": False,
            "content_reviewed": False,
            "changes_made": 0
        }
        
        # Check if this is a simple conversation that doesn't require document operations
        is_simple_conversation = (
            not analysis.get("requires_planning", False) and
            not analysis.get("requires_writing", False) and
            not analysis.get("requires_review", False)
        )
        
        if is_simple_conversation:
            await self._emit_activity("orchestrator", "Preparing conversational response", "in_progress",
                                    input_data=f"Intent: {analysis.get('intent', 'conversation')}")
            # Add a small delay to show realistic timing
            import asyncio
            await asyncio.sleep(0.1)
            await self._update_activity_status("orchestrator", "Preparing conversational response", "completed",
                                             output_data="Ready to generate response")
        
        # Writing phase
        if analysis.get("requires_writing", False):
            logger.info(f"Document writing triggered for: {self.context.user_message}")
            agent_state_manager.transition_to(
                AgentState.WRITING,
                AgentType.WRITER.value,
                "Generating content"
            )
            
            await self._emit_activity("writer", "Generating document content", "in_progress",
                                    input_data=self.context.user_message)
            
            # Send streaming start notification
            if self.websocket_manager and self.document_id:
                await self._send_streaming_start_notification()
            
            writing_result = await self.writer.write_content(
                self.context,
                self.current_plan
            )
            logger.info(f"Writing result: {writing_result}")
            
            if writing_result.get("success", False):
                await self._update_activity_status("writer", "Generating document content", "completed",
                                                 output_data=f"{writing_result.get('words_written', 0)} words written")
                
                # Add document saving activity if content was written to document
                if writing_result.get("document_updated", False):
                    await self._emit_activity("orchestrator", "Saving content to document", "completed",
                                            output_data=f"Document updated with {writing_result.get('words_written', 0)} words")
            else:
                await self._update_activity_status("writer", "Generating document content", "error",
                                                 error=writing_result.get('error', 'Writing failed'))
            
            result["content_generated"] = True
            result["changes_made"] = writing_result.get("changes_made", 0)
            
            # Log agent handoff to reviewer if review is needed
            if analysis.get("requires_review", False):
                await self._emit_activity("orchestrator", "Writer completed, sending to reviewer", "completed",
                                        output_data=f"Content ready for review: {writing_result.get('words_written', 0)} words")
            
            # Send progress message
            progress_message = AgentMessage(
                agent_type=AgentType.WRITER.value,
                message_type="content_generated",
                content=f"Generated {writing_result.get('words_written', 0)} words",
                metadata=writing_result
            )
            agent_state_manager.add_message(progress_message)
        
        # Review phase
        if analysis.get("requires_review", False):
            agent_state_manager.transition_to(
                AgentState.REVIEWING,
                AgentType.REVIEWER.value,
                "Reviewing content"
            )
            
            await self._emit_activity("reviewer", "Reviewing content quality", "in_progress")
            
            review_result = await self.reviewer.review_content(
                self.context,
                self.current_plan
            )
            
            if review_result.get("success", False):
                await self._update_activity_status("reviewer", "Reviewing content quality", "completed",
                                                 output_data=f"Review score: {review_result.get('score', 0)}/10")
            else:
                await self._update_activity_status("reviewer", "Reviewing content quality", "error",
                                                 error=review_result.get('error', 'Review failed'))
            
            result["content_reviewed"] = True
            result["review_score"] = review_result.get("score", 0)
            
            # Log review completion and handoff back to orchestrator
            await self._emit_activity("orchestrator", "Review completed, finalizing response", "completed",
                                    output_data=f"Review score: {review_result.get('score', 0)}/10, ready for final response")
            
            # Send review message
            review_message = AgentMessage(
                agent_type=AgentType.REVIEWER.value,
                message_type="content_reviewed",
                content=f"Content review complete. Score: {review_result.get('score', 0)}/10",
                metadata=review_result
            )
            agent_state_manager.add_message(review_message)
        
        return result
    
    async def _determine_preview_update(self, execution_result: Dict[str, Any]) -> bool:
        """Determine if preview should be updated"""
        
        # Get current state information
        current_state = agent_state_manager.current_state
        last_action = AgentAction.WRITE_CONTENT if execution_result.get("content_generated") else AgentAction.ANALYZE_REQUEST
        
        # Calculate time since last update
        time_since_last_update = 0
        if preview_decision_engine.last_update_time:
            time_since_last_update = (datetime.utcnow() - preview_decision_engine.last_update_time).total_seconds()
        
        # Check if update is needed
        should_update = preview_decision_engine.should_update_preview(
            current_state=current_state,
            last_action=last_action,
            time_since_last_update=time_since_last_update,
            content_changes=execution_result.get("changes_made", 0),
            user_requested=False  # TODO: Detect user preview requests
        )
        
        if should_update:
            agent_state_manager.transition_to(
                AgentState.UPDATING_PREVIEW,
                AgentType.ORCHESTRATOR.value,
                "Updating document preview"
            )
            
            # Record the update
            preview_decision_engine.record_update()
            
            # Send update message
            update_message = AgentMessage(
                agent_type=AgentType.ORCHESTRATOR.value,
                message_type="preview_updated",
                content="Document preview has been updated",
                metadata={"update_reason": "content_changes"}
            )
            agent_state_manager.add_message(update_message)
        
        return should_update
    
    async def _generate_final_response(self, 
                                     analysis: Dict[str, Any],
                                     execution_result: Dict[str, Any],
                                     preview_updated: bool) -> str:
        """Generate final response to user"""
        
        # Build response context
        response_context = {
            "analysis": analysis,
            "execution_result": execution_result,
            "preview_updated": preview_updated,
            "plan_exists": self.current_plan is not None
        }
        
        # Generate response using orchestrator LLM
        response_prompt = self._build_response_prompt(response_context)
        
        response = await self.llm_router.route_request(
            AgentType.ORCHESTRATOR,
            response_prompt
        )
        
        return response
    
    async def _send_streaming_start_notification(self):
        """Send notification that streaming is starting"""
        try:
            if not self.websocket_manager:
                return
                
            from app.models.schemas import WebSocketMessage
            from datetime import datetime
            
            message = WebSocketMessage(
                type="document_streaming_start",
                data={
                    "document_id": self.document_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_request": self.context.user_message
                }
            )
            
            await self.websocket_manager.broadcast_to_document(self.document_id, message)
            
        except Exception as e:
            logger.error(f"Error sending streaming start notification: {e}")
    
    def _build_response_prompt(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build prompt for final response generation"""
        
        system_prompt = """
        You are a helpful document assistant. Generate a natural, conversational response to the user
        based on the work that has been completed. Be concise but informative.
        
        If document content was generated or updated, mention this in your response with relevant details
        like word count, sections created, or content saved to the document.
        """
        
        # Include document update information if available
        document_info = ""
        if context['execution_result'].get('document_updated', False):
            words_written = context['execution_result'].get('words_written', 0)
            sections_completed = context['execution_result'].get('sections_completed', 0)
            document_info = f"Document updated: {words_written} words written"
            if sections_completed > 0:
                document_info += f", {sections_completed} sections completed"
        
        context_summary = f"""
        Intent: {context['analysis'].get('intent', 'unknown')}
        Content generated: {context['execution_result'].get('content_generated', False)}
        Content reviewed: {context['execution_result'].get('content_reviewed', False)}
        Preview updated: {context['preview_updated']}
        Plan exists: {context['plan_exists']}
        {document_info}
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context_summary}"},
            {"role": "user", "content": f"Original request: {self.context.user_message}"}
        ]
    
    async def stream_response(self, user_message: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream response with real-time process updates"""
        
        response_chunks = []
        
        # Setup activity callback to capture process events
        async def activity_callback(activity):
            # This will be called whenever an activity is emitted or updated
            # We can yield this data to the frontend
            pass
        
        self.add_activity_callback(activity_callback)
        
        try:
            result = await self.process_user_request(user_message, **kwargs)
            
            if result["success"]:
                response = result["response"]
                words = response.split()
                
                for word in words:
                    chunk = word + " "
                    response_chunks.append(chunk)
                    yield chunk
                    await asyncio.sleep(0.05)
            else:
                yield f"Error: {result['error']}"
                
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current orchestrator state"""
        return {
            "document_id": self.document_id,
            "agent_state": agent_state_manager.get_state_info(),
            "plan_exists": self.current_plan is not None,
            "plan_progress": self.current_plan.current_step if self.current_plan else 0,
            "config": self.config.to_dict(),
            "available_providers": self.llm_router.get_available_providers()
        }