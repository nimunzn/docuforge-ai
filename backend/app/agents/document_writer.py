"""
Document Writer Agent
Specialized agent for generating document content
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.agents.agent_config import AgentConfig, AgentType
from app.agents.llm_router import LLMRouter
from app.agents.agent_states import DocumentPlan, AgentContext, AgentMessage
from app.services.document_service import DocumentService
from app.services.websocket_service import WebSocketManager
from app.models.schemas import WebSocketMessage
from app.telemetry import trace_agent, telemetry

logger = logging.getLogger(__name__)


class DocumentWriter:
    """Agent responsible for writing document content"""
    
    def __init__(self, llm_router: LLMRouter, config: AgentConfig, document_service: Optional[DocumentService] = None, websocket_manager: Optional[WebSocketManager] = None):
        self.llm_router = llm_router
        self.config = config
        self.agent_type = AgentType.WRITER
        self.document_service = document_service
        self.websocket_manager = websocket_manager
    
    @trace_agent("writer", "write_content")
    async def write_content(self, 
                          context: AgentContext, 
                          plan: Optional[DocumentPlan] = None) -> Dict[str, Any]:
        """Write content based on context and plan"""
        
        try:
            logger.info(f"DocumentWriter.write_content called with user_message: {context.user_message}")
            logger.info(f"Document ID: {context.document_id}, Plan exists: {plan is not None}")
            logger.info(f"Document service available: {self.document_service is not None}")
            
            if plan:
                # Write based on plan
                result = await self._write_from_plan(context, plan)
            else:
                # Write based on user request directly
                result = await self._write_from_request(context)
            
            logger.info(f"Content generated: {len(result['content'])} characters")
            
            # Save content to document if document service is available
            if self.document_service and context.document_id:
                logger.info(f"Saving content to document {context.document_id}")
                await self._save_content_to_document(context.document_id, result["content"], plan)
                
                # Send streaming completion notification
                if self.websocket_manager:
                    await self._send_streaming_completion(context.document_id, result["content"])
            else:
                logger.warning(f"Not saving content - document_service: {self.document_service is not None}, document_id: {context.document_id}")
            
            return {
                "success": True,
                "content": result["content"],
                "words_written": result["words_written"],
                "changes_made": result["changes_made"],
                "sections_completed": result.get("sections_completed", 0),
                "document_updated": self.document_service is not None and context.document_id is not None
            }
            
        except Exception as e:
            logger.error(f"Error writing content: {e}", exc_info=True)
            logger.error(f"Context: user_message='{context.user_message}', document_id={context.document_id}")
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "words_written": 0,
                "changes_made": 0,
                "document_updated": False
            }
    
    async def _write_from_plan(self, context: AgentContext, plan: DocumentPlan) -> Dict[str, Any]:
        """Write content following a structured plan"""
        
        total_content = ""
        total_words = 0
        sections_completed = 0
        
        # Process each section in the plan
        for i, section in enumerate(plan.sections):
            if i < plan.current_step:
                continue  # Skip already completed sections
            
            # Write section content
            section_content = await self._write_section(context, section, plan)
            
            total_content += section_content
            section_words = len(section_content.split())
            total_words += section_words
            
            sections_completed += 1
            
            # Update plan progress
            plan.current_step = i + 1
            
            logger.info(f"Completed section '{section['title']}' with {section_words} words")
        
        return {
            "content": total_content,
            "words_written": total_words,
            "changes_made": sections_completed,
            "sections_completed": sections_completed
        }
    
    async def _write_from_request(self, context: AgentContext) -> Dict[str, Any]:
        """Write content directly from user request with streaming"""
        
        # Build writing prompt
        writing_prompt = self._build_direct_writing_prompt(context)
        
        # Stream content generation
        content = ""
        async for chunk in self.llm_router.stream_route_request(
            self.agent_type,
            writing_prompt
        ):
            content += chunk
            
            # Send streaming update via WebSocket
            if self.websocket_manager and context.document_id:
                await self._send_streaming_update(
                    context.document_id,
                    chunk,
                    content,
                    section_name="Document Content"
                )
        
        word_count = len(content.split())
        
        return {
            "content": content,
            "words_written": word_count,
            "changes_made": 1
        }
    
    async def _write_section(self, 
                           context: AgentContext, 
                           section: Dict[str, Any], 
                           plan: DocumentPlan) -> str:
        """Write content for a specific section with streaming"""
        
        # Build section writing prompt
        section_prompt = self._build_section_writing_prompt(context, section, plan)
        
        # Stream section content generation
        section_content = ""
        section_title = section.get('title', 'Section')
        
        # First, send the section header
        section_header = f"\n## {section_title}\n\n"
        if self.websocket_manager and context.document_id:
            await self._send_streaming_update(
                context.document_id,
                section_header,
                section_header,
                section_name=section_title,
                is_header=True
            )
        
        # Stream the section content
        async for chunk in self.llm_router.stream_route_request(
            self.agent_type,
            section_prompt
        ):
            section_content += chunk
            
            # Send streaming update via WebSocket
            if self.websocket_manager and context.document_id:
                await self._send_streaming_update(
                    context.document_id,
                    chunk,
                    section_content,
                    section_name=section_title
                )
        
        # Add section formatting
        formatted_content = self._format_section_content(section, section_content)
        
        return formatted_content
    
    def _build_direct_writing_prompt(self, context: AgentContext) -> List[Dict[str, str]]:
        """Build prompt for direct content writing"""
        
        system_prompt = """
        You are a skilled content writer. Create high-quality, engaging content based on the user's request.
        
        Guidelines:
        - Write in a clear, professional tone
        - Structure content with appropriate headings using markdown
        - Use proper grammar and formatting
        - Make content informative and valuable
        - Adapt style to the content type
        
        IMPORTANT: For template requests, create concise, well-structured templates that users can fill in.
        Templates should include:
        - Clear section headings
        - Brief explanations of what goes in each section
        - Placeholder text in [brackets] where users should add their content
        - Professional formatting with markdown
        
        Focus on quality and relevance. Keep templates practical and usable.
        """
        
        conversation_context = ""
        if context.conversation_history:
            recent_messages = context.conversation_history[-3:]  # Last 3 messages
            conversation_context = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in recent_messages
            ])
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Recent conversation: {conversation_context}"},
            {"role": "user", "content": f"Write content for: {context.user_message}"}
        ]
    
    def _build_section_writing_prompt(self, 
                                    context: AgentContext, 
                                    section: Dict[str, Any], 
                                    plan: DocumentPlan) -> List[Dict[str, str]]:
        """Build prompt for section writing"""
        
        system_prompt = f"""
        You are writing a section for a {plan.document_type} titled "{plan.title}".
        
        Section Details:
        - Title: {section['title']}
        - Description: {section.get('description', 'No description')}
        - Target Words: {section.get('estimated_words', 200)}
        - Priority: {section.get('priority', 'medium')}
        
        Write engaging, well-structured content that:
        - Fits the document type and overall theme
        - Meets the target word count approximately
        - Flows well with the document structure
        - Is appropriate for the intended audience
        
        Focus on quality and coherence.
        """
        
        document_context = f"""
        Document Type: {plan.document_type}
        Document Title: {plan.title}
        Section {plan.current_step + 1} of {plan.total_steps}
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Document Context: {document_context}"},
            {"role": "user", "content": f"User Request: {context.user_message}"}
        ]
    
    def _format_section_content(self, section: Dict[str, Any], content: str) -> str:
        """Format section content with proper headings"""
        
        section_title = section.get('title', 'Section')
        
        # Add section heading
        formatted_content = f"\n## {section_title}\n\n"
        
        # Add content
        formatted_content += content.strip()
        
        # Add spacing
        formatted_content += "\n\n"
        
        return formatted_content
    
    async def expand_content(self, 
                           existing_content: str, 
                           expansion_request: str,
                           context: AgentContext) -> Dict[str, Any]:
        """Expand existing content based on request"""
        
        try:
            # Build expansion prompt
            expansion_prompt = self._build_expansion_prompt(
                existing_content, 
                expansion_request, 
                context
            )
            
            # Generate expanded content
            expanded_content = await self.llm_router.route_request(
                self.agent_type,
                expansion_prompt
            )
            
            # Calculate metrics
            original_words = len(existing_content.split())
            expanded_words = len(expanded_content.split())
            new_words = expanded_words - original_words
            
            return {
                "success": True,
                "expanded_content": expanded_content,
                "original_words": original_words,
                "new_words": new_words,
                "total_words": expanded_words
            }
            
        except Exception as e:
            logger.error(f"Error expanding content: {e}")
            return {
                "success": False,
                "error": str(e),
                "expanded_content": existing_content,
                "new_words": 0
            }
    
    def _build_expansion_prompt(self, 
                              existing_content: str, 
                              expansion_request: str,
                              context: AgentContext) -> List[Dict[str, str]]:
        """Build prompt for content expansion"""
        
        system_prompt = """
        You are expanding existing content. Add relevant information while maintaining:
        - Consistency with existing tone and style
        - Logical flow and organization
        - Quality and accuracy
        - Appropriate depth and detail
        
        Integrate new content seamlessly with existing material.
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Existing content: {existing_content}"},
            {"role": "user", "content": f"Expansion request: {expansion_request}"}
        ]
    
    async def rewrite_content(self, 
                            existing_content: str, 
                            rewrite_request: str,
                            context: AgentContext) -> Dict[str, Any]:
        """Rewrite content based on request"""
        
        try:
            # Build rewrite prompt
            rewrite_prompt = self._build_rewrite_prompt(
                existing_content, 
                rewrite_request, 
                context
            )
            
            # Generate rewritten content
            rewritten_content = await self.llm_router.route_request(
                self.agent_type,
                rewrite_prompt
            )
            
            # Calculate metrics
            original_words = len(existing_content.split())
            rewritten_words = len(rewritten_content.split())
            
            return {
                "success": True,
                "rewritten_content": rewritten_content,
                "original_words": original_words,
                "rewritten_words": rewritten_words,
                "change_percentage": abs(rewritten_words - original_words) / original_words * 100
            }
            
        except Exception as e:
            logger.error(f"Error rewriting content: {e}")
            return {
                "success": False,
                "error": str(e),
                "rewritten_content": existing_content,
                "change_percentage": 0
            }
    
    def _build_rewrite_prompt(self, 
                            existing_content: str, 
                            rewrite_request: str,
                            context: AgentContext) -> List[Dict[str, str]]:
        """Build prompt for content rewriting"""
        
        system_prompt = """
        You are rewriting content based on specific requirements. Consider:
        - The requested changes or improvements
        - Maintaining core message and value
        - Improving clarity, flow, or style
        - Meeting any specific requirements
        
        Provide a complete rewrite that addresses the request.
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Content to rewrite: {existing_content}"},
            {"role": "user", "content": f"Rewrite request: {rewrite_request}"}
        ]
    
    async def generate_variations(self, 
                                content: str, 
                                num_variations: int = 3) -> List[str]:
        """Generate multiple variations of content"""
        
        variations = []
        
        for i in range(num_variations):
            try:
                variation_prompt = self._build_variation_prompt(content, i)
                
                variation = await self.llm_router.route_request(
                    self.agent_type,
                    variation_prompt
                )
                
                variations.append(variation)
                
            except Exception as e:
                logger.error(f"Error generating variation {i}: {e}")
                variations.append(content)  # Fallback to original
        
        return variations
    
    def _build_variation_prompt(self, content: str, variation_index: int) -> List[Dict[str, str]]:
        """Build prompt for content variation"""
        
        style_hints = [
            "more concise and direct",
            "more detailed and explanatory",
            "more engaging and conversational"
        ]
        
        style_hint = style_hints[variation_index % len(style_hints)]
        
        system_prompt = f"""
        Create a variation of the given content that is {style_hint}.
        Maintain the core message and key information while adjusting the presentation.
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Content to vary: {content}"}
        ]
    
    async def _save_content_to_document(self, document_id: int, content: str, plan: Optional[DocumentPlan] = None):
        """Save generated content to document database"""
        try:
            if not self.document_service:
                logger.warning("Document service not available, cannot save content")
                return
            
            # Structure the content for document storage
            structured_content = self._structure_content(content, plan)
            
            # Create update data
            from app.models.schemas import DocumentUpdate
            update_data = DocumentUpdate(
                content=structured_content,
                status="draft",
                updated_at=datetime.utcnow()
            )
            
            # Update the document
            updated_document = await self.document_service.update_document(document_id, update_data)
            
            if updated_document:
                logger.info(f"Successfully saved content to document {document_id}")
                
                # Send WebSocket notification for real-time preview update
                if self.websocket_manager:
                    await self._send_document_update_notification(document_id, updated_document, structured_content)
            else:
                logger.error(f"Failed to save content to document {document_id}")
                
        except Exception as e:
            logger.error(f"Error saving content to document {document_id}: {e}")
    
    def _structure_content(self, content: str, plan: Optional[DocumentPlan] = None) -> Dict[str, Any]:
        """Structure raw content into organized document format"""
        try:
            # If we have a plan, try to organize content by sections
            if plan and plan.sections:
                return self._structure_content_with_plan(content, plan)
            else:
                return self._structure_content_simple(content)
                
        except Exception as e:
            logger.error(f"Error structuring content: {e}")
            return self._structure_content_simple(content)
    
    def _structure_content_with_plan(self, content: str, plan: DocumentPlan) -> Dict[str, Any]:
        """Structure content based on document plan"""
        sections = []
        
        # Split content into sections based on markdown headers
        content_parts = content.split('\n##')
        
        for i, part in enumerate(content_parts):
            if i == 0:
                # First part might not have ## prefix
                if part.strip():
                    sections.append({
                        "id": f"section_{i}",
                        "title": "Introduction",
                        "content": part.strip(),
                        "order": i
                    })
            else:
                # Extract title and content
                lines = part.strip().split('\n', 1)
                title = lines[0].strip()
                section_content = lines[1].strip() if len(lines) > 1 else ""
                
                sections.append({
                    "id": f"section_{i}",
                    "title": title,
                    "content": section_content,
                    "order": i
                })
        
        return {
            "type": plan.document_type,
            "title": plan.title,
            "sections": sections,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "plan_id": id(plan),
                "total_sections": len(sections)
            }
        }
    
    def _structure_content_simple(self, content: str) -> Dict[str, Any]:
        """Structure content without a plan"""
        return {
            "type": "document",
            "title": "Generated Document",
            "sections": [
                {
                    "id": "section_0",
                    "title": "Content",
                    "content": content,
                    "order": 0
                }
            ],
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_sections": 1
            }
        }
    
    async def _send_document_update_notification(self, document_id: int, updated_document: Any, structured_content: Dict[str, Any]):
        """Send WebSocket notification about document update"""
        try:
            message = WebSocketMessage(
                type="document_updated",
                data={
                    "document": {
                        "id": document_id,
                        "title": updated_document.title,
                        "content": updated_document.content,
                        "updated_at": updated_document.updated_at.isoformat(),
                        "status": updated_document.status,
                        "type": updated_document.type,
                        "created_at": updated_document.created_at.isoformat()
                    },
                    "sections_count": len(structured_content.get("sections", [])),
                    "word_count": self._calculate_word_count(structured_content)
                }
            )
            
            await self.websocket_manager.broadcast_to_document(document_id, message)
            logger.info(f"Sent document update notification for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error sending document update notification: {e}")
    
    def _calculate_word_count(self, structured_content: Dict[str, Any]) -> int:
        """Calculate word count from structured content"""
        try:
            total_words = 0
            sections = structured_content.get("sections", [])
            
            for section in sections:
                content = section.get("content", "")
                if content:
                    total_words += len(content.split())
            
            return total_words
        except Exception as e:
            logger.error(f"Error calculating word count: {e}")
            return 0
    
    async def _send_streaming_update(self, document_id: int, chunk: str, full_content: str, section_name: str = "Document", is_header: bool = False):
        """Send real-time streaming update via WebSocket"""
        try:
            if not self.websocket_manager:
                return
                
            from app.models.schemas import WebSocketMessage
            
            message = WebSocketMessage(
                type="document_content_streaming",
                data={
                    "document_id": document_id,
                    "chunk": chunk,
                    "full_content": full_content,
                    "section_name": section_name,
                    "is_header": is_header,
                    "timestamp": datetime.utcnow().isoformat(),
                    "word_count": len(full_content.split())
                }
            )
            
            await self.websocket_manager.broadcast_to_document(document_id, message)
            
        except Exception as e:
            logger.error(f"Error sending streaming update: {e}")
    
    async def _send_streaming_completion(self, document_id: int, final_content: str):
        """Send notification that streaming is complete"""
        try:
            if not self.websocket_manager:
                return
                
            from app.models.schemas import WebSocketMessage
            
            message = WebSocketMessage(
                type="document_content_complete",
                data={
                    "document_id": document_id,
                    "final_content": final_content,
                    "timestamp": datetime.utcnow().isoformat(),
                    "word_count": len(final_content.split())
                }
            )
            
            await self.websocket_manager.broadcast_to_document(document_id, message)
            
        except Exception as e:
            logger.error(f"Error sending streaming completion: {e}")