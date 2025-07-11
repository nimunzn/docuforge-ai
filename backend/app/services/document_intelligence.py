from typing import Dict, Any, List, Optional, Tuple
from app.services.ai_service_direct import AIService
from app.services.prompt_service import PromptService, DocumentType
from app.services.conversation_service import ConversationService
from app.models.document import Document
from sqlalchemy.orm import Session
import json
import re
from datetime import datetime


class DocumentIntelligenceService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
        self.prompt_service = PromptService()
        self.conversation_service = ConversationService(db)

    async def analyze_user_intent(self, user_input: str, document_id: Optional[int] = None) -> Dict[str, Any]:
        """Analyze user input to determine intent and extract parameters"""
        try:
            prompt = self.prompt_service.get_intent_detection_prompt(user_input)
            response = await self.ai_service.generate_response(prompt)
            
            # Parse JSON response
            intent_data = json.loads(response)
            
            # Add document context if available
            if document_id:
                document = self.db.query(Document).filter(Document.id == document_id).first()
                if document:
                    intent_data["document_context"] = {
                        "id": document.id,
                        "title": document.title,
                        "type": document.type,
                        "has_content": bool(document.content)
                    }
            
            return intent_data
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback to rule-based intent detection
            return self._fallback_intent_detection(user_input)

    def _fallback_intent_detection(self, user_input: str) -> Dict[str, Any]:
        """Fallback rule-based intent detection"""
        user_input_lower = user_input.lower()
        
        # Intent patterns
        patterns = {
            "create_document": [
                r"create.*document", r"write.*document", r"generate.*document",
                r"make.*document", r"new.*document", r"start.*document"
            ],
            "modify_content": [
                r"change.*content", r"modify.*section", r"update.*content",
                r"edit.*section", r"revise.*content", r"improve.*section"
            ],
            "change_style": [
                r"change.*style", r"make.*formal", r"make.*casual",
                r"adjust.*tone", r"more.*professional", r"less.*formal"
            ],
            "add_section": [
                r"add.*section", r"include.*section", r"insert.*section",
                r"create.*section", r"new.*section"
            ],
            "generate_image": [
                r"add.*image", r"create.*image", r"generate.*image",
                r"include.*picture", r"insert.*image"
            ],
            "export_document": [
                r"export.*document", r"download.*document", r"save.*document",
                r"convert.*pdf", r"export.*pdf", r"generate.*pdf"
            ]
        }
        
        detected_intent = "ask_question"  # default
        confidence = 0.5
        
        for intent, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, user_input_lower):
                    detected_intent = intent
                    confidence = 0.8
                    break
            if detected_intent != "ask_question":
                break
        
        # Detect document type
        document_type = None
        type_patterns = {
            "proposal": [r"proposal", r"business.*plan"],
            "report": [r"report", r"analysis"],
            "presentation": [r"presentation", r"slides", r"powerpoint"],
            "memo": [r"memo", r"memorandum"],
            "letter": [r"letter", r"correspondence"],
            "resume": [r"resume", r"cv", r"curriculum.*vitae"],
            "whitepaper": [r"whitepaper", r"white.*paper"],
            "manual": [r"manual", r"guide", r"instructions"],
            "article": [r"article", r"blog.*post"],
            "creative": [r"story", r"creative", r"poem", r"script"]
        }
        
        for doc_type, pattern_list in type_patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, user_input_lower):
                    document_type = doc_type
                    break
            if document_type:
                break
        
        return {
            "intent": detected_intent,
            "document_type": document_type,
            "confidence": confidence,
            "parameters": self._extract_parameters(user_input),
            "clarification_needed": confidence < 0.7
        }

    def _extract_parameters(self, user_input: str) -> Dict[str, Any]:
        """Extract parameters from user input"""
        params = {}
        
        # Extract potential title
        title_patterns = [
            r"titled?\s+['\"]([^'\"]+)['\"]",
            r"called?\s+['\"]([^'\"]+)['\"]",
            r"about\s+([A-Z][^.!?]*)"
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                params["title"] = match.group(1).strip()
                break
        
        # Extract length requirements
        length_patterns = [
            r"(\d+)\s*pages?",
            r"(\d+)\s*words?",
            r"(\d+)\s*slides?",
            r"short|brief|concise",
            r"long|detailed|comprehensive"
        ]
        
        for pattern in length_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                if match.group(0).lower() in ["short", "brief", "concise"]:
                    params["length"] = "short"
                elif match.group(0).lower() in ["long", "detailed", "comprehensive"]:
                    params["length"] = "long"
                else:
                    params["length"] = match.group(0)
                break
        
        # Extract tone/style
        tone_patterns = [
            r"formal|professional|business",
            r"casual|informal|friendly",
            r"technical|academic|scholarly",
            r"creative|engaging|persuasive"
        ]
        
        for pattern in tone_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                params["tone"] = match.group(0).lower()
                break
        
        return params

    async def generate_document_structure(
        self, 
        user_input: str, 
        document_type: DocumentType,
        provider: str = "openai"
    ) -> Dict[str, Any]:
        """Generate document structure based on user input"""
        try:
            prompt = self.prompt_service.get_document_creation_prompt(document_type, user_input)
            response = await self.ai_service.generate_response(prompt, provider=provider)
            
            # Parse JSON response
            structure = json.loads(response)
            
            # Validate structure
            if not all(key in structure for key in ["title", "sections"]):
                raise ValueError("Invalid document structure")
            
            # Add metadata
            structure["metadata"] = structure.get("metadata", {})
            structure["metadata"]["created_at"] = datetime.utcnow().isoformat()
            structure["metadata"]["document_type"] = document_type.value
            structure["metadata"]["generated_by"] = provider
            
            return structure
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback to basic structure
            return self._generate_fallback_structure(user_input, document_type)

    def _generate_fallback_structure(self, user_input: str, document_type: DocumentType) -> Dict[str, Any]:
        """Generate fallback document structure"""
        basic_structures = {
            DocumentType.PROPOSAL: {
                "title": "Business Proposal",
                "sections": [
                    {"title": "Executive Summary", "content": ""},
                    {"title": "Problem Statement", "content": ""},
                    {"title": "Proposed Solution", "content": ""},
                    {"title": "Timeline", "content": ""},
                    {"title": "Budget", "content": ""},
                    {"title": "Conclusion", "content": ""}
                ]
            },
            DocumentType.REPORT: {
                "title": "Report",
                "sections": [
                    {"title": "Executive Summary", "content": ""},
                    {"title": "Introduction", "content": ""},
                    {"title": "Methodology", "content": ""},
                    {"title": "Findings", "content": ""},
                    {"title": "Analysis", "content": ""},
                    {"title": "Recommendations", "content": ""}
                ]
            },
            DocumentType.PRESENTATION: {
                "title": "Presentation",
                "sections": [
                    {"title": "Title Slide", "content": ""},
                    {"title": "Agenda", "content": ""},
                    {"title": "Introduction", "content": ""},
                    {"title": "Main Content", "content": ""},
                    {"title": "Conclusion", "content": ""},
                    {"title": "Q&A", "content": ""}
                ]
            }
        }
        
        structure = basic_structures.get(document_type, {
            "title": "Document",
            "sections": [
                {"title": "Introduction", "content": ""},
                {"title": "Main Content", "content": ""},
                {"title": "Conclusion", "content": ""}
            ]
        })
        
        # Try to extract title from user input
        title_match = re.search(r"(?:about|on|for|titled?)\s+([A-Z][^.!?]*)", user_input, re.IGNORECASE)
        if title_match:
            structure["title"] = title_match.group(1).strip()
        
        structure["metadata"] = {
            "created_at": datetime.utcnow().isoformat(),
            "document_type": document_type.value,
            "generated_by": "fallback"
        }
        
        return structure

    async def expand_section_content(
        self, 
        section_title: str, 
        current_content: str,
        user_request: str,
        provider: str = "openai"
    ) -> str:
        """Expand or modify section content"""
        try:
            prompt = self.prompt_service.get_content_expansion_prompt(
                section_title, current_content, user_request
            )
            response = await self.ai_service.generate_response(prompt, provider=provider)
            return response.strip()
            
        except Exception as e:
            return f"Error expanding content: {str(e)}"

    async def adjust_document_style(
        self, 
        document_content: Dict[str, Any], 
        style_request: str,
        provider: str = "openai"
    ) -> Dict[str, Any]:
        """Adjust document style/tone"""
        try:
            prompt = self.prompt_service.get_style_adjustment_prompt(
                document_content, style_request
            )
            response = await self.ai_service.generate_response(prompt, provider=provider)
            
            # Parse JSON response
            adjusted_content = json.loads(response)
            return adjusted_content
            
        except (json.JSONDecodeError, Exception) as e:
            return document_content  # Return original if adjustment fails

    async def suggest_document_images(
        self, 
        document_content: Dict[str, Any], 
        section_title: str = None,
        provider: str = "openai"
    ) -> List[Dict[str, Any]]:
        """Suggest relevant images for document"""
        try:
            prompt = self.prompt_service.get_image_suggestion_prompt(
                document_content, section_title
            )
            response = await self.ai_service.generate_response(prompt, provider=provider)
            
            # Parse JSON response
            suggestions = json.loads(response)
            return suggestions if isinstance(suggestions, list) else []
            
        except (json.JSONDecodeError, Exception) as e:
            return []

    async def generate_document_summary(
        self, 
        document_content: Dict[str, Any],
        provider: str = "openai"
    ) -> str:
        """Generate document summary"""
        try:
            prompt = self.prompt_service.get_summary_prompt(document_content)
            response = await self.ai_service.generate_response(prompt, provider=provider)
            return response.strip()
            
        except Exception as e:
            return "Summary generation failed"

    async def process_conversational_request(
        self, 
        user_input: str, 
        document_id: int,
        conversation_id: Optional[int] = None,
        provider: str = "openai"
    ) -> Dict[str, Any]:
        """Process a conversational request with context"""
        
        # Get conversation context
        context_messages = []
        if conversation_id:
            context_messages = self.conversation_service.get_conversation_context(conversation_id)
        
        # Analyze intent
        intent_data = await self.analyze_user_intent(user_input, document_id)
        
        # Get document context
        document = self.db.query(Document).filter(Document.id == document_id).first()
        document_context = document.content if document else {}
        
        # Generate contextual prompt
        prompt = self.prompt_service.get_conversation_context_prompt(
            context_messages, user_input
        )
        
        # Add document context to system message
        if document_context:
            prompt[0]["content"] += f"\n\nCurrent Document Context: {json.dumps(document_context)}"
        
        # Generate response
        response = await self.ai_service.generate_response(prompt, provider=provider)
        
        return {
            "intent": intent_data,
            "response": response,
            "document_context": document_context,
            "conversation_context": len(context_messages)
        }