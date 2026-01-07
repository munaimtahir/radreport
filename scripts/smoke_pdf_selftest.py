#!/usr/bin/env python3
"""
Minimal WeasyPrint runtime check inside the backend container.
Usage inside container:
  python scripts/smoke_pdf_selftest.py
"""
from io import BytesIO
from weasyprint import HTML, CSS


def main():
    html = HTML(string="<html><body><h1>PDF OK</h1><p>WeasyPrint working.</p></body></html>")
    css = CSS(string="@page { size: A4; margin: 10mm; } body { font-family: DejaVu Sans, sans-serif; }")
    data: bytes = html.write_pdf(stylesheets=[css])
    # ensure non-empty
    assert len(data) > 1000
    # write to tmp for inspection
    with open("/tmp/weasyprint_selftest.pdf", "wb") as f:
        f.write(data)
    print("OK: WeasyPrint generated /tmp/weasyprint_selftest.pdf")


if __name__ == "__main__":
    main()

