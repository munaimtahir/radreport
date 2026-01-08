"""
ReportLab PDF Engine for RIMS
All PDF generation uses ReportLab for deterministic, print-safe output.
"""

from .base import PDFBase, PDFStyles
from .receipt import build_receipt_pdf_reportlab
from .clinical_report import build_clinical_report_pdf
from .prescription import build_prescription_pdf

__all__ = [
    'PDFBase',
    'PDFStyles',
    'build_receipt_pdf_reportlab',
    'build_clinical_report_pdf',
    'build_prescription_pdf',
]
