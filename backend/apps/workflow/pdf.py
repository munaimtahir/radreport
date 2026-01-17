"""
PDF generation for workflow (receipts, USG reports, OPD prescriptions)
All PDFs generated using ReportLab for deterministic output.
"""
from django.core.files.base import ContentFile
from apps.reporting.pdf_engine.receipt import (
    build_service_visit_receipt_pdf_reportlab,
    build_receipt_snapshot_pdf,
)
from apps.reporting.pdf_engine.clinical_report import build_clinical_report_pdf
from apps.reporting.pdf_engine.prescription import build_prescription_pdf


def build_service_visit_receipt_pdf(service_visit, invoice):
    """Generate receipt PDF for service visit using ReportLab"""
    return build_service_visit_receipt_pdf_reportlab(service_visit, invoice)


def build_receipt_pdf_from_snapshot(snapshot):
    """Generate receipt PDF from immutable snapshot data."""
    return build_receipt_snapshot_pdf(snapshot)


def build_usg_report_pdf(usg_report):
    """Generate USG report PDF using ReportLab"""
    return build_clinical_report_pdf(usg_report)


def build_opd_prescription_pdf(opd_consult):
    """Generate OPD prescription PDF using ReportLab"""
    return build_prescription_pdf(opd_consult)
