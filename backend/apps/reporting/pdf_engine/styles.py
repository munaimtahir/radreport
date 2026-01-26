from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.colors import black, HexColor

class ReportStyles:
    @staticmethod
    def get_styles():
        base_styles = getSampleStyleSheet()
        
        custom_styles = {
            'ReportTitle': ParagraphStyle(
                'ReportTitle',
                parent=base_styles['Heading1'],
                fontSize=16,
                textColor=HexColor('#0B5ED7'),  # Clinic Blue
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
            ),
            'SectionHeading': ParagraphStyle(
                'SectionHeading',
                parent=base_styles['Heading2'],
                fontSize=12,
                textColor=HexColor('#0B5ED7'),
                spaceAfter=6,
                spaceBefore=12,
                fontName='Helvetica-Bold',
                keepWithNext=True,
            ),
            'BodyText': ParagraphStyle(
                'BodyText',
                parent=base_styles['Normal'],
                fontSize=10,
                leading=14,
                textColor=black,
                spaceAfter=8,
                fontName='Helvetica',
                alignment=TA_JUSTIFY,
            ),
            'PatientLabel': ParagraphStyle(
                'PatientLabel',
                parent=base_styles['Normal'],
                fontSize=9,
                textColor=HexColor('#666666'),
                fontName='Helvetica-Bold',
            ),
            'PatientValue': ParagraphStyle(
                'PatientValue',
                parent=base_styles['Normal'],
                fontSize=9,
                textColor=black,
                fontName='Helvetica',
            ),
            'FooterText': ParagraphStyle(
                'FooterText',
                parent=base_styles['Normal'],
                fontSize=8,
                textColor=HexColor('#666666'),
                alignment=TA_CENTER,
                fontName='Helvetica-Oblique',
            ),
             'Disclaimer': ParagraphStyle(
                'Disclaimer',
                parent=base_styles['Normal'],
                fontSize=7,
                textColor=HexColor('#666666'),
                alignment=TA_CENTER,
                fontName='Helvetica',
                spaceBefore=4,
            ),
        }
        
        styles_dict = {name: base_styles.byName[name] for name in base_styles.byName}
        return {**styles_dict, **custom_styles}
