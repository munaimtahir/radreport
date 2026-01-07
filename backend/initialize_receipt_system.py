#!/usr/bin/env python
"""
Initialize Receipt System
Creates ReceiptSequence and ReceiptSettings if they don't exist
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from apps.studies.models import ReceiptSequence, ReceiptSettings
from django.utils import timezone

def initialize_receipt_system():
    """Initialize receipt system components"""
    print("=" * 60)
    print("Initializing Receipt System")
    print("=" * 60)
    
    # Initialize ReceiptSettings (singleton)
    print("\n[1/2] Initializing ReceiptSettings...")
    settings = ReceiptSettings.get_settings()
    print(f"✓ ReceiptSettings initialized")
    print(f"  - Header Text: {settings.header_text}")
    print(f"  - Logo: {'Yes' if settings.logo_image else 'No'}")
    print(f"  - Header Image: {'Yes' if settings.header_image else 'No'}")
    
    # Initialize ReceiptSequence for current month
    print("\n[2/2] Initializing ReceiptSequence for current month...")
    now = timezone.now()
    yymm = now.strftime("%y%m")
    
    sequence, created = ReceiptSequence.objects.get_or_create(
        yymm=yymm,
        defaults={"last_number": 0}
    )
    
    if created:
        print(f"✓ Created ReceiptSequence for {yymm}")
    else:
        print(f"✓ ReceiptSequence for {yymm} already exists (last_number: {sequence.last_number})")
    
    print("\n" + "=" * 60)
    print("✅ Receipt System Initialized!")
    print("=" * 60)

if __name__ == "__main__":
    initialize_receipt_system()
