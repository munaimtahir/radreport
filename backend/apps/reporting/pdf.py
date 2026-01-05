from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from django.core.files.base import ContentFile

def build_basic_pdf(report) -> ContentFile:
    """Basic PDF generator stub.
    Replace with your branded layout later (header, footer, signatory, QR, etc.)
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Radiology Report")
    y -= 25

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Accession: {report.study.accession}")
    y -= 14
    c.drawString(40, y, f"Patient: {report.study.patient.name} | MRN: {report.study.patient.mrn}")
    y -= 14
    c.drawString(40, y, f"Service: {report.study.service.name} ({report.study.service.modality.code})")
    y -= 20

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Findings")
    y -= 14
    c.setFont("Helvetica", 10)
    for line in (report.narrative or "").splitlines()[:40]:
        c.drawString(40, y, line[:110])
        y -= 12
        if y < 80:
            c.showPage()
            y = height - 50

    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Impression")
    y -= 14
    c.setFont("Helvetica", 10)
    for line in (report.impression or "").splitlines()[:20]:
        c.drawString(40, y, line[:110])
        y -= 12
        if y < 80:
            c.showPage()
            y = height - 50

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return ContentFile(pdf_bytes, name=f"{report.study.accession}.pdf")
