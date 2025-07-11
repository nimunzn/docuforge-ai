from typing import Dict, Any, Optional, List
import os
from datetime import datetime
from app.models.document import Document
from app.services.unified_document import UnifiedDocument, DocumentFormat
from app.services.generators.word_generator import WordGenerator
from app.services.generators.powerpoint_generator import PowerPointGenerator
from app.services.generators.pdf_generator import PDFGenerator


class ExportService:
    def __init__(self):
        self.export_dir = "exports"
        os.makedirs(self.export_dir, exist_ok=True)
        
        # Initialize generators
        self.word_generator = WordGenerator()
        self.powerpoint_generator = PowerPointGenerator()
        self.pdf_generator = PDFGenerator()

    async def export_document(
        self, 
        document: Document, 
        format: str, 
        include_images: bool = True,
        options: Dict[str, Any] = None
    ) -> bytes:
        """Export document in specified format with options"""
        options = options or {}
        options['include_images'] = include_images
        
        # Convert to unified document model
        unified_doc = self._convert_to_unified_document(document)
        
        # Optimize for target format
        format_enum = DocumentFormat(format.lower())
        unified_doc.optimize_for_format(format_enum)
        
        # Export in requested format
        return unified_doc.export(format_enum, options)

    def _convert_to_unified_document(self, document: Document) -> UnifiedDocument:
        """Convert database document to unified document model"""
        if document.content:
            # Use new unified document model
            return UnifiedDocument.from_legacy_format({
                'title': document.title,
                'sections': document.content.get('sections', []),
                'metadata': {
                    'document_type': document.type,
                    'created_at': document.created_at.isoformat(),
                    'updated_at': document.updated_at.isoformat(),
                    'id': document.id
                }
            })
        else:
            # Create empty document
            unified_doc = UnifiedDocument(title=document.title, document_type=document.type)
            unified_doc.set_metadata('created_at', document.created_at.isoformat())
            unified_doc.set_metadata('updated_at', document.updated_at.isoformat())
            unified_doc.set_metadata('id', document.id)
            return unified_doc

    async def export_with_advanced_options(
        self, 
        document: Document, 
        format: str, 
        options: Dict[str, Any]
    ) -> bytes:
        """Export with advanced formatting options"""
        
        # Enhanced options for different formats
        if format.lower() == "docx":
            word_options = {
                'page_break_between_sections': options.get('page_breaks', False),
                'include_toc': options.get('table_of_contents', False),
                'font_size': options.get('font_size', 11),
                'line_spacing': options.get('line_spacing', 1.15),
                'margin_size': options.get('margins', 1.0)
            }
            return await self._export_to_word_advanced(document, word_options)
            
        elif format.lower() == "pptx":
            ppt_options = {
                'slide_size': options.get('slide_size', 'widescreen'),
                'include_agenda': options.get('include_agenda', True),
                'include_conclusion': options.get('include_conclusion', True),
                'include_qna': options.get('include_qna', True),
                'section_headers': options.get('section_headers', False),
                'theme': options.get('theme', 'default')
            }
            return await self._export_to_powerpoint_advanced(document, ppt_options)
            
        elif format.lower() == "pdf":
            pdf_options = {
                'page_size': options.get('page_size', 'letter'),
                'include_toc': options.get('table_of_contents', False),
                'page_break_between_sections': options.get('page_breaks', False),
                'header_footer': options.get('header_footer', True),
                'page_numbers': options.get('page_numbers', True)
            }
            return await self._export_to_pdf_advanced(document, pdf_options)
        
        else:
            # Fall back to basic export
            return await self.export_document(document, format, options.get('include_images', True))

    async def _export_to_word_advanced(self, document: Document, options: Dict[str, Any]) -> bytes:
        """Export to Word with advanced options"""
        unified_doc = self._convert_to_unified_document(document)
        return unified_doc.to_word(options)

    async def _export_to_powerpoint_advanced(self, document: Document, options: Dict[str, Any]) -> bytes:
        """Export to PowerPoint with advanced options"""
        unified_doc = self._convert_to_unified_document(document)
        return unified_doc.to_powerpoint(options)

    async def _export_to_pdf_advanced(self, document: Document, options: Dict[str, Any]) -> bytes:
        """Export to PDF with advanced options"""
        unified_doc = self._convert_to_unified_document(document)
        return unified_doc.to_pdf(options)

    def create_template_document(self, template_type: str, format: str, title: str = None) -> bytes:
        """Create a template document in specified format"""
        if format.lower() == "docx":
            return self.word_generator.create_template_document(template_type, title)
        elif format.lower() == "pptx":
            return self.powerpoint_generator.create_template_presentation(template_type, title)
        elif format.lower() == "pdf":
            return self.pdf_generator.create_template_document(template_type, title)
        else:
            raise ValueError(f"Unsupported format for template: {format}")

    def get_export_options(self, format: str) -> Dict[str, Any]:
        """Get available export options for a format"""
        if format.lower() == "docx":
            return {
                'page_breaks': {
                    'type': 'boolean',
                    'default': False,
                    'description': 'Add page breaks between sections'
                },
                'table_of_contents': {
                    'type': 'boolean',
                    'default': False,
                    'description': 'Include table of contents'
                },
                'font_size': {
                    'type': 'integer',
                    'default': 11,
                    'min': 8,
                    'max': 16,
                    'description': 'Font size for body text'
                },
                'line_spacing': {
                    'type': 'number',
                    'default': 1.15,
                    'min': 1.0,
                    'max': 2.0,
                    'description': 'Line spacing'
                },
                'margins': {
                    'type': 'number',
                    'default': 1.0,
                    'min': 0.5,
                    'max': 2.0,
                    'description': 'Margin size in inches'
                }
            }
        elif format.lower() == "pptx":
            return {
                'slide_size': {
                    'type': 'select',
                    'default': 'widescreen',
                    'options': ['widescreen', 'standard'],
                    'description': 'Slide size format'
                },
                'include_agenda': {
                    'type': 'boolean',
                    'default': True,
                    'description': 'Include agenda slide'
                },
                'include_conclusion': {
                    'type': 'boolean',
                    'default': True,
                    'description': 'Include conclusion slide'
                },
                'include_qna': {
                    'type': 'boolean',
                    'default': True,
                    'description': 'Include Q&A slide'
                },
                'section_headers': {
                    'type': 'boolean',
                    'default': False,
                    'description': 'Add section header slides'
                }
            }
        elif format.lower() == "pdf":
            return {
                'page_size': {
                    'type': 'select',
                    'default': 'letter',
                    'options': ['letter', 'A4'],
                    'description': 'Page size'
                },
                'table_of_contents': {
                    'type': 'boolean',
                    'default': False,
                    'description': 'Include table of contents'
                },
                'page_breaks': {
                    'type': 'boolean',
                    'default': False,
                    'description': 'Add page breaks between sections'
                },
                'header_footer': {
                    'type': 'boolean',
                    'default': True,
                    'description': 'Include header and footer'
                },
                'page_numbers': {
                    'type': 'boolean',
                    'default': True,
                    'description': 'Include page numbers'
                }
            }
        else:
            return {}

    def get_supported_formats(self) -> List[Dict[str, Any]]:
        """Get list of supported export formats"""
        return [
            {
                'format': 'docx',
                'name': 'Microsoft Word',
                'description': 'Word document with full formatting',
                'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'extension': '.docx'
            },
            {
                'format': 'pptx',
                'name': 'Microsoft PowerPoint',
                'description': 'PowerPoint presentation with slides',
                'mime_type': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'extension': '.pptx'
            },
            {
                'format': 'pdf',
                'name': 'PDF Document',
                'description': 'Portable Document Format',
                'mime_type': 'application/pdf',
                'extension': '.pdf'
            }
        ]

    def get_template_types(self) -> List[Dict[str, Any]]:
        """Get available template types"""
        return [
            {
                'type': 'proposal',
                'name': 'Business Proposal',
                'description': 'Professional business proposal template',
                'sections': ['Executive Summary', 'Problem Statement', 'Solution', 'Timeline', 'Budget', 'Conclusion']
            },
            {
                'type': 'report',
                'name': 'Research Report',
                'description': 'Comprehensive research report template',
                'sections': ['Executive Summary', 'Introduction', 'Methodology', 'Findings', 'Analysis', 'Recommendations']
            },
            {
                'type': 'presentation',
                'name': 'Business Presentation',
                'description': 'Professional presentation template',
                'sections': ['Title', 'Agenda', 'Introduction', 'Main Content', 'Conclusion', 'Q&A']
            },
            {
                'type': 'memo',
                'name': 'Business Memo',
                'description': 'Internal business memorandum template',
                'sections': ['Header', 'Purpose', 'Background', 'Discussion', 'Action Items']
            },
            {
                'type': 'whitepaper',
                'name': 'Technical Whitepaper',
                'description': 'Technical whitepaper template',
                'sections': ['Abstract', 'Introduction', 'Problem', 'Solution', 'Results', 'Conclusion']
            },
            {
                'type': 'manual',
                'name': 'User Manual',
                'description': 'User manual and documentation template',
                'sections': ['Getting Started', 'Features', 'Advanced', 'Troubleshooting', 'Support']
            }
        ]

    def save_export_to_file(self, content: bytes, filename: str, format: str) -> str:
        """Save exported content to file and return file path"""
        file_extension = f".{format.lower()}"
        if not filename.endswith(file_extension):
            filename += file_extension
        
        file_path = os.path.join(self.export_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return file_path

    def get_export_statistics(self, document: Document) -> Dict[str, Any]:
        """Get export statistics for a document"""
        unified_doc = self._convert_to_unified_document(document)
        return unified_doc.get_statistics()