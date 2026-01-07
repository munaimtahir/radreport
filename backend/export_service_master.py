#!/usr/bin/env python
"""
Export Service Master List
Creates a backup/export of all services for production
"""
import os
import sys
import django
import csv
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from apps.catalog.models import Service

def export_service_master():
    """Export all services to CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"service_master_export_{timestamp}.csv"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    services = Service.objects.select_related("modality", "default_template").all().order_by("code")
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'service_code', 'name', 'department', 'billing_group', 'sub_category',
            'price', 'currency', 'tat_min', 'unit', 'is_active',
            'modality_code', 'category', 'tat_value', 'tat_unit', 'tat_minutes',
            'has_template', 'template_id'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for svc in services:
            # Determine billing_group and sub_category from name
            billing_group = "Ultrasound"
            sub_category = "Gray Scale"
            if "guided" in svc.name.lower():
                billing_group = "Procedure"
                sub_category = "Ultrasound Guided"
            elif "doppler" in svc.name.lower():
                sub_category = "Doppler"
            
            writer.writerow({
                'service_code': svc.code or '',
                'name': svc.name,
                'department': 'Radiology',
                'billing_group': billing_group,
                'sub_category': sub_category,
                'price': str(svc.price),
                'currency': 'PKR',
                'tat_min': svc.tat_minutes,
                'unit': 'service',
                'is_active': '1' if svc.is_active else '0',
                'modality_code': svc.modality.code if svc.modality else '',
                'category': svc.category,
                'tat_value': svc.tat_value,
                'tat_unit': svc.tat_unit,
                'tat_minutes': svc.tat_minutes,
                'has_template': '1' if svc.default_template else '0',
                'template_id': str(svc.default_template.id) if svc.default_template else '',
            })
    
    print(f"✅ Service master exported to: {filepath}")
    print(f"   Total services: {services.count()}")
    return filepath

if __name__ == "__main__":
    export_service_master()
