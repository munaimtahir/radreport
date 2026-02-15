#!/usr/bin/env python
"""
Initialize Printing/Receipt System
Ensures ReceiptBrandingConfig and ReportingOrganizationConfig singletons exist.
SequenceCounter rows are created on first use (no pre-seeding needed).
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from apps.printing.models import ReceiptBrandingConfig
from apps.reporting.models import ReportingOrganizationConfig


def initialize_receipt_system():
    """Ensure printing config singletons exist."""
    print("=" * 60)
    print("Initializing Printing/Receipt System")
    print("=" * 60)

    print("\n[1/2] Ensuring ReceiptBrandingConfig...")
    r = ReceiptBrandingConfig.get_singleton()
    print(f"✓ ReceiptBrandingConfig ready")
    print(f"  - Header: {r.receipt_header_text[:50]}...")
    print(f"  - Logo: {'Yes' if r.receipt_logo else 'No'}")
    print(f"  - Banner: {'Yes' if r.receipt_banner else 'No'}")

    print("\n[2/2] Ensuring ReportingOrganizationConfig...")
    org = ReportingOrganizationConfig.objects.first()
    if not org:
        org = ReportingOrganizationConfig.objects.create(
            org_name="Organization",
            disclaimer_text="This report is electronically verified.",
        )
        print("✓ Created ReportingOrganizationConfig")
    else:
        print(f"✓ ReportingOrganizationConfig exists: {org.org_name}")

    print("\n" + "=" * 60)
    print("✅ Printing System Ready!")
    print("=" * 60)


if __name__ == "__main__":
    initialize_receipt_system()
