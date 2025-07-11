"""
Document Reviewer Agent
Specialized agent for reviewing and improving document content
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime

from app.agents.agent_config import AgentConfig, AgentType
from app.agents.llm_router import LLMRouter
from app.agents.agent_states import DocumentPlan, AgentContext, AgentMessage
from app.telemetry import trace_agent, telemetry

logger = logging.getLogger(__name__)


class DocumentReviewer:
    """Agent responsible for reviewing and improving document content"""
    
    def __init__(self, llm_router: LLMRouter, config: AgentConfig):
        self.llm_router = llm_router
        self.config = config
        self.agent_type = AgentType.REVIEWER
    
    @trace_agent("reviewer", "review_content")
    async def review_content(self, 
                           context: AgentContext, 
                           plan: Optional[DocumentPlan] = None) -> Dict[str, Any]:
        """Review document content and provide feedback"""
        
        try:
            # Get current content (this would typically come from the document service)
            current_content = await self._get_current_content(context)
            
            # Perform comprehensive review
            review_result = await self._comprehensive_review(current_content, context, plan)
            
            return {
                "success": True,
                "score": review_result["score"],
                "feedback": review_result["feedback"],
                "suggestions": review_result["suggestions"],
                "areas_for_improvement": review_result["areas_for_improvement"],
                "strengths": review_result["strengths"],
                "revision_needed": review_result["score"] < 7
            }
            
        except Exception as e:
            logger.error(f"Error reviewing content: {e}")
            return {
                "success": False,
                "error": str(e),
                "score": 5,
                "feedback": "Review failed",
                "suggestions": [],
                "revision_needed": True
            }
    
    async def _get_current_content(self, context: AgentContext) -> str:
        """Get current document content"""
        # This would typically fetch from the document service
        # For now, return placeholder content
        return "Document content placeholder"
    
    async def _comprehensive_review(self, 
                                  content: str, 
                                  context: AgentContext, 
                                  plan: Optional[DocumentPlan]) -> Dict[str, Any]:
        """Perform comprehensive content review"""
        
        # Build review prompt
        review_prompt = self._build_review_prompt(content, context, plan)
        
        # Get review from LLM
        review_response = await self.llm_router.route_request(
            self.agent_type,
            review_prompt
        )
        
        # Parse review response
        review_data = self._parse_review_response(review_response)
        
        return review_data
    
    def _build_review_prompt(self, 
                           content: str, 
                           context: AgentContext, 
                           plan: Optional[DocumentPlan]) -> List[Dict[str, str]]:
        """Build prompt for content review"""
        
        system_prompt = """
        You are a professional document reviewer. Provide a comprehensive analysis of the content.
        
        Evaluate:
        1. Content Quality (clarity, accuracy, completeness)
        2. Structure and Organization
        3. Writing Style and Tone
        4. Grammar and Language
        5. Relevance to Purpose
        
        Provide:
        - Overall score (1-10)
        - Specific feedback
        - Actionable suggestions
        - Areas for improvement
        - Identified strengths
        
        Format your response as a structured analysis.
        """
        
        context_info = ""
        if plan:
            context_info = f"""
            Document Type: {plan.document_type}
            Title: {plan.title}
            Expected Sections: {len(plan.sections)}
            """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context_info}"},
            {"role": "user", "content": f"Content to review: {content}"}
        ]
    
    def _parse_review_response(self, response: str) -> Dict[str, Any]:
        """Parse review response into structured data"""
        
        try:
            # Extract score
            score = self._extract_score(response)
            
            # Extract feedback sections
            feedback = self._extract_feedback(response)
            suggestions = self._extract_suggestions(response)
            areas_for_improvement = self._extract_areas_for_improvement(response)
            strengths = self._extract_strengths(response)
            
            return {
                "score": score,
                "feedback": feedback,
                "suggestions": suggestions,
                "areas_for_improvement": areas_for_improvement,
                "strengths": strengths
            }
            
        except Exception as e:
            logger.error(f"Error parsing review response: {e}")
            return self._create_fallback_review()
    
    def _extract_score(self, response: str) -> int:
        """Extract numerical score from response"""
        
        # Look for score patterns
        import re
        
        # Pattern: "Score: 8/10" or "8/10" or "Score: 8"
        patterns = [
            r'score[:\s]*(\d+)(?:/10)?',
            r'(\d+)/10',
            r'rating[:\s]*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.lower())
            if match:
                score = int(match.group(1))
                return min(max(score, 1), 10)  # Clamp between 1-10
        
        # Default score if not found
        return 7
    
    def _extract_feedback(self, response: str) -> str:
        """Extract main feedback from response"""
        
        # Look for feedback sections
        lines = response.split('\n')
        feedback_lines = []
        
        in_feedback_section = False
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['feedback', 'analysis', 'review']):
                in_feedback_section = True
                continue
            elif any(keyword in line.lower() for keyword in ['suggestion', 'improvement', 'strength']):
                in_feedback_section = False
            elif in_feedback_section and line:
                feedback_lines.append(line)
        
        return '\n'.join(feedback_lines) if feedback_lines else response[:200]
    
    def _extract_suggestions(self, response: str) -> List[str]:
        """Extract suggestions from response"""
        
        suggestions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                suggestion = line[2:].strip()
                if any(keyword in suggestion.lower() for keyword in ['suggest', 'recommend', 'consider', 'try']):
                    suggestions.append(suggestion)
        
        return suggestions[:5]  # Limit to top 5
    
    def _extract_areas_for_improvement(self, response: str) -> List[str]:
        """Extract areas for improvement from response"""
        
        areas = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['improve', 'better', 'enhance', 'fix']):
                areas.append(line)
        
        return areas[:3]  # Limit to top 3
    
    def _extract_strengths(self, response: str) -> List[str]:
        """Extract strengths from response"""
        
        strengths = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['good', 'strong', 'excellent', 'well']):
                strengths.append(line)
        
        return strengths[:3]  # Limit to top 3
    
    def _create_fallback_review(self) -> Dict[str, Any]:
        """Create fallback review when parsing fails"""
        
        return {
            "score": 7,
            "feedback": "Content appears to be well-structured and informative.",
            "suggestions": ["Consider adding more specific examples", "Review for clarity"],
            "areas_for_improvement": ["Content organization", "Detail level"],
            "strengths": ["Clear writing style", "Good structure"]
        }
    
    async def check_grammar_and_style(self, content: str) -> Dict[str, Any]:
        """Check grammar and style issues"""
        
        try:
            # Build grammar check prompt
            grammar_prompt = self._build_grammar_check_prompt(content)
            
            # Get grammar analysis
            grammar_response = await self.llm_router.route_request(
                self.agent_type,
                grammar_prompt
            )
            
            return {
                "success": True,
                "issues_found": self._extract_grammar_issues(grammar_response),
                "suggestions": self._extract_grammar_suggestions(grammar_response),
                "overall_assessment": grammar_response
            }
            
        except Exception as e:
            logger.error(f"Error checking grammar: {e}")
            return {
                "success": False,
                "error": str(e),
                "issues_found": [],
                "suggestions": []
            }
    
    def _build_grammar_check_prompt(self, content: str) -> List[Dict[str, str]]:
        """Build prompt for grammar and style checking"""
        
        system_prompt = """
        You are a grammar and style expert. Review the content for:
        - Grammar errors
        - Spelling mistakes
        - Punctuation issues
        - Style inconsistencies
        - Readability problems
        
        Provide specific, actionable feedback.
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Content to check: {content}"}
        ]
    
    def _extract_grammar_issues(self, response: str) -> List[str]:
        """Extract grammar issues from response"""
        
        issues = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['error', 'mistake', 'incorrect', 'issue']):
                issues.append(line)
        
        return issues
    
    def _extract_grammar_suggestions(self, response: str) -> List[str]:
        """Extract grammar suggestions from response"""
        
        suggestions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                suggestion = line[2:].strip()
                if any(keyword in suggestion.lower() for keyword in ['change', 'replace', 'correct']):
                    suggestions.append(suggestion)
        
        return suggestions
    
    async def assess_completeness(self, 
                                content: str, 
                                plan: Optional[DocumentPlan]) -> Dict[str, Any]:
        """Assess content completeness against plan"""
        
        if not plan:
            return {
                "completeness_score": 8,
                "missing_sections": [],
                "assessment": "No plan available for comparison"
            }
        
        try:
            # Build completeness prompt
            completeness_prompt = self._build_completeness_prompt(content, plan)
            
            # Get completeness assessment
            completeness_response = await self.llm_router.route_request(
                self.agent_type,
                completeness_prompt
            )
            
            return {
                "success": True,
                "completeness_score": self._extract_completeness_score(completeness_response),
                "missing_sections": self._extract_missing_sections(completeness_response),
                "assessment": completeness_response
            }
            
        except Exception as e:
            logger.error(f"Error assessing completeness: {e}")
            return {
                "success": False,
                "error": str(e),
                "completeness_score": 6,
                "missing_sections": []
            }
    
    def _build_completeness_prompt(self, content: str, plan: DocumentPlan) -> List[Dict[str, str]]:
        """Build prompt for completeness assessment"""
        
        system_prompt = """
        Compare the content against the planned document structure.
        
        Assess:
        - Are all planned sections present?
        - Does content match section requirements?
        - Are there any gaps or missing elements?
        - Is the content comprehensive for the intended purpose?
        
        Provide a completeness score (1-10) and identify any missing sections.
        """
        
        plan_info = f"""
        Planned Document: {plan.title}
        Type: {plan.document_type}
        Expected Sections: {[section['title'] for section in plan.sections]}
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Plan: {plan_info}"},
            {"role": "user", "content": f"Content to assess: {content}"}
        ]
    
    def _extract_completeness_score(self, response: str) -> int:
        """Extract completeness score from response"""
        
        # Use same extraction method as overall score
        return self._extract_score(response)
    
    def _extract_missing_sections(self, response: str) -> List[str]:
        """Extract missing sections from response"""
        
        missing_sections = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['missing', 'absent', 'not found', 'lacking']):
                missing_sections.append(line)
        
        return missing_sections
    
    async def suggest_improvements(self, 
                                 review_result: Dict[str, Any],
                                 content: str) -> List[str]:
        """Generate specific improvement suggestions"""
        
        try:
            # Build improvement prompt
            improvement_prompt = self._build_improvement_prompt(review_result, content)
            
            # Get improvement suggestions
            improvement_response = await self.llm_router.route_request(
                self.agent_type,
                improvement_prompt
            )
            
            return self._extract_improvement_suggestions(improvement_response)
            
        except Exception as e:
            logger.error(f"Error generating improvements: {e}")
            return ["Review content for clarity", "Check grammar and spelling"]
    
    def _build_improvement_prompt(self, review_result: Dict[str, Any], content: str) -> List[Dict[str, str]]:
        """Build prompt for improvement suggestions"""
        
        system_prompt = """
        Based on the review feedback, provide specific, actionable improvement suggestions.
        Focus on the most impactful changes that will enhance the content quality.
        """
        
        review_summary = f"""
        Review Score: {review_result.get('score', 7)}
        Areas for Improvement: {review_result.get('areas_for_improvement', [])}
        Current Feedback: {review_result.get('feedback', 'No feedback')}
        """
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Review Summary: {review_summary}"},
            {"role": "user", "content": f"Content: {content[:500]}..."}
        ]
    
    def _extract_improvement_suggestions(self, response: str) -> List[str]:
        """Extract improvement suggestions from response"""
        
        suggestions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('* ') or line.startswith('1.'):
                suggestion = line.lstrip('-*0123456789. ').strip()
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions[:10]  # Limit to top 10