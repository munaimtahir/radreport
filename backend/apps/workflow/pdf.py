"""
PDF generation for workflow (receipts, USG reports, OPD prescriptions)
"""
from io import BytesIO
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML, CSS
import os
from pathlib import Path


def build_service_visit_receipt_pdf(service_visit, invoice):
    """Generate receipt PDF for service visit"""
    from apps.studies.models import ReceiptSequence
    
    # Get receipt number (format: yymm-001)
    receipt_number = ReceiptSequence.get_next_receipt_number()
    
    # Get payment
    payment = service_visit.payments.first()
    
    context = {
        'receipt_number': receipt_number,
        'receipt_date': service_visit.registered_at,
        'patient': {
            'patient_reg_no': service_visit.patient.patient_reg_no or service_visit.patient.mrn,
            'mrn': service_visit.patient.mrn,
            'name': service_visit.patient.name,
            'age': service_visit.patient.age,
            'gender': service_visit.patient.gender,
            'phone': service_visit.patient.phone,
        },
        'visit_id': service_visit.visit_id,
        'service': {
            'name': service_visit.service.name,
            'code': service_visit.service.code,
        },
        'total_amount': invoice.total_amount,
        'discount': invoice.discount,
        'net_amount': invoice.net_amount,
        'paid_amount': payment.amount_paid if payment else invoice.net_amount,
        'balance_amount': invoice.balance_amount,
        'payment_method': payment.method if payment else 'cash',
        'cashier_name': payment.received_by.username if payment and payment.received_by else 'N/A',
    }
    
    # Render HTML template
    html_string = render_to_string('workflow/receipt.html', context)
    
    # Generate PDF using WeasyPrint
    css = CSS(string='''
        @page {
            size: A4 portrait;
            margin: 15mm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 10pt;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .receipt-info {
            margin-bottom: 15px;
        }
        .patient-info, .service-info {
            margin-bottom: 10px;
        }
        .amounts {
            margin-top: 20px;
            border-top: 1px solid #000;
            padding-top: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        td {
            padding: 5px;
        }
        .label {
            font-weight: bold;
        }
    ''')
    
    html = HTML(string=html_string)
    pdf_bytes = html.write_pdf(stylesheets=[css])
    
    return ContentFile(pdf_bytes, name=f"receipt_{receipt_number}.pdf")


def build_usg_report_pdf(usg_report):
    """Generate USG report PDF"""
    service_visit = usg_report.service_visit
    
    context = {
        'visit_id': service_visit.visit_id,
        'patient': {
            'patient_reg_no': service_visit.patient.patient_reg_no or service_visit.patient.mrn,
            'name': service_visit.patient.name,
            'age': service_visit.patient.age,
            'gender': service_visit.patient.gender,
        },
        'service': {
            'name': service_visit.service.name,
            'code': service_visit.service.code,
        },
        'report_data': usg_report.report_json,
        'created_by': usg_report.created_by.username if usg_report.created_by else 'N/A',
        'verified_by': usg_report.verifier.username if usg_report.verifier else None,
        'verified_at': usg_report.verified_at,
    }
    
    # Render HTML template
    html_string = render_to_string('workflow/usg_report.html', context)
    
    # Generate PDF
    css = CSS(string='''
        @page {
            size: A4 portrait;
            margin: 20mm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 11pt;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .patient-info {
            margin-bottom: 15px;
        }
        .findings, .impression {
            margin-top: 20px;
        }
        .signature {
            margin-top: 40px;
        }
    ''')
    
    html = HTML(string=html_string)
    pdf_bytes = html.write_pdf(stylesheets=[css])
    
    return ContentFile(pdf_bytes, name=f"usg_report_{service_visit.visit_id}.pdf")


def build_opd_prescription_pdf(opd_consult):
    """Generate OPD prescription PDF"""
    service_visit = opd_consult.service_visit
    
    context = {
        'visit_id': service_visit.visit_id,
        'patient': {
            'patient_reg_no': service_visit.patient.patient_reg_no or service_visit.patient.mrn,
            'name': service_visit.patient.name,
            'age': service_visit.patient.age,
            'gender': service_visit.patient.gender,
        },
        'diagnosis': opd_consult.diagnosis,
        'medicines': opd_consult.medicines_json if isinstance(opd_consult.medicines_json, list) else [],
        'investigations': opd_consult.investigations_json if isinstance(opd_consult.investigations_json, list) else [],
        'advice': opd_consult.advice,
        'followup': opd_consult.followup,
        'consultant': opd_consult.consultant.username if opd_consult.consultant else 'N/A',
        'consult_date': opd_consult.consult_at,
    }
    
    # Render HTML template
    html_string = render_to_string('workflow/opd_prescription.html', context)
    
    # Generate PDF
    css = CSS(string='''
        @page {
            size: A4 portrait;
            margin: 20mm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 11pt;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .patient-info {
            margin-bottom: 15px;
        }
        .section {
            margin-top: 15px;
        }
        .medicines-table, .investigations-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .medicines-table td, .investigations-table td {
            padding: 5px;
            border-bottom: 1px solid #ddd;
        }
        .signature {
            margin-top: 40px;
        }
    ''')
    
    html = HTML(string=html_string)
    pdf_bytes = html.write_pdf(stylesheets=[css])
    
    return ContentFile(pdf_bytes, name=f"prescription_{service_visit.visit_id}.pdf")
