from typing import Dict, Any, List
from enum import Enum


class DocumentType(str, Enum):
    PROPOSAL = "proposal"
    REPORT = "report"
    PRESENTATION = "presentation"
    MEMO = "memo"
    LETTER = "letter"
    RESUME = "resume"
    WHITEPAPER = "whitepaper"
    MANUAL = "manual"
    ARTICLE = "article"
    CREATIVE = "creative"


class PromptService:
    def __init__(self):
        self.base_system_prompt = """You are DocuForge AI, an expert document creation assistant. You help users create professional documents through conversational interaction.

Your capabilities:
- Generate structured, well-formatted documents
- Understand document requirements from natural language
- Create appropriate sections and content
- Suggest improvements and refinements
- Maintain professional tone and style

Always respond with structured JSON when creating document content."""

    def get_document_creation_prompt(self, document_type: DocumentType, user_input: str) -> List[Dict[str, str]]:
        """Generate prompt for creating a new document"""
        
        type_instructions = self._get_type_specific_instructions(document_type)
        
        system_message = f"""{self.base_system_prompt}

{type_instructions}

User Request: {user_input}

Please create a document structure based on the user's request. Respond with a JSON object containing:
- title: A clear, professional title
- sections: Array of sections with 'title' and 'content' fields
- metadata: Document type, estimated length, tone, etc.
- suggestions: Array of improvement suggestions

Keep content professional but engaging. If user request is unclear, ask clarifying questions."""

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ]

    def get_content_expansion_prompt(self, section_title: str, current_content: str, user_request: str) -> List[Dict[str, str]]:
        """Generate prompt for expanding specific section content"""
        
        system_message = f"""{self.base_system_prompt}

The user wants to expand or modify the following section:
Title: {section_title}
Current Content: {current_content}

User Request: {user_request}

Please provide the expanded/modified content while maintaining consistency with the overall document. Respond with just the new content for this section."""

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_request}
        ]

    def get_style_adjustment_prompt(self, content: Dict[str, Any], style_request: str) -> List[Dict[str, str]]:
        """Generate prompt for adjusting document style/tone"""
        
        system_message = f"""{self.base_system_prompt}

The user wants to adjust the style/tone of their document:
Current Document: {content}

Style Request: {style_request}

Please modify the document content to match the requested style while preserving the core information. Respond with the complete updated document in JSON format."""

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": style_request}
        ]

    def get_image_suggestion_prompt(self, document_content: Dict[str, Any], section_title: str = None) -> List[Dict[str, str]]:
        """Generate prompt for suggesting images for document sections"""
        
        context = f"Document: {document_content.get('title', 'Unknown')}"
        if section_title:
            context += f"\nSection: {section_title}"
        
        system_message = f"""{self.base_system_prompt}

Based on the document content, suggest appropriate images that would enhance the document:
{context}

Please suggest 3-5 relevant images with:
- Description of the image
- Suggested placement in document
- Alt text for accessibility
- Image style/type (photo, illustration, chart, etc.)

Respond with JSON array of image suggestions."""

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Suggest images for this document content: {document_content}"}
        ]

    def get_summary_prompt(self, document_content: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate prompt for creating document summary"""
        
        system_message = f"""{self.base_system_prompt}

Please create a concise summary of this document:
{document_content}

The summary should:
- Capture key points and main themes
- Be 2-3 sentences long
- Suitable for preview/overview purposes"""

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": "Create a summary of this document"}
        ]

    def get_intent_detection_prompt(self, user_input: str) -> List[Dict[str, str]]:
        """Generate prompt for detecting user intent"""
        
        system_message = f"""{self.base_system_prompt}

Analyze the user's input to determine their intent. Respond with JSON containing:
- intent: One of [create_document, modify_content, change_style, add_section, generate_image, export_document, ask_question]
- document_type: If creating document, suggest type from {list(DocumentType)}
- confidence: 0-1 score
- parameters: Relevant parameters extracted from input
- clarification_needed: Boolean if more info needed

User Input: {user_input}"""

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ]

    def _get_type_specific_instructions(self, document_type: DocumentType) -> str:
        """Get specific instructions for different document types"""
        
        instructions = {
            DocumentType.PROPOSAL: """
For PROPOSAL documents:
- Start with executive summary
- Include problem statement, solution, timeline, budget
- Use persuasive but professional tone
- Include clear call-to-action
- Structure: Executive Summary, Problem, Solution, Timeline, Budget, Conclusion
""",
            DocumentType.REPORT: """
For REPORT documents:
- Start with executive summary
- Include methodology, findings, recommendations
- Use objective, analytical tone
- Support with data and evidence
- Structure: Executive Summary, Introduction, Methodology, Findings, Analysis, Recommendations
""",
            DocumentType.PRESENTATION: """
For PRESENTATION documents:
- Create slide-friendly content
- Use bullet points and clear headings
- Include speaker notes
- Visual-heavy approach
- Structure: Title Slide, Agenda, Main Content Slides, Conclusion, Q&A
""",
            DocumentType.MEMO: """
For MEMO documents:
- Brief and to-the-point
- Clear subject line
- Direct communication style
- Action items clearly stated
- Structure: To/From/Date/Subject, Summary, Details, Action Items
""",
            DocumentType.LETTER: """
For LETTER documents:
- Professional business format
- Clear purpose and call-to-action
- Appropriate salutation and closing
- Personal but professional tone
- Structure: Header, Date, Recipient, Salutation, Body, Closing, Signature
""",
            DocumentType.RESUME: """
For RESUME documents:
- Professional formatting
- Quantifiable achievements
- Relevant skills and experience
- Concise and scannable
- Structure: Contact Info, Summary, Experience, Skills, Education, Additional Sections
""",
            DocumentType.WHITEPAPER: """
For WHITEPAPER documents:
- Authoritative and informative
- Research-backed content
- Technical depth with accessibility
- Thought leadership tone
- Structure: Abstract, Introduction, Problem, Solution, Case Studies, Conclusion
""",
            DocumentType.MANUAL: """
For MANUAL documents:
- Step-by-step instructions
- Clear, actionable language
- Troubleshooting sections
- User-friendly format
- Structure: Overview, Getting Started, Features, Procedures, Troubleshooting, FAQ
""",
            DocumentType.ARTICLE: """
For ARTICLE documents:
- Engaging introduction
- Well-researched content
- Clear structure with subheadings
- Informative and accessible tone
- Structure: Headline, Introduction, Main Content, Conclusion, References
""",
            DocumentType.CREATIVE: """
For CREATIVE documents:
- Flexible structure based on content
- Engaging and original voice
- Appropriate formatting for medium
- Creative but readable approach
- Structure: Varies based on creative type
"""
        }
        
        return instructions.get(document_type, "Create a well-structured professional document.")

    def get_conversation_context_prompt(self, conversation_history: List[Dict[str, str]], new_message: str) -> List[Dict[str, str]]:
        """Generate prompt with conversation context"""
        
        messages = [{"role": "system", "content": self.base_system_prompt}]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Keep last 10 messages for context
            messages.append(msg)
        
        # Add new message
        messages.append({"role": "user", "content": new_message})
        
        return messages