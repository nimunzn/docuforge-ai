from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, black, blue, gray
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
from typing import Dict, Any, List, Optional
import os
from datetime import datetime


class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold',
            keepWithNext=True
        ))
        
        # Subheading style
        self.styles.add(ParagraphStyle(
            name='CustomSubheading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=16,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold',
            leftIndent=20
        ))
        
        # Body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Caption style
        self.styles.add(ParagraphStyle(
            name='Caption',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique',
            textColor=colors.gray
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            fontName='Helvetica',
            textColor=colors.gray
        ))
    
    def create_document(self, document_data: Dict[str, Any], options: Dict[str, Any] = None) -> bytes:
        """Create a PDF document from document data"""
        options = options or {}
        
        # Create buffer
        buffer = BytesIO()
        
        # Create document
        page_size = A4 if options.get('page_size') == 'A4' else letter
        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build story
        story = []
        
        # Add title
        title = document_data.get('title', 'Document')
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Add metadata
        metadata = document_data.get('metadata', {})
        if metadata:
            story.extend(self._add_metadata(metadata))
        
        # Add table of contents if requested
        if options.get('include_toc', False):
            story.extend(self._add_table_of_contents(document_data))
        
        # Add sections
        sections = document_data.get('sections', [])
        for i, section in enumerate(sections):
            story.extend(self._add_section(section, options))
            
            # Add page break between sections if requested
            if options.get('page_break_between_sections', False) and i < len(sections) - 1:
                story.append(PageBreak())
        
        # Build PDF
        doc.build(story, onFirstPage=self._first_page_template, onLaterPages=self._later_pages_template)
        
        # Get PDF bytes
        buffer.seek(0)
        return buffer.getvalue()
    
    def _add_metadata(self, metadata: Dict[str, Any]) -> List:
        """Add metadata to document"""
        elements = []
        
        if metadata.get('author'):
            elements.append(Paragraph(f"<b>Author:</b> {metadata['author']}", self.styles['Normal']))
        
        if metadata.get('created_at'):
            date_str = metadata['created_at'][:10] if isinstance(metadata['created_at'], str) else str(metadata['created_at'])
            elements.append(Paragraph(f"<b>Date:</b> {date_str}", self.styles['Normal']))
        
        if metadata.get('organization'):
            elements.append(Paragraph(f"<b>Organization:</b> {metadata['organization']}", self.styles['Normal']))
        
        if metadata.get('document_type'):
            elements.append(Paragraph(f"<b>Document Type:</b> {metadata['document_type'].title()}", self.styles['Normal']))
        
        if elements:
            elements.append(Spacer(1, 20))
        
        return elements
    
    def _add_table_of_contents(self, document_data: Dict[str, Any]) -> List:
        """Add table of contents"""
        elements = []
        
        elements.append(Paragraph("Table of Contents", self.styles['CustomHeading']))
        elements.append(Spacer(1, 12))
        
        sections = document_data.get('sections', [])
        for i, section in enumerate(sections):
            section_title = section.get('title', f'Section {i+1}')
            elements.append(Paragraph(f"{i+1}. {section_title}", self.styles['Normal']))
            
            # Add subsections
            subsections = section.get('subsections', [])
            for j, subsection in enumerate(subsections):
                subsection_title = subsection.get('title', f'Subsection {j+1}')
                elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{i+1}.{j+1}. {subsection_title}", self.styles['Normal']))
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _add_section(self, section: Dict[str, Any], options: Dict[str, Any]) -> List:
        """Add a section to the document"""
        elements = []
        
        section_title = section.get('title', '')
        section_content = section.get('content', '')
        
        # Add section heading
        if section_title:
            elements.append(Paragraph(section_title, self.styles['CustomHeading']))
        
        # Add section content
        if section_content:
            paragraphs = section_content.split('\n\n')
            for para_text in paragraphs:
                if para_text.strip():
                    # Process formatting
                    formatted_text = self._process_text_formatting(para_text.strip())
                    elements.append(Paragraph(formatted_text, self.styles['CustomBody']))
        
        # Add subsections
        subsections = section.get('subsections', [])
        for subsection in subsections:
            elements.extend(self._add_subsection(subsection, options))
        
        elements.append(Spacer(1, 12))
        return elements
    
    def _add_subsection(self, subsection: Dict[str, Any], options: Dict[str, Any]) -> List:
        """Add a subsection to the document"""
        elements = []
        
        subsection_title = subsection.get('title', '')
        subsection_content = subsection.get('content', '')
        
        # Add subsection heading
        if subsection_title:
            elements.append(Paragraph(subsection_title, self.styles['CustomSubheading']))
        
        # Add subsection content
        if subsection_content:
            paragraphs = subsection_content.split('\n\n')
            for para_text in paragraphs:
                if para_text.strip():
                    formatted_text = self._process_text_formatting(para_text.strip())
                    elements.append(Paragraph(formatted_text, self.styles['CustomBody']))
        
        return elements
    
    def _process_text_formatting(self, text: str) -> str:
        """Process basic text formatting for PDF"""
        import re
        
        # Bold text: **text** -> <b>text</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Italic text: *text* -> <i>text</i>
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        # Code text: `text` -> <font name="Courier">text</font>
        text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
        
        # Bullet points: lines starting with - or *
        lines = text.split('\n')
        formatted_lines = []
        for line in lines:
            if line.strip().startswith(('- ', '* ', '• ')):
                formatted_lines.append('• ' + line.strip()[2:])
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _first_page_template(self, canvas, doc):
        """Template for first page"""
        canvas.saveState()
        
        # Add header
        canvas.setFont('Helvetica-Bold', 12)
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 30, "DocuForge AI")
        
        # Add footer
        canvas.setFont('Helvetica', 9)
        canvas.drawCentredString(doc.width/2 + doc.leftMargin, 30, f"Generated on {datetime.now().strftime('%Y-%m-%d')}")
        
        canvas.restoreState()
    
    def _later_pages_template(self, canvas, doc):
        """Template for later pages"""
        canvas.saveState()
        
        # Add header
        canvas.setFont('Helvetica', 10)
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 30, "DocuForge AI")
        
        # Add footer with page number
        canvas.setFont('Helvetica', 9)
        canvas.drawCentredString(doc.width/2 + doc.leftMargin, 30, f"Page {doc.page}")
        
        canvas.restoreState()
    
    def add_table(self, elements: List, table_data: List[List[str]], headers: List[str] = None, title: str = None):
        """Add a table to the document"""
        if title:
            elements.append(Paragraph(title, self.styles['CustomSubheading']))
        
        # Prepare table data
        data = []
        if headers:
            data.append(headers)
        data.extend(table_data)
        
        # Create table
        table = Table(data, hAlign='LEFT')
        
        # Style the table
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]
        
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(Spacer(1, 12))
        
        return elements
    
    def add_image(self, elements: List, image_path: str, width: Optional[float] = None, caption: str = None):
        """Add an image to the document"""
        try:
            if width:
                img = ImageReader(image_path)
                img_width = width * inch
                img_height = img_width * (img.getSize()[1] / img.getSize()[0])
            else:
                img = ImageReader(image_path)
                img_width = 4 * inch
                img_height = img_width * (img.getSize()[1] / img.getSize()[0])
            
            # Add image
            elements.append(Spacer(1, 12))
            # Note: Direct image insertion in ReportLab requires custom canvas drawing
            # For now, add placeholder
            elements.append(Paragraph(f"[Image: {caption or 'Image'}]", self.styles['Caption']))
            
            # Add caption
            if caption:
                elements.append(Paragraph(f"Figure: {caption}", self.styles['Caption']))
            
            elements.append(Spacer(1, 12))
            
        except Exception as e:
            # Add placeholder if image fails
            elements.append(Paragraph(f"[Image: {caption or 'Image could not be loaded'}]", self.styles['Caption']))
            elements.append(Spacer(1, 12))
        
        return elements
    
    def create_template_document(self, template_type: str, title: str = None) -> bytes:
        """Create a template PDF document based on type"""
        templates = {
            'report': {
                'title': title or 'Research Report',
                'sections': [
                    {'title': 'Executive Summary', 'content': 'Provide a brief overview of the report findings and recommendations.\n\nKey points:\n• Main findings\n• Critical recommendations\n• Strategic implications'},
                    {'title': 'Introduction', 'content': 'Introduce the research topic and objectives.\n\n**Purpose**: Define the purpose and scope of the research.\n\n**Methodology**: Describe the research methods used.\n\n**Scope**: Outline what is and isn\'t covered.'},
                    {'title': 'Literature Review', 'content': 'Review existing research and knowledge on the topic.\n\n**Current State**: What is currently known?\n\n**Gaps**: What questions remain unanswered?\n\n**Relevance**: How does this research fit into the broader context?'},
                    {'title': 'Methodology', 'content': 'Describe the research methods and approach.\n\n**Data Collection**: How was data gathered?\n\n**Analysis**: What analytical methods were used?\n\n**Limitations**: What are the limitations of the approach?'},
                    {'title': 'Findings', 'content': 'Present the key findings from the research.\n\n**Primary Results**: What are the main discoveries?\n\n**Supporting Evidence**: What data supports these findings?\n\n**Unexpected Results**: Were there any surprising outcomes?'},
                    {'title': 'Analysis', 'content': 'Analyze and interpret the findings.\n\n**Implications**: What do these findings mean?\n\n**Patterns**: What patterns or trends emerge?\n\n**Significance**: Why are these findings important?'},
                    {'title': 'Recommendations', 'content': 'Provide actionable recommendations based on the findings.\n\n**Immediate Actions**: What should be done first?\n\n**Long-term Strategy**: What are the strategic implications?\n\n**Implementation**: How should recommendations be executed?'},
                    {'title': 'Conclusion', 'content': 'Summarize the key points and final thoughts.\n\n**Summary**: Recap the main findings and recommendations.\n\n**Future Research**: What additional research is needed?\n\n**Final Thoughts**: Concluding remarks on the significance of the work.'}
                ]
            },
            'whitepaper': {
                'title': title or 'Technical Whitepaper',
                'sections': [
                    {'title': 'Abstract', 'content': 'Brief summary of the whitepaper content and key findings.\n\n**Problem**: What problem does this address?\n\n**Solution**: What solution is proposed?\n\n**Results**: What are the key outcomes?'},
                    {'title': 'Introduction', 'content': 'Introduction to the topic and its significance.\n\n**Background**: Provide context and background information.\n\n**Importance**: Why is this topic important?\n\n**Scope**: What will be covered in this whitepaper?'},
                    {'title': 'Problem Statement', 'content': 'Detailed description of the problem being addressed.\n\n**Current Challenges**: What are the existing problems?\n\n**Impact**: How do these problems affect stakeholders?\n\n**Need for Solution**: Why is a solution urgently needed?'},
                    {'title': 'Technical Approach', 'content': 'Description of the technical solution and methodology.\n\n**Architecture**: How is the solution designed?\n\n**Implementation**: How is it implemented?\n\n**Technical Specifications**: What are the technical details?'},
                    {'title': 'Results and Analysis', 'content': 'Presentation of results and technical analysis.\n\n**Performance Metrics**: How does the solution perform?\n\n**Comparison**: How does it compare to existing solutions?\n\n**Validation**: How were the results validated?'},
                    {'title': 'Use Cases', 'content': 'Real-world applications and use cases.\n\n**Scenario 1**: Describe a primary use case.\n\n**Scenario 2**: Describe a secondary use case.\n\n**Benefits**: What are the benefits in each scenario?'},
                    {'title': 'Future Considerations', 'content': 'Discussion of future developments and considerations.\n\n**Roadmap**: What are the next steps?\n\n**Challenges**: What challenges lie ahead?\n\n**Opportunities**: What opportunities exist?'}
                ]
            },
            'manual': {
                'title': title or 'User Manual',
                'sections': [
                    {'title': 'Getting Started', 'content': 'Introduction and initial setup instructions.\n\n**Welcome**: Welcome to the system.\n\n**System Requirements**: What you need to get started.\n\n**Installation**: How to install or access the system.'},
                    {'title': 'Basic Features', 'content': 'Overview of basic functionality.\n\n**Core Functions**: What are the main features?\n\n**Navigation**: How to navigate the system.\n\n**Common Tasks**: Most frequently used functions.'},
                    {'title': 'Advanced Features', 'content': 'Detailed guide to advanced functionality.\n\n**Advanced Tools**: More sophisticated features.\n\n**Customization**: How to customize the system.\n\n**Integration**: How to integrate with other systems.'},
                    {'title': 'Troubleshooting', 'content': 'Common issues and solutions.\n\n**Common Problems**: Frequently encountered issues.\n\n**Solutions**: Step-by-step solutions.\n\n**When to Contact Support**: When to seek additional help.'},
                    {'title': 'FAQ', 'content': 'Frequently asked questions.\n\n**Q: How do I...?**\nA: Step-by-step instructions.\n\n**Q: What if...?**\nA: Explanation and guidance.\n\n**Q: Where can I find...?**\nA: Location and access information.'},
                    {'title': 'Support', 'content': 'How to get help and support.\n\n**Contact Information**: How to reach support.\n\n**Documentation**: Where to find additional resources.\n\n**Community**: How to connect with other users.'}
                ]
            }
        }
        
        template_data = templates.get(template_type, templates['report'])
        return self.create_document(template_data, {'include_toc': True, 'page_size': 'A4'})