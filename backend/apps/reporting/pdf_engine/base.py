"""
Base PDF utilities and styles for ReportLab
Provides common layout, fonts, and page templates.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.colors import black, white, HexColor
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
from PIL import Image
import os


class PDFStyles:
    """Centralized PDF styles"""
    
    @staticmethod
    def get_styles():
        """Get paragraph styles for PDF documents"""
        styles = getSampleStyleSheet()
        
        # Custom styles
        custom_styles = {
            'title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=black,
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
            ),
            'heading': ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=black,
                spaceAfter=10,
                spaceBefore=12,
                fontName='Helvetica-Bold',
            ),
            'subheading': ParagraphStyle(
                'CustomSubheading',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=black,
                spaceAfter=8,
                spaceBefore=10,
                fontName='Helvetica-Bold',
            ),
            'body': ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=10,
                textColor=black,
                spaceAfter=6,
                fontName='Helvetica',
            ),
            'small': ParagraphStyle(
                'CustomSmall',
                parent=styles['Normal'],
                fontSize=9,
                textColor=black,
                spaceAfter=4,
                fontName='Helvetica',
            ),
            'label': ParagraphStyle(
                'CustomLabel',
                parent=styles['Normal'],
                fontSize=10,
                textColor=black,
                spaceAfter=4,
                fontName='Helvetica-Bold',
            ),
            'footer': ParagraphStyle(
                'CustomFooter',
                parent=styles['Normal'],
                fontSize=8,
                textColor=HexColor('#666666'),
                spaceAfter=0,
                alignment=TA_CENTER,
                fontName='Helvetica-Oblique',
            ),
        }
        
        return {**styles, **custom_styles}


class PDFBase:
    """Base PDF generator with common functionality"""
    
    PAGE_SIZE = A4
    PAGE_WIDTH, PAGE_HEIGHT = A4
    MARGIN_LEFT = 40
    MARGIN_RIGHT = 40
    MARGIN_TOP = 50
    MARGIN_BOTTOM = 50
    
    def __init__(self):
        self.buffer = BytesIO()
        self.styles = PDFStyles.get_styles()
    
    def draw_header(self, canvas_obj, doc, logo_path=None, header_text=None, institution_name=None):
        """Draw header on every page"""
        canvas_obj.saveState()
        
        y = self.PAGE_HEIGHT - 20
        
        # Logo (if provided)
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path)
                logo_width, logo_height = logo.size
                # Scale to max 60mm height
                max_height = 60 * mm
                scale = min(max_height / logo_height, (self.PAGE_WIDTH - 80) / logo_width)
                display_height = logo_height * scale
                display_width = logo_width * scale
                
                canvas_obj.drawImage(
                    ImageReader(logo),
                    self.MARGIN_LEFT,
                    y - display_height,
                    width=display_width,
                    height=display_height,
                    preserveAspectRatio=True
                )
                y -= display_height + 10
            except Exception:
                pass  # Continue without logo if it fails
        
        # Header text / Institution name
        if header_text or institution_name:
            text = header_text or institution_name or "Radiology Information Management System"
            canvas_obj.setFont("Helvetica-Bold", 16)
            text_width = canvas_obj.stringWidth(text, "Helvetica-Bold", 16)
            canvas_obj.drawString(
                (self.PAGE_WIDTH - text_width) / 2,
                y - 20,
                text
            )
            y -= 30
        
        canvas_obj.restoreState()
    
    def draw_footer(self, canvas_obj, doc):
        """Draw footer on every page"""
        canvas_obj.saveState()
        
        # Footer line
        canvas_obj.setStrokeColor(HexColor('#CCCCCC'))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(self.MARGIN_LEFT, 30, self.PAGE_WIDTH - self.MARGIN_RIGHT, 30)
        
        # Footer text
        canvas_obj.setFont("Helvetica-Oblique", 8)
        footer_text = "Computer generated document - RIMS"
        text_width = canvas_obj.stringWidth(footer_text, "Helvetica-Oblique", 8)
        canvas_obj.drawString(
            (self.PAGE_WIDTH - text_width) / 2,
            15,
            footer_text
        )
        
        # Page number
        page_num = canvas_obj.getPageNumber()
        page_text = f"Page {page_num}"
        canvas_obj.drawString(
            self.PAGE_WIDTH - self.MARGIN_RIGHT - 50,
            15,
            page_text
        )
        
        canvas_obj.restoreState()
    
    def create_page_template(self):
        """Create page template with header/footer"""
        def on_page(canvas_obj, doc):
            # Header
            self.draw_header(canvas_obj, doc)
            # Footer
            self.draw_footer(canvas_obj, doc)
        
        frame = Frame(
            self.MARGIN_LEFT,
            self.MARGIN_BOTTOM,
            self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.PAGE_HEIGHT - self.MARGIN_TOP - self.MARGIN_BOTTOM,
            leftPadding=0,
            bottomPadding=0,
            rightPadding=0,
            topPadding=0,
        )
        
        return PageTemplate(id='main', frames=[frame], onPage=on_page)
    
    def create_table_style(self):
        """Create standard table style"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E0E0E0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F5F5F5')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ])
    
    def get_receipt_settings(self):
        """Get receipt settings if available"""
        try:
            from apps.studies.models import ReceiptSettings
            return ReceiptSettings.get_settings()
        except Exception:
            return None
