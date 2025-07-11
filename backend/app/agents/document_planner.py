"""
Document Planner Agent
Specialized agent for creating and updating document plans
"""
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime

from app.agents.agent_config import AgentConfig, AgentType
from app.agents.llm_router import LLMRouter
from app.agents.agent_states import DocumentPlan, AgentContext, AgentMessage
from app.telemetry import trace_agent, telemetry

logger = logging.getLogger(__name__)


class DocumentPlanner:
    """Agent responsible for creating and managing document plans"""
    
    def __init__(self, llm_router: LLMRouter, config: AgentConfig):
        self.llm_router = llm_router
        self.config = config
        self.agent_type = AgentType.PLANNER
    
    @trace_agent("planner", "create_plan")
    async def create_plan(self, 
                         user_request: str, 
                         analysis: Dict[str, Any]) -> DocumentPlan:
        """Create a new document plan"""
        
        try:
            # Build planning prompt
            planning_prompt = self._build_planning_prompt(user_request, analysis)
            
            # Get plan from LLM
            plan_response = await self.llm_router.route_request(
                self.agent_type,
                planning_prompt
            )
            
            # Parse plan response
            plan_data = self._parse_plan_response(plan_response)
            
            # Create DocumentPlan object
            plan = DocumentPlan(
                document_type=plan_data.get("document_type", "document"),
                title=plan_data.get("title", "Untitled Document"),
                sections=plan_data.get("sections", []),
                estimated_time=plan_data.get("estimated_time", 300),
                total_steps=len(plan_data.get("sections", []))
            )
            
            logger.info(f"Created plan with {len(plan.sections)} sections")
            return plan
            
        except Exception as e:
            logger.error(f"Error creating plan: {e}")
            # Return fallback plan
            return self._create_fallback_plan(user_request)
    
    async def update_plan(self, 
                         current_plan: DocumentPlan,
                         user_request: str,
                         analysis: Dict[str, Any]) -> DocumentPlan:
        """Update an existing document plan"""
        
        try:
            # Build update prompt
            update_prompt = self._build_update_prompt(current_plan, user_request, analysis)
            
            # Get updated plan from LLM
            update_response = await self.llm_router.route_request(
                self.agent_type,
                update_prompt
            )
            
            # Parse update response
            update_data = self._parse_plan_response(update_response)
            
            # Update the plan
            updated_plan = DocumentPlan(
                document_type=update_data.get("document_type", current_plan.document_type),
                title=update_data.get("title", current_plan.title),
                sections=update_data.get("sections", current_plan.sections),
                estimated_time=update_data.get("estimated_time", current_plan.estimated_time),
                current_step=current_plan.current_step,
                total_steps=len(update_data.get("sections", current_plan.sections)),
                created_at=current_plan.created_at,
                updated_at=datetime.utcnow()
            )
            
            logger.info(f"Updated plan with {len(updated_plan.sections)} sections")
            return updated_plan
            
        except Exception as e:
            logger.error(f"Error updating plan: {e}")
            # Return current plan if update fails
            return current_plan
    
    def _build_planning_prompt(self, user_request: str, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build prompt for document planning"""
        
        system_prompt = """
        You are a strategic document planner. Create a detailed plan for document creation.
        
        Your response should be a JSON object with:
        - document_type: type of document (proposal, report, presentation, etc.)
        - title: document title
        - sections: array of section objects with {title, description, estimated_words, priority}
        - estimated_time: total estimated time in seconds
        
        Consider:
        - Document purpose and audience
        - Logical flow and structure
        - Content requirements
        - Time constraints
        
        Be strategic and think about the best way to organize the content.
        """
        
        intent_context = f"""
        User Intent: {analysis.get('intent', 'unknown')}
        Confidence: {analysis.get('confidence', 0.5)}
        Document Type Hints: {analysis.get('document_type', 'general')}
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {intent_context}"},
            {"role": "user", "content": f"User Request: {user_request}"}
        ]
    
    def _build_update_prompt(self, 
                           current_plan: DocumentPlan,
                           user_request: str,
                           analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build prompt for plan updates"""
        
        system_prompt = """
        You are updating an existing document plan. Modify the plan based on the user's request.
        
        Your response should be a JSON object with the updated plan structure.
        Consider:
        - What changes are needed
        - How to preserve existing good structure
        - Whether to add, modify, or remove sections
        - Updated time estimates
        
        Be thoughtful about maintaining document coherence.
        """
        
        current_plan_info = f"""
        Current Plan:
        - Type: {current_plan.document_type}
        - Title: {current_plan.title}
        - Sections: {len(current_plan.sections)}
        - Progress: {current_plan.current_step}/{current_plan.total_steps}
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Current Plan: {current_plan_info}"},
            {"role": "user", "content": f"User Request: {user_request}"}
        ]
    
    def _parse_plan_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into plan data"""
        
        try:
            # Try to parse as JSON
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # Try to extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response[start:end]
                return json.loads(json_str)
            
            # If no JSON found, create from text
            return self._extract_plan_from_text(response)
            
        except Exception as e:
            logger.error(f"Error parsing plan response: {e}")
            return self._create_basic_plan_structure()
    
    def _extract_plan_from_text(self, text: str) -> Dict[str, Any]:
        """Extract plan structure from text response"""
        
        # Basic text parsing - look for common patterns
        lines = text.split('\n')
        sections = []
        title = "Document"
        
        for line in lines:
            line = line.strip()
            if line.startswith('Title:') or line.startswith('# '):
                title = line.replace('Title:', '').replace('# ', '').strip()
            elif line.startswith('- ') or line.startswith('* '):
                sections.append({
                    "title": line.replace('- ', '').replace('* ', '').strip(),
                    "description": "",
                    "estimated_words": 200,
                    "priority": "medium"
                })
        
        return {
            "document_type": "document",
            "title": title,
            "sections": sections,
            "estimated_time": len(sections) * 300  # 5 minutes per section
        }
    
    def _create_basic_plan_structure(self) -> Dict[str, Any]:
        """Create basic plan structure as fallback"""
        
        return {
            "document_type": "document",
            "title": "Document",
            "sections": [
                {
                    "title": "Introduction",
                    "description": "Document introduction",
                    "estimated_words": 150,
                    "priority": "high"
                },
                {
                    "title": "Main Content",
                    "description": "Main document content",
                    "estimated_words": 500,
                    "priority": "high"
                },
                {
                    "title": "Conclusion",
                    "description": "Document conclusion",
                    "estimated_words": 100,
                    "priority": "medium"
                }
            ],
            "estimated_time": 900  # 15 minutes
        }
    
    def _create_fallback_plan(self, user_request: str) -> DocumentPlan:
        """Create fallback plan when LLM fails"""
        
        return DocumentPlan(
            document_type="document",
            title="Document",
            sections=[
                {
                    "title": "Content",
                    "description": f"Content based on: {user_request[:100]}...",
                    "estimated_words": 300,
                    "priority": "high"
                }
            ],
            estimated_time=600,
            total_steps=1
        )
    
    async def analyze_plan_progress(self, plan: DocumentPlan) -> Dict[str, Any]:
        """Analyze current plan progress"""
        
        completion_percentage = (plan.current_step / plan.total_steps * 100) if plan.total_steps > 0 else 0
        
        return {
            "completion_percentage": completion_percentage,
            "current_step": plan.current_step,
            "total_steps": plan.total_steps,
            "estimated_remaining_time": plan.estimated_time * (1 - completion_percentage / 100),
            "next_section": plan.sections[plan.current_step] if plan.current_step < len(plan.sections) else None
        }
    
    async def suggest_improvements(self, plan: DocumentPlan) -> List[str]:
        """Suggest improvements to the plan"""
        
        # Build improvement prompt
        improvement_prompt = self._build_improvement_prompt(plan)
        
        try:
            suggestions_response = await self.llm_router.route_request(
                self.agent_type,
                improvement_prompt
            )
            
            # Parse suggestions
            suggestions = suggestions_response.split('\n')
            return [s.strip() for s in suggestions if s.strip()]
            
        except Exception as e:
            logger.error(f"Error getting plan improvements: {e}")
            return ["Consider adding more detail to sections", "Review section order"]
    
    def _build_improvement_prompt(self, plan: DocumentPlan) -> List[Dict[str, str]]:
        """Build prompt for plan improvements"""
        
        system_prompt = """
        Analyze the document plan and suggest improvements.
        Focus on:
        - Content organization
        - Section completeness
        - Logical flow
        - Missing elements
        
        Provide specific, actionable suggestions.
        """
        
        plan_summary = f"""
        Plan: {plan.title}
        Type: {plan.document_type}
        Sections: {len(plan.sections)}
        Progress: {plan.current_step}/{plan.total_steps}
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Plan to analyze: {plan_summary}"}
        ]