import logging
import os
from io import BytesIO
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import black, white, HexColor
from reportlab.lib.utils import ImageReader
from django.conf import settings
from django.utils import timezone

from apps.reporting.models import ReportInstance, PrintingConfig
from .styles import ReportStyles

logger = logging.getLogger(__name__)

# Constants
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_LEFT = 20 * mm
MARGIN_RIGHT = 20 * mm
MARGIN_TOP = 50 * mm  # Space for Header
MARGIN_BOTTOM = 30 * mm # Space for Footer

class ReportPDFGenerator:
    def __init__(self, report_instance_id):
        self.report_id = report_instance_id
        self.styles = ReportStyles.get_styles()
        self.data = None
        self.buffer = BytesIO()

    def fetch_data(self):
        try:
            report = ReportInstance.objects.select_related(
                'service_visit_item',
                'service_visit_item__service',
                'service_visit_item__service_visit',
                'service_visit_item__service_visit__patient',
                'service_visit_item__consultant', # Performing consultant
                'service_visit_item__service_visit__booked_consultant', # Referring/Booked
            ).get(id=self.report_id)
        except ReportInstance.DoesNotExist:
            logger.error(f"ReportInstance {self.report_id} not found")
            raise

        item = report.service_visit_item
        visit = item.service_visit
        patient = visit.patient
        service = item.service

        # Consultant Logic
        referring_consultant = visit.booked_consultant.name if visit.booked_consultant else (patient.referrer or "Self")
        
        # Dynamic Signatory (Radiologist)
        radiologist_name = "Dr. Unknown"
        if item.consultant:
             radiologist_name = item.consultant.name
        elif report.created_by:
             radiologist_name = f"Dr. {report.created_by.get_full_name()}"
        
        dynamic_signatories = [
            {"name": radiologist_name, "designation": "Consultant Radiologist"}
        ]

        # Config / Branding Logic
        org_details = {
             "lab_name": "Adjacent Excel Labs",
             "lab_address": "Near Arman Pan Shop Faisalabad Road Jaranwala",
             "lab_contact": "Tel: 041 4313 777 | WhatsApp: 03279640897",
            "logo_path": str(settings.BASE_DIR / "static" / "branding" / "logo.png"),
            "disclaimer": "Electronically verified. Results should be interpreted by a physician in correlation with clinical and radiologic findings."
        }
        
        static_signatories = []

        # Load Config
        config = PrintingConfig.get()
        if config:
            org_details["lab_name"] = config.org_name
            if config.address:
                org_details["lab_address"] = config.address
            if config.phone:
                org_details["lab_contact"] = config.phone

            # Handle Logo
            if config.report_logo:
                try:
                    org_details["logo_path"] = config.report_logo.path
                except Exception:
                    pass

            if config.disclaimer_text:
                org_details["disclaimer"] = config.disclaimer_text

            if config.signatories_json and isinstance(config.signatories_json, list):
                static_signatories = config.signatories_json

        # Final Signatories: Static (e.g. HOD) + Dynamic (Radiologist) ? 
        # Usually Dynamic is most important. We'll append Static ones if any.
        final_signatories = dynamic_signatories + static_signatories

        self.data = {
            "header": org_details,
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
            "body": {
                "findings": report.findings_text or "No findings recorded.",
                "impression": report.impression_text,
                "limitations": report.limitations_text
            },
            "footer": {
                "disclaimer": org_details["disclaimer"],
                "signatories": final_signatories
            }
        }
        
    def draw_header(self, canvas, doc):
        canvas.saveState()
        
        # Logo
        logo_path = self.data['header']['logo_path']
        if os.path.exists(logo_path):
            try:
                # height 20mm
                img_height = 20 * mm
                img_width = 20 * mm # Aspect ratio placeholder, logic below handles fit
                
                logo = ImageReader(logo_path)
                iw, ih = logo.getSize()
                aspect = iw / float(ih)
                
                final_height = 20 * mm
                final_width = final_height * aspect
                
                # Draw logo at top left inside margins
                canvas.drawImage(logo, MARGIN_LEFT, PAGE_HEIGHT - 30 * mm, width=final_width, height=final_height, mask='auto')
            except Exception as e:
                logger.error(f"Error drawing logo: {e}")

        # Organization details - centered/right or just text next to logo
        # Matching Receipt style: Center text
        # But for Report, usually Logo Left, Text Center/Right.
        # Let's put organization name centered at top
        
        canvas.setFont("Helvetica-Bold", 16)
        canvas.setFillColor(HexColor('#0B5ED7'))
        canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 20 * mm, self.data['header']['lab_name'])
        
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(HexColor('#666666'))
        canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 25 * mm, self.data['header']['lab_address'])
        canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 30 * mm, self.data['header']['lab_contact'])
        
        # Divider Line
        canvas.setStrokeColor(HexColor('#CCCCCC'))
        canvas.setLineWidth(1)
        canvas.line(MARGIN_LEFT, PAGE_HEIGHT - 35 * mm, PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - 35 * mm)
        
        canvas.restoreState()

    def draw_footer(self, canvas, doc):
        canvas.saveState()
        
        # Disclaimer
        disclaimer = self.data['footer']['disclaimer']
        canvas.setFont("Helvetica-Oblique", 7)
        canvas.setFillColor(HexColor('#666666'))
        canvas.drawCentredString(PAGE_WIDTH / 2, 25 * mm, disclaimer)
        
        # Signatories
        sigs = self.data['footer']['signatories']
        # Draw on right side
        y_pos = 40 * mm
        for sig in sigs:
            canvas.setFont("Helvetica-Bold", 10)
            canvas.setFillColor(black)
            canvas.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos, sig['name'])
            canvas.setFont("Helvetica", 9)
            canvas.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y_pos - 4*mm, sig['designation'])
            y_pos -= 10*mm # Stack if multiple (though code assumes 1 usually)

        # Page Number
        page_num = canvas.getPageNumber()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(black)
        canvas.drawString(PAGE_WIDTH - MARGIN_RIGHT - 10*mm, 15*mm, f"Page {page_num}")
        
        # Bottom Line
        canvas.setStrokeColor(HexColor('#E0E0E0'))
        canvas.line(MARGIN_LEFT, 20*mm, PAGE_WIDTH - MARGIN_RIGHT, 20*mm)

        canvas.restoreState()

    def build_patient_table(self):
        # 2 Columns: Label | Value || Label | Value
        p = self.data['patient']
        s = self.data['study']
        
        # Construct simplified layout:
        # P_Name | P_Age/Gender
        # P_MRN  | P_RefNo (VisitID)
        # Ref_By | Study_Date
        
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
        
        # Column widths
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

    def generate(self) -> bytes:
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
        
        # Title: Service Name Report
        title_text = f"{self.data['study']['service_name']} REPORT"
        story.append(Paragraph(title_text, self.styles['ReportTitle']))
        story.append(Spacer(1, 10))
        
        # Patient Table
        story.append(self.build_patient_table())
        story.append(Spacer(1, 15))
        
        # Findings
        story.append(Paragraph("FINDINGS", self.styles['SectionHeading']))
        # Split text by newlines and create paragraphs to preserve some formatting
        findings_text = self.data['body']['findings']
        for para in findings_text.split('\n'):
            if para.strip():
                story.append(Paragraph(para, self.styles['BodyText']))
        
        # Impression
        if self.data['body']['impression']:
            story.append(Spacer(1, 10))
            story.append(Paragraph("IMPRESSION", self.styles['SectionHeading']))
            for para in self.data['body']['impression'].split('\n'):
                if para.strip():
                    story.append(Paragraph(para, self.styles['BodyText']))
                    
        # Limitations
        if self.data['body']['limitations']:
            story.append(Spacer(1, 10))
            story.append(Paragraph("LIMITATIONS", self.styles['SectionHeading']))
            for para in self.data['body']['limitations'].split('\n'):
                if para.strip():
                    story.append(Paragraph(para, self.styles['BodyText']))

        doc.build(story)
        
        pdf_bytes = self.buffer.getvalue()
        self.buffer.close()
        return pdf_bytes

def generate_report_pdf(report_instance_id) -> bytes:
    generator = ReportPDFGenerator(report_instance_id)
    return generator.generate()
