from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from app.services.generators.word_generator import WordGenerator
from app.services.generators.powerpoint_generator import PowerPointGenerator
from app.services.generators.pdf_generator import PDFGenerator


class DocumentFormat(str, Enum):
    WORD = "docx"
    POWERPOINT = "pptx"
    PDF = "pdf"


class SectionType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    BULLET_LIST = "bullet_list"
    NUMBERED_LIST = "numbered_list"
    TABLE = "table"
    IMAGE = "image"
    QUOTE = "quote"
    CODE = "code"


@dataclass
class DocumentSection:
    """Represents a document section with unified structure"""
    title: str
    content: str
    section_type: SectionType = SectionType.PARAGRAPH
    level: int = 1  # Heading level (1-6)
    subsections: List['DocumentSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_subsection(self, subsection: 'DocumentSection'):
        """Add a subsection"""
        self.subsections.append(subsection)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'title': self.title,
            'content': self.content,
            'section_type': self.section_type.value,
            'level': self.level,
            'subsections': [sub.to_dict() for sub in self.subsections],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentSection':
        """Create from dictionary"""
        subsections = [cls.from_dict(sub) for sub in data.get('subsections', [])]
        return cls(
            title=data.get('title', ''),
            content=data.get('content', ''),
            section_type=SectionType(data.get('section_type', 'paragraph')),
            level=data.get('level', 1),
            subsections=subsections,
            metadata=data.get('metadata', {})
        )


@dataclass
class DocumentImage:
    """Represents an image in the document"""
    path: str
    caption: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    alt_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'caption': self.caption,
            'width': self.width,
            'height': self.height,
            'alt_text': self.alt_text
        }


@dataclass
class DocumentTable:
    """Represents a table in the document"""
    headers: List[str]
    rows: List[List[str]]
    caption: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'headers': self.headers,
            'rows': self.rows,
            'caption': self.caption
        }


class UnifiedDocument:
    """Unified document model that can be converted to any format"""
    
    def __init__(self, title: str = "", document_type: str = "document"):
        self.title = title
        self.document_type = document_type
        self.sections: List[DocumentSection] = []
        self.images: List[DocumentImage] = []
        self.tables: List[DocumentTable] = []
        self.metadata: Dict[str, Any] = {
            'created_at': datetime.utcnow().isoformat(),
            'document_type': document_type,
            'version': '1.0'
        }
        
        # Initialize generators
        self.word_generator = WordGenerator()
        self.powerpoint_generator = PowerPointGenerator()
        self.pdf_generator = PDFGenerator()
    
    def add_section(self, section: DocumentSection):
        """Add a section to the document"""
        self.sections.append(section)
    
    def add_image(self, image: DocumentImage):
        """Add an image to the document"""
        self.images.append(image)
    
    def add_table(self, table: DocumentTable):
        """Add a table to the document"""
        self.tables.append(table)
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata"""
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'title': self.title,
            'document_type': self.document_type,
            'sections': [section.to_dict() for section in self.sections],
            'images': [img.to_dict() for img in self.images],
            'tables': [table.to_dict() for table in self.tables],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedDocument':
        """Create from dictionary"""
        doc = cls(
            title=data.get('title', ''),
            document_type=data.get('document_type', 'document')
        )
        
        # Add sections
        for section_data in data.get('sections', []):
            section = DocumentSection.from_dict(section_data)
            doc.add_section(section)
        
        # Add images
        for img_data in data.get('images', []):
            image = DocumentImage(**img_data)
            doc.add_image(image)
        
        # Add tables
        for table_data in data.get('tables', []):
            table = DocumentTable(**table_data)
            doc.add_table(table)
        
        # Set metadata
        doc.metadata = data.get('metadata', {})
        
        return doc
    
    @classmethod
    def from_legacy_format(cls, data: Dict[str, Any]) -> 'UnifiedDocument':
        """Create from legacy document format"""
        doc = cls(
            title=data.get('title', ''),
            document_type=data.get('metadata', {}).get('document_type', 'document')
        )
        
        # Convert legacy sections
        for section_data in data.get('sections', []):
            section = DocumentSection(
                title=section_data.get('title', ''),
                content=section_data.get('content', ''),
                section_type=SectionType.PARAGRAPH,
                level=1
            )
            
            # Handle subsections if present
            for subsection_data in section_data.get('subsections', []):
                subsection = DocumentSection(
                    title=subsection_data.get('title', ''),
                    content=subsection_data.get('content', ''),
                    section_type=SectionType.PARAGRAPH,
                    level=2
                )
                section.add_subsection(subsection)
            
            doc.add_section(section)
        
        # Set metadata
        doc.metadata = data.get('metadata', {})
        
        return doc
    
    def to_word(self, options: Dict[str, Any] = None) -> bytes:
        """Convert to Word document"""
        options = options or {}
        
        # Convert to legacy format for word generator
        legacy_data = self._to_legacy_format()
        
        return self.word_generator.create_document(legacy_data, options)
    
    def to_powerpoint(self, options: Dict[str, Any] = None) -> bytes:
        """Convert to PowerPoint presentation"""
        options = options or {}
        
        # Convert to legacy format for powerpoint generator
        legacy_data = self._to_legacy_format()
        
        return self.powerpoint_generator.create_presentation(legacy_data, options)
    
    def to_pdf(self, options: Dict[str, Any] = None) -> bytes:
        """Convert to PDF document"""
        options = options or {}
        
        # Convert to legacy format for PDF generator
        legacy_data = self._to_legacy_format()
        
        return self.pdf_generator.create_document(legacy_data, options)
    
    def _to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for generators"""
        return {
            'title': self.title,
            'sections': [self._section_to_legacy(section) for section in self.sections],
            'metadata': self.metadata
        }
    
    def _section_to_legacy(self, section: DocumentSection) -> Dict[str, Any]:
        """Convert section to legacy format"""
        return {
            'title': section.title,
            'content': section.content,
            'subsections': [self._section_to_legacy(sub) for sub in section.subsections]
        }
    
    def export(self, format: DocumentFormat, options: Dict[str, Any] = None) -> bytes:
        """Export document in specified format"""
        options = options or {}
        
        if format == DocumentFormat.WORD:
            return self.to_word(options)
        elif format == DocumentFormat.POWERPOINT:
            return self.to_powerpoint(options)
        elif format == DocumentFormat.PDF:
            return self.to_pdf(options)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def optimize_for_format(self, format: DocumentFormat):
        """Optimize document structure for specific format"""
        if format == DocumentFormat.POWERPOINT:
            self._optimize_for_powerpoint()
        elif format == DocumentFormat.PDF:
            self._optimize_for_pdf()
        elif format == DocumentFormat.WORD:
            self._optimize_for_word()
    
    def _optimize_for_powerpoint(self):
        """Optimize for PowerPoint presentation"""
        # Split long sections into multiple slides
        optimized_sections = []
        
        for section in self.sections:
            if len(section.content) > 500:  # Long content
                # Split into bullet points or paragraphs
                content_parts = self._split_content_for_slides(section.content)
                
                for i, part in enumerate(content_parts):
                    title = section.title if i == 0 else f"{section.title} (cont.)"
                    new_section = DocumentSection(
                        title=title,
                        content=part,
                        section_type=SectionType.BULLET_LIST,
                        level=section.level
                    )
                    optimized_sections.append(new_section)
            else:
                # Convert to bullet points if appropriate
                if '\n-' in section.content or '\n*' in section.content:
                    section.section_type = SectionType.BULLET_LIST
                optimized_sections.append(section)
        
        self.sections = optimized_sections
    
    def _optimize_for_pdf(self):
        """Optimize for PDF document"""
        # Ensure proper heading hierarchy
        for section in self.sections:
            if section.level == 0:
                section.level = 1
            
            # Ensure subsections have proper levels
            for subsection in section.subsections:
                if subsection.level <= section.level:
                    subsection.level = section.level + 1
    
    def _optimize_for_word(self):
        """Optimize for Word document"""
        # Ensure proper formatting for Word
        for section in self.sections:
            # Process content for Word-specific formatting
            section.content = self._process_word_formatting(section.content)
            
            for subsection in section.subsections:
                subsection.content = self._process_word_formatting(subsection.content)
    
    def _split_content_for_slides(self, content: str) -> List[str]:
        """Split content into slide-sized chunks"""
        # Target ~300 characters per slide
        max_chars = 300
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        slides = []
        current_slide = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if current_length + len(para) > max_chars and current_slide:
                slides.append('\n\n'.join(current_slide))
                current_slide = [para]
                current_length = len(para)
            else:
                current_slide.append(para)
                current_length += len(para)
        
        if current_slide:
            slides.append('\n\n'.join(current_slide))
        
        return slides
    
    def _process_word_formatting(self, content: str) -> str:
        """Process content for Word-specific formatting"""
        # Convert bullet points to proper format
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip().startswith(('-', '*', '•')):
                # Convert to bullet point
                formatted_lines.append('• ' + line.strip()[1:].strip())
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def get_word_count(self) -> int:
        """Get total word count"""
        total_words = len(self.title.split()) if self.title else 0
        
        for section in self.sections:
            total_words += len(section.title.split()) if section.title else 0
            total_words += len(section.content.split()) if section.content else 0
            
            for subsection in section.subsections:
                total_words += len(subsection.title.split()) if subsection.title else 0
                total_words += len(subsection.content.split()) if subsection.content else 0
        
        return total_words
    
    def get_section_count(self) -> int:
        """Get total section count"""
        count = len(self.sections)
        for section in self.sections:
            count += len(section.subsections)
        return count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get document statistics"""
        return {
            'word_count': self.get_word_count(),
            'section_count': self.get_section_count(),
            'image_count': len(self.images),
            'table_count': len(self.tables),
            'document_type': self.document_type,
            'created_at': self.metadata.get('created_at'),
            'title': self.title
        }