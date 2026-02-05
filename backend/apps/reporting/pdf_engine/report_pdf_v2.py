"""
V2 PDF generation for JSON schema-based reports.
Generates PDF from ReportInstanceV2 with values_json and narrative_json.
"""
import logging
import os
from io import BytesIO
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import black, HexColor
from reportlab.lib.utils import ImageReader
from django.conf import settings
from django.utils import timezone

from apps.reporting.models import ReportInstanceV2, ReportingOrganizationConfig
from .styles import ReportStyles

logger = logging.getLogger(__name__)

# Constants (reuse from V1)
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_LEFT = 20 * mm
MARGIN_RIGHT = 20 * mm
MARGIN_TOP = 50 * mm
MARGIN_BOTTOM = 30 * mm


class ReportPDFGeneratorV2:
    """PDF generator for V2 reports (JSON schema-based)"""
    
    def __init__(self, report_instance_v2_id, narrative_json=None):
        """
        Initialize V2 PDF generator.
        
        Args:
            report_instance_v2_id: UUID of ReportInstanceV2
            narrative_json: Optional pre-generated narrative (used for publish snapshots)
        """
        self.report_id = report_instance_v2_id
        self.narrative_json = narrative_json
        self.styles = ReportStyles.get_styles()
        self.data = None
        self.buffer = BytesIO()
    
    def fetch_data(self):
        """Fetch report data and prepare for PDF generation"""
        try:
            report = ReportInstanceV2.objects.select_related(
                'work_item',
                'work_item__service',
                'work_item__service_visit',
                'work_item__service_visit__patient',
                'work_item__consultant',
                'work_item__service_visit__booked_consultant',
                'template_v2',
            ).get(id=self.report_id)
        except ReportInstanceV2.DoesNotExist:
            logger.error(f"ReportInstanceV2 {self.report_id} not found")
            raise
        
        item = report.work_item
        visit = item.service_visit
        patient = visit.patient
        service = item.service
        template = report.template_v2
        
        # Consultant logic (same as V1)
        referring_consultant = visit.booked_consultant.name if visit.booked_consultant else (patient.referrer or "Self")
        
        # Dynamic signatory (radiologist)
        radiologist_name = "Dr. Unknown"
        if item.consultant:
            radiologist_name = item.consultant.name
        elif report.created_by:
            radiologist_name = f"Dr. {report.created_by.get_full_name()}"
        
        dynamic_signatories = [
            {"name": radiologist_name, "designation": "Consultant Radiologist"}
        ]
        
        # Config / Branding (reuse V1 logic)
        lab_details = {
            "lab_name": "Adjacent Excel Labs",
            "lab_address": "Near Arman Pan Shop Faisalabad Road Jaranwala",
            "lab_contact": "Tel: 041 4313 777 | WhatsApp: 03279640897",
            "logo_path": str(settings.BASE_DIR / "static" / "branding" / "logo.png"),
            "disclaimer": "Electronically verified. Laboratory results should be interpreted by a physician in correlation with clinical and radiologic findings."
        }
        
        static_signatories = []
        
        # Load config
        config = ReportingOrganizationConfig.objects.first()
        if config:
            lab_details["lab_name"] = config.org_name
            if config.address:
                lab_details["lab_address"] = config.address
            if config.phone:
                lab_details["lab_contact"] = config.phone
            
            if config.logo:
                try:
                    lab_details["logo_path"] = config.logo.path
                except Exception:
                    pass
            
            if config.disclaimer_text:
                lab_details["disclaimer"] = config.disclaimer_text
            
            if config.signatories_json and isinstance(config.signatories_json, list):
                static_signatories = config.signatories_json
        
        final_signatories = dynamic_signatories + static_signatories
        
        self.data = {
            "header": lab_details,
            "patient": {
                "name": patient.name,
                "age_gender": f"{patient.age or '-'} Y / {patient.gender or '-'}",
                "mr_no": patient.mrn,
                "ref_no": visit.visit_id,
                "consultant": referring_consultant
            },
            "study": {
                "service_name": service.name,
                "modality": service.modality.code if service.modality else "RADIOLOGY",
                "study_datetime": item.created_at.strftime("%Y-%m-%d %H:%M"),
                "report_datetime": report.updated_at.strftime("%Y-%m-%d %H:%M")
            },
            "template": {
                "code": template.code,
                "name": template.name,
                "version": template.id,
            },
            "values": report.values_json,
            "json_schema": template.json_schema,
            "narrative": self.narrative_json or {},
            "footer": {
                "disclaimer": lab_details["disclaimer"],
                "signatories": final_signatories
            }
        }
    
    def draw_header(self, canvas, doc):
        """Draw header (reuse V1 logic)"""
        canvas.saveState()
        
        logo_path = self.data['header']['logo_path']
        if os.path.exists(logo_path):
            try:
                img_height = 20 * mm
                logo = ImageReader(logo_path)
                iw, ih = logo.getSize()
                aspect = iw / float(ih)
                final_height = 20 * mm
                final_width = final_height * aspect
                canvas.drawImage(logo, MARGIN_LEFT, PAGE_HEIGHT - 30 * mm, width=final_width, height=final_height, mask='auto')
            except Exception as e:
                logger.error(f"Error drawing logo: {e}")
        
        canvas.setFont("Helvetica-Bold", 16)
        canvas.setFillColor(HexColor('#0B5ED7'))
        canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 20 * mm, self.data['header']['lab_name'])
        
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(HexColor('#666666'))
        canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 25 * mm, self.data['header']['lab_address'])
        canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 30 * mm, self.data['header']['lab_contact'])
        
        canvas.setStrokeColor(HexColor('#CCCCCC'))
        canvas.setLineWidth(1)
        canvas.line(MARGIN_LEFT, PAGE_HEIGHT - 35 * mm, PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - 35 * mm)
        
        canvas.restoreState()
    
    def draw_footer(self, canvas, doc):
        """Draw footer (reuse V1 logic)"""
        canvas.saveState()
        
        disclaimer = self.data['footer']['disclaimer']
        canvas.setFont("Helvetica-Oblique", 7)
        canvas.setFillColor(HexColor('#666666'))
        canvas.drawCentredString(PAGE_WIDTH / 2, 25 * mm, disclaimer)
        
        sigs = self.data['footer']['signatories']
        y_pos = 40 * mm
        for sig in sigs:
            canvas.setFont("Helvetica-Bold", 10)
            canvas.setFillColor(black)
            canvas.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos, sig['name'])
            canvas.setFont("Helvetica", 9)
            canvas.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos - 4*mm, sig['designation'])
            y_pos -= 10*mm
        
        page_num = canvas.getPageNumber()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(black)
        canvas.drawString(PAGE_WIDTH - MARGIN_RIGHT - 10*mm, 15*mm, f"Page {page_num}")
        
        canvas.setStrokeColor(HexColor('#E0E0E0'))
        canvas.line(MARGIN_LEFT, 20*mm, PAGE_WIDTH - MARGIN_RIGHT, 20*mm)
        
        canvas.restoreState()
    
    def build_patient_table(self):
        """Build patient demographics table (reuse V1 logic)"""
        p = self.data['patient']
        s = self.data['study']
        
        data = [
            [
                Paragraph("Patient Name:", self.styles['PatientLabel']),
                Paragraph(p['name'], self.styles['PatientValue']),
                Paragraph("Age / Gender:", self.styles['PatientLabel']),
                Paragraph(p['age_gender'], self.styles['PatientValue']),
            ],
            [
                Paragraph("MR No:", self.styles['PatientLabel']),
                Paragraph(p['mr_no'], self.styles['PatientValue']),
                Paragraph("Ref No:", self.styles['PatientLabel']),
                Paragraph(p['ref_no'], self.styles['PatientValue']),
            ],
            [
                Paragraph("Referred By:", self.styles['PatientLabel']),
                Paragraph(p['consultant'], self.styles['PatientValue']),
                Paragraph("Report Date:", self.styles['PatientLabel']),
                Paragraph(s['report_datetime'], self.styles['PatientValue']),
            ]
        ]
        
        avail_width = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
        col_width = avail_width / 4
        
        t = Table(data, colWidths=[col_width]*4)
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, HexColor('#EEEEEE')),
            ('BACKGROUND', (0,0), (-1,-1), HexColor('#FAFAFA')),
        ]))
        return t
    
    def build_values_table(self):
        """Build table of values from values_json"""
        values = self.data['values']
        json_schema = self.data['json_schema']
        properties = json_schema.get('properties', {})
        
        # Build table data: [Label, Value]
        table_data = []
        for field_name, value in values.items():
            # Get label from schema
            field_schema = properties.get(field_name, {})
            label = field_schema.get('title', field_name)
            
            # Format value
            formatted_value = self._format_value_for_display(value, field_schema)
            
            if formatted_value:  # Only include non-empty values
                table_data.append([
                    Paragraph(f"<b>{label}:</b>", self.styles['BodyText']),
                    Paragraph(formatted_value, self.styles['BodyText']),
                ])
        
        if not table_data:
            return None
        
        avail_width = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
        t = Table(table_data, colWidths=[avail_width * 0.4, avail_width * 0.6])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        return t
    
    def _format_value_for_display(self, value, field_schema):
        """Format a value for display in PDF"""
        if value is None or value == "":
            return ""
        
        field_type = field_schema.get('type')
        
        # Boolean
        if field_type == 'boolean':
            if isinstance(value, bool):
                return "Yes" if value else "No"
            return str(value)
        
        # Array (multiple selections)
        if isinstance(value, list):
            if not value:
                return ""
            return ", ".join(str(v) for v in value)
        
        # Default
        return str(value)
    
    def generate(self) -> bytes:
        """Generate PDF and return bytes"""
        self.fetch_data()
        
        doc = BaseDocTemplate(
            self.buffer,
            pagesize=A4,
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            topMargin=MARGIN_TOP,
            bottomMargin=MARGIN_BOTTOM
        )
        
        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id='normal'
        )
        
        template = PageTemplate(id='report', frames=frame, onPage=self.draw_header, onPageEnd=self.draw_footer)
        doc.addPageTemplates([template])
        
        story = []
        
        # Title
        title_text = f"{self.data['study']['service_name']} REPORT"
        story.append(Paragraph(title_text, self.styles['ReportTitle']))
        story.append(Spacer(1, 10))
        
        # Patient table
        story.append(self.build_patient_table())
        story.append(Spacer(1, 15))
        
        # Render narrative if available
        narrative = self.data.get('narrative', {})
        if narrative:
            self._render_narrative(story, narrative)
        else:
            # Fallback: render values as table
            story.append(Paragraph("REPORT VALUES", self.styles['SectionHeading']))
            story.append(Spacer(1, 5))
            values_table = self.build_values_table()
            if values_table:
                story.append(values_table)
        
        doc.build(story)
        
        pdf_bytes = self.buffer.getvalue()
        self.buffer.close()
        return pdf_bytes
    
    def _render_narrative(self, story, narrative):
        """Render narrative sections into story"""
        # Render sections
        sections = narrative.get('sections', [])
        for section in sections:
            title = section.get('title', '')
            lines = section.get('lines', [])
            
            if title:
                story.append(Paragraph(title.upper(), self.styles['SectionHeading']))
            
            for line in lines:
                story.append(Paragraph(line, self.styles['BodyText']))
            
            story.append(Spacer(1, 10))
        
        # Render impression
        impression_lines = narrative.get('impression', [])
        if impression_lines:
            story.append(Paragraph("IMPRESSION", self.styles['SectionHeading']))
            for line in impression_lines:
                story.append(Paragraph(line, self.styles['BodyText']))


def generate_report_pdf_v2(report_instance_v2_id, narrative_json=None) -> bytes:
    """
    Generate V2 PDF for a report instance.
    
    Args:
        report_instance_v2_id: UUID of ReportInstanceV2
        narrative_json: Optional pre-generated narrative
    
    Returns:
        PDF bytes
    """
    generator = ReportPDFGeneratorV2(report_instance_v2_id, narrative_json)
    return generator.generate()
