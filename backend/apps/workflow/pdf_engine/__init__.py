"""
ReportLab PDF Engine for RIMS
All PDF generation uses ReportLab for deterministic, print-safe output.
"""

from .base import PDFBase, PDFStyles
from .receipt import build_receipt_pdf_reportlab
from .prescription import build_prescription_pdf

__all__ = [
    'PDFBase',
    'PDFStyles',
    'build_receipt_pdf_reportlab',
    'build_prescription_pdf',
]

