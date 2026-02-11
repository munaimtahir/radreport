"""
V2 PDF generation for JSON schema-based reports.
Radiology Master Report Layout v1.0 (A4 print-first, modality-agnostic).
"""

import logging
import os
from io import BytesIO

from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from apps.reporting.models import ReportInstanceV2, ReportingOrganizationConfig

logger = logging.getLogger(__name__)

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_LEFT = 18 * mm
MARGIN_RIGHT = 18 * mm
MARGIN_TOP = 20 * mm
MARGIN_BOTTOM = 20 * mm
HEADER_HEIGHT = 33 * mm
FOOTER_RESERVED = 12 * mm

DIVIDER = HexColor("#cfcfcf")
LIGHT_BG = HexColor("#f7f7f7")
SOFT_BG = HexColor("#f1f1f1")


class ReportPDFGeneratorV2:
    """A4 print-first report generator for all radiology modalities."""

    def __init__(self, report_instance_v2_id, narrative_json=None):
        self.report_id = report_instance_v2_id
        self.input_narrative_json = narrative_json or {}
        self.buffer = BytesIO()
        self.data = None
        self.styles = self._build_styles()

    def _build_styles(self):
        base = getSampleStyleSheet()
        return {
            "title": ParagraphStyle(
                "rm_title",
                parent=base["Normal"],
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=16,
                alignment=1,
                textColor=colors.black,
                spaceAfter=8,
            ),
            "section_title": ParagraphStyle(
                "rm_section_title",
                parent=base["Normal"],
                fontName="Helvetica-Bold",
                fontSize=12.2,
                leading=14,
                textColor=colors.black,
                spaceBefore=8,
                spaceAfter=5,
            ),
            "subheading": ParagraphStyle(
                "rm_subheading",
                parent=base["Normal"],
                fontName="Helvetica-Bold",
                fontSize=11,
                leading=13,
                textColor=colors.black,
                spaceBefore=5,
                spaceAfter=3,
            ),
            "body": ParagraphStyle(
                "rm_body",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=11,
                leading=14,
                textColor=colors.black,
                spaceAfter=4,
            ),
            "label": ParagraphStyle(
                "rm_label",
                parent=base["Normal"],
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=12,
                textColor=colors.black,
            ),
            "value": ParagraphStyle(
                "rm_value",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=10.5,
                leading=12,
                textColor=colors.black,
            ),
            "footer": ParagraphStyle(
                "rm_footer",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=8.8,
                leading=11,
                textColor=HexColor("#555555"),
                alignment=1,
            ),
            "header_center_strong": ParagraphStyle(
                "rm_header_center_strong",
                parent=base["Normal"],
                fontName="Helvetica-Bold",
                fontSize=11,
                leading=12,
                alignment=1,
                textColor=colors.black,
            ),
            "header_center": ParagraphStyle(
                "rm_header_center",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=9.5,
                leading=11,
                alignment=1,
                textColor=colors.black,
            ),
            "header_right": ParagraphStyle(
                "rm_header_right",
                parent=base["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=11,
                alignment=2,
                textColor=colors.black,
            ),
        }

    def _listify(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        text = str(value).strip()
        return [text] if text else []

    def fetch_data(self):
        try:
            report = ReportInstanceV2.objects.select_related(
                "work_item",
                "work_item__service",
                "work_item__service_visit",
                "work_item__service_visit__patient",
                "work_item__consultant",
                "template_v2",
                "created_by",
            ).get(id=self.report_id)
        except ReportInstanceV2.DoesNotExist:
            logger.error("ReportInstanceV2 %s not found", self.report_id)
            raise

        item = report.work_item
        visit = item.service_visit
        patient = visit.patient

        config = ReportingOrganizationConfig.objects.first()
        center_lines = []
        logo_path = ""
        disclaimer = "This report is based on imaging findings at the time of examination. Clinical correlation is advised."
        static_signatories = []

        if config:
            if config.org_name:
                center_lines.append(config.org_name.strip())
            if config.address:
                center_lines.append(str(config.address).strip())
            if config.phone:
                center_lines.append(str(config.phone).strip())
            if config.logo:
                try:
                    logo_path = config.logo.path
                except Exception:
                    logo_path = ""
            if config.disclaimer_text:
                disclaimer = config.disclaimer_text
            if isinstance(config.signatories_json, list):
                static_signatories = config.signatories_json

        narrative = self.input_narrative_json or report.narrative_json or {}

        findings = []
        for block in narrative.get("sections", []) if isinstance(narrative, dict) else []:
            if not isinstance(block, dict):
                continue
            lines = self._listify(block.get("lines"))
            if lines:
                findings.append({"heading": str(block.get("title", "")).strip(), "lines": lines})

        if not findings:
            fallback_lines = []
            for key, value in (report.values_json or {}).items():
                text = str(value).strip()
                if text:
                    fallback_lines.append(f"{key.replace('_', ' ').title()}: {text}")
            if fallback_lines:
                findings.append({"heading": "", "lines": fallback_lines})

        measurements = []
        for key, value in (report.values_json or {}).items():
            if isinstance(value, (int, float)):
                measurements.append({"label": key.replace("_", " ").title(), "value": str(value), "unit": ""})
            elif isinstance(value, str):
                low = key.lower()
                if ("measurement" in low or "size" in low or "diameter" in low) and value.strip():
                    measurements.append({"label": key.replace("_", " ").title(), "value": value.strip(), "unit": ""})
        measurements = measurements[:12]

        clinical_indication = ""
        for key, value in (report.values_json or {}).items():
            low = key.lower()
            if "clinical" in low or "history" in low or "indication" in low:
                text = str(value).strip()
                if text:
                    clinical_indication = text
                    break

        signatories = []
        right_lines = []
        if item.consultant:
            signatories.append(
                {
                    "verification_label": "Electronically Verified",
                    "name": item.consultant.display_name,
                    "credentials": item.consultant.degrees,
                    "registration": "",
                }
            )
            right_lines = [
                x
                for x in [
                    item.consultant.display_name,
                    item.consultant.degrees,
                    item.consultant.designation,
                    item.consultant.mobile_number,
                ]
                if x
            ]
        elif report.created_by:
            name = report.created_by.get_full_name() or report.created_by.username
            signatories.append(
                {
                    "verification_label": "Electronically Verified",
                    "name": name,
                    "credentials": "",
                    "registration": "",
                }
            )
            right_lines = [name]

        for raw in static_signatories:
            if not isinstance(raw, dict):
                continue
            nm = str(raw.get("name", "")).strip()
            ds = str(raw.get("designation", "")).strip()
            if nm or ds:
                signatories.append(
                    {
                        "verification_label": "Electronically Verified",
                        "name": nm,
                        "credentials": ds,
                        "registration": str(raw.get("registration", "")).strip(),
                    }
                )

        self.data = {
            "header": {
                "logo_path": logo_path,
                "center_lines": center_lines,
                "right_lines": right_lines,
            },
            "patient": {
                "name": patient.name,
                "age": str(patient.age or ""),
                "sex": patient.gender or "",
                "mrn": patient.patient_reg_no or patient.mrn,
                "mobile": patient.phone or "",
                "ref_no": visit.visit_id,
                "referred_by": visit.referring_consultant or patient.referrer or "",
                "study_datetime": item.created_at.strftime("%Y-%m-%d %H:%M"),
                "report_datetime": report.updated_at.strftime("%Y-%m-%d %H:%M"),
                "clinical_indication": clinical_indication,
            },
            "report_title": (report.template_v2.name or item.service.name or "Radiology Report").upper(),
            "sections": {
                "technique": self._listify(narrative.get("technique")) if isinstance(narrative, dict) else [],
                "comparison": self._listify(narrative.get("comparison")) if isinstance(narrative, dict) else [],
                "findings": findings,
                "measurements": measurements,
                "impression": self._listify(narrative.get("impression")) if isinstance(narrative, dict) else [],
                "recommendations": self._listify(narrative.get("recommendations")) if isinstance(narrative, dict) else [],
            },
            "signatories": signatories,
            "footer": {"disclaimer": disclaimer},
        }

    def draw_header(self, canvas, doc):
        canvas.saveState()

        left_x = MARGIN_LEFT
        top_y = PAGE_HEIGHT - MARGIN_TOP
        bottom_y = top_y - HEADER_HEIGHT

        logo_path = self.data["header"].get("logo_path")
        if logo_path and os.path.exists(logo_path):
            try:
                logo = ImageReader(logo_path)
                iw, ih = logo.getSize()
                max_w = 28 * mm
                max_h = 18 * mm
                ratio = min(max_w / float(iw), max_h / float(ih))
                w = iw * ratio
                h = ih * ratio
                canvas.drawImage(logo, left_x, top_y - h, width=w, height=h, preserveAspectRatio=True, mask="auto")
            except Exception as exc:
                logger.warning("Failed to draw logo: %s", exc)

        center_lines = self.data["header"].get("center_lines", [])
        center_x = PAGE_WIDTH / 2
        center_y = top_y - 4 * mm
        if center_lines:
            for idx, line in enumerate(center_lines[:4]):
                style = self.styles["header_center_strong"] if idx == 0 else self.styles["header_center"]
                p = Paragraph(line, style)
                w, h = p.wrap(90 * mm, 12 * mm)
                p.drawOn(canvas, center_x - w / 2, center_y - h)
                center_y -= h

        right_lines = self.data["header"].get("right_lines", [])
        right_x = PAGE_WIDTH - MARGIN_RIGHT
        right_y = top_y - 2 * mm
        for line in right_lines[:5]:
            p = Paragraph(line, self.styles["header_right"])
            w, h = p.wrap(65 * mm, 9 * mm)
            p.drawOn(canvas, right_x - w, right_y - h)
            right_y -= h

        canvas.setStrokeColor(DIVIDER)
        canvas.setLineWidth(0.8)
        canvas.line(MARGIN_LEFT, bottom_y, PAGE_WIDTH - MARGIN_RIGHT, bottom_y)

        canvas.restoreState()

    def draw_footer(self, canvas, doc):
        canvas.saveState()
        y = MARGIN_BOTTOM - 2 * mm
        canvas.setStrokeColor(DIVIDER)
        canvas.setLineWidth(0.7)
        canvas.line(MARGIN_LEFT, y + 8 * mm, PAGE_WIDTH - MARGIN_RIGHT, y + 8 * mm)

        footer_text = self.data.get("footer", {}).get("disclaimer", "")
        p = Paragraph(footer_text, self.styles["footer"])
        w, h = p.wrap(PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT, 10 * mm)
        p.drawOn(canvas, MARGIN_LEFT, y + 2 * mm)

        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, y - 1 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    def _patient_table(self):
        p = self.data["patient"]
        age_sex = " / ".join([x for x in [p.get("age"), p.get("sex")] if x])

        left = [
            ("Patient Name", p.get("name", "")),
            ("Age / Sex", age_sex),
            ("MRN / Patient ID", p.get("mrn", "")),
            ("Mobile", p.get("mobile", "")),
        ]
        right = [
            ("Ref No / Accession", p.get("ref_no", "")),
            ("Referred By", p.get("referred_by", "")),
            ("Study Date/Time", p.get("study_datetime", "")),
            ("Report Date/Time", p.get("report_datetime", "")),
        ]

        rows = []
        max_rows = max(len(left), len(right))
        for i in range(max_rows):
            l_label, l_val = left[i] if i < len(left) else ("", "")
            r_label, r_val = right[i] if i < len(right) else ("", "")
            rows.append(
                [
                    Paragraph(l_label if l_val else "", self.styles["label"]),
                    Paragraph(str(l_val) if l_val else "", self.styles["value"]),
                    Paragraph(r_label if r_val else "", self.styles["label"]),
                    Paragraph(str(r_val) if r_val else "", self.styles["value"]),
                ]
            )

        avail = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
        table = Table(rows, colWidths=[27 * mm, (avail / 2) - 27 * mm, 30 * mm, (avail / 2) - 30 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                    ("BOX", (0, 0), (-1, -1), 0.6, HexColor("#e1e1e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.2, HexColor("#efefef")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        flow = [table]
        indication = p.get("clinical_indication", "")
        if indication:
            flow.append(Spacer(1, 4))
            flow.append(Paragraph(f"<b>Clinical Indication:</b> {indication}", self.styles["value"]))
        return KeepTogether(flow)

    def _section_heading(self, text):
        return KeepTogether(
            [
                Paragraph(text, self.styles["section_title"]),
                Table([[
                    ""
                ]], colWidths=[PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT], rowHeights=[0.6], style=TableStyle([
                    ("LINEABOVE", (0, 0), (0, 0), 0.6, HexColor("#dedede")),
                ])),
                Spacer(1, 3),
            ]
        )

    def _render_lines(self, lines):
        out = []
        for line in lines:
            out.append(Paragraph(line, self.styles["body"]))
        return out

    def _render_measurements(self, measurements):
        rows = [[Paragraph("<b>Parameter</b>", self.styles["value"]), Paragraph("<b>Value</b>", self.styles["value"])]]
        for m in measurements:
            value = f"{m.get('value', '')} {m.get('unit', '')}".strip()
            rows.append([Paragraph(str(m.get("label", "")), self.styles["value"]), Paragraph(value, self.styles["value"])])
        t = Table(rows, colWidths=[(PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT) * 0.52, (PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT) * 0.48])
        t.setStyle(
            TableStyle(
                [
                    ("LINEBELOW", (0, 0), (-1, -1), 0.4, HexColor("#e4e4e4")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return t

    def _render_bullets(self, lines):
        items = [ListItem(Paragraph(line, self.styles["body"])) for line in lines]
        return ListFlowable(items, bulletType="bullet", start="circle", leftIndent=14)

    def _signature_block(self):
        blocks = []
        for sig in self.data.get("signatories", []):
            lines = [sig.get("verification_label") or "Electronically Verified"]
            if sig.get("name"):
                lines.append(f"<b>{sig.get('name')}</b>")
            if sig.get("credentials"):
                lines.append(sig.get("credentials"))
            if sig.get("registration"):
                lines.append(sig.get("registration"))
            p = Paragraph("<br/>".join(lines), ParagraphStyle("sig", parent=self.styles["value"], alignment=2, leading=12))
            blocks.append(p)
            blocks.append(Spacer(1, 5))

        if not blocks:
            return None

        table = Table([[b] for b in blocks], colWidths=[70 * mm])
        table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return KeepTogether([Spacer(1, 10), table])

    def generate(self) -> bytes:
        self.fetch_data()

        doc = BaseDocTemplate(
            self.buffer,
            pagesize=A4,
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            topMargin=MARGIN_TOP + HEADER_HEIGHT + 2 * mm,
            bottomMargin=MARGIN_BOTTOM + FOOTER_RESERVED,
        )

        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
        doc.addPageTemplates([PageTemplate(id="master", frames=[frame], onPage=self.draw_header, onPageEnd=self.draw_footer)])

        story = []
        story.append(self._patient_table())
        story.append(Spacer(1, 7))

        story.append(Paragraph(self.data.get("report_title", "RADIOLOGY REPORT"), self.styles["title"]))
        story.append(Table([[""]], colWidths=[PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT], rowHeights=[0.6], style=TableStyle([("LINEABOVE", (0, 0), (0, 0), 0.7, DIVIDER)])))
        story.append(Spacer(1, 4))

        sections = self.data.get("sections", {})

        technique = sections.get("technique", [])
        if technique:
            story.append(self._section_heading("Technique"))
            story.extend(self._render_lines(technique))

        comparison = sections.get("comparison", [])
        if comparison:
            story.append(self._section_heading("Comparison"))
            story.extend(self._render_lines(comparison))

        story.append(self._section_heading("Findings"))
        findings = sections.get("findings", [])
        if findings:
            for block in findings:
                heading = str(block.get("heading", "")).strip()
                if heading:
                    story.append(Paragraph(heading, self.styles["subheading"]))
                for line in block.get("lines", []):
                    story.append(Paragraph(line, self.styles["body"]))
                for para in block.get("paragraphs", []):
                    story.append(Paragraph(para, self.styles["body"]))
                bullets = [str(b).strip() for b in block.get("bullets", []) if str(b).strip()]
                if bullets:
                    story.append(self._render_bullets(bullets))
                story.append(Spacer(1, 2))
        else:
            story.append(Paragraph("No findings provided.", self.styles["body"]))

        measurements = sections.get("measurements", [])
        if measurements:
            story.append(self._section_heading("Measurements"))
            story.append(self._render_measurements(measurements))

        impression = sections.get("impression", [])
        if impression:
            impression_block = [
                Paragraph("Impression", self.styles["section_title"]),
                Spacer(1, 2),
                self._render_bullets(impression),
            ]
            impression_table = Table(
                [[KeepTogether(impression_block)]],
                colWidths=[PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), SOFT_BG),
                        ("BOX", (0, 0), (-1, -1), 0.6, HexColor("#dfdfdf")),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ]
                ),
            )
            story.append(KeepTogether([Spacer(1, 6), impression_table]))

        recommendations = sections.get("recommendations", [])
        if recommendations:
            story.append(self._section_heading("Recommendations / Advice"))
            story.append(self._render_bullets(recommendations))

        sig = self._signature_block()
        if sig is not None:
            story.append(sig)

        doc.build(story)
        pdf_bytes = self.buffer.getvalue()
        self.buffer.close()
        return pdf_bytes


def generate_report_pdf_v2(report_instance_v2_id, narrative_json=None) -> bytes:
    generator = ReportPDFGeneratorV2(report_instance_v2_id, narrative_json)
    return generator.generate()
