#!/usr/bin/env python3
"""
End-to-end workflow test script for RIMS
Run this after setting up the database and creating a superuser.
Usage: python manage.py shell < test_workflow.py
Or: python test_workflow.py (if Django is in PYTHONPATH)
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rims_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.patients.models import Patient
from apps.catalog.models import Modality, Service
from apps.templates.models import Template, TemplateSection, TemplateField, FieldOption, TemplateVersion
from apps.studies.models import Study
from apps.reporting.models import Report

User = get_user_model()

def test_workflow():
    print("=" * 60)
    print("RIMS End-to-End Workflow Test")
    print("=" * 60)
    
    # Step 1: Get or create test user
    print("\n[1/8] Checking for test user...")
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com', 'is_staff': True}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("✓ Created test user: testuser / testpass123")
    else:
        print("✓ Test user already exists")
    
    # Step 2: Create Patient
    print("\n[2/8] Creating patient...")
    patient, created = Patient.objects.get_or_create(
        mrn='TEST001',
        defaults={
            'name': 'John Doe',
            'age': 45,
            'gender': 'M',
            'phone': '123-456-7890'
        }
    )
    print(f"✓ Patient created: {patient.mrn} - {patient.name}")
    
    # Step 3: Create Modality and Service
    print("\n[3/8] Creating modality and service...")
    modality, created = Modality.objects.get_or_create(
        code='USG',
        defaults={'name': 'Ultrasound'}
    )
    print(f"✓ Modality: {modality.code}")
    
    service, created = Service.objects.get_or_create(
        modality=modality,
        name='Abdominal Ultrasound',
        defaults={'price': 150.00, 'tat_minutes': 30}
    )
    print(f"✓ Service: {service.name}")
    
    # Step 4: Create Template with sections and fields
    print("\n[4/8] Creating template...")
    template, created = Template.objects.get_or_create(
        name='Abdominal USG Report',
        modality_code='USG',
        defaults={'is_active': True}
    )
    
    if created or template.sections.count() == 0:
        # Clear existing sections if any
        template.sections.all().delete()
        
        # Create section 1
        section1 = TemplateSection.objects.create(
            template=template,
            title='Findings',
            order=1
        )
        
        # Create fields in section 1
        field1 = TemplateField.objects.create(
            section=section1,
            label='Liver',
            key='liver',
            field_type='short_text',
            required=True,
            order=1
        )
        
        field2 = TemplateField.objects.create(
            section=section1,
            label='Status',
            key='status',
            field_type='dropdown',
            required=True,
            order=2
        )
        
        # Add options to dropdown field
        FieldOption.objects.create(field=field2, label='Normal', value='normal', order=1)
        FieldOption.objects.create(field=field2, label='Abnormal', value='abnormal', order=2)
        
        field3 = TemplateField.objects.create(
            section=section1,
            label='Abnormalities',
            key='abnormalities',
            field_type='checklist',
            required=False,
            order=3
        )
        
        FieldOption.objects.create(field=field3, label='Mass', value='mass', order=1)
        FieldOption.objects.create(field=field3, label='Cyst', value='cyst', order=2)
        FieldOption.objects.create(field=field3, label='Calculi', value='calculi', order=3)
    
    print(f"✓ Template: {template.name}")
    print(f"  - Sections: {template.sections.count()}")
    print(f"  - Total fields: {sum(s.fields.count() for s in template.sections.all())}")
    
    # Step 5: Publish Template Version
    print("\n[5/8] Publishing template version...")
    latest_version = template.versions.order_by('-version').first()
    next_version = 1 if not latest_version else latest_version.version + 1
    
    # Build schema
    schema = {
        "template_id": str(template.id),
        "name": template.name,
        "modality_code": template.modality_code,
        "sections": []
    }
    for sec in template.sections.all().order_by("order"):
        sec_obj = {
            "id": str(sec.id),
            "title": sec.title,
            "order": sec.order,
            "fields": []
        }
        for f in sec.fields.all().order_by("order"):
            field_obj = {
                "id": str(f.id),
                "label": f.label,
                "key": f.key,
                "type": f.field_type,
                "required": f.required,
                "options": [{"label": o.label, "value": o.value} for o in f.options.all().order_by("order")]
            }
            sec_obj["fields"].append(field_obj)
        schema["sections"].append(sec_obj)
    
    template_version = TemplateVersion.objects.create(
        template=template,
        version=next_version,
        schema=schema,
        is_published=True
    )
    print(f"✓ Template version published: v{template_version.version}")
    
    # Step 6: Create Study
    print("\n[6/8] Creating study...")
    from datetime import datetime
    from django.utils import timezone
    accession = datetime.now().strftime("%Y%m%d") + "0001"
    
    study, created = Study.objects.get_or_create(
        accession=accession,
        defaults={
            'patient': patient,
            'service': service,
            'indication': 'Routine checkup',
            'status': 'registered',
            'created_by': user
        }
    )
    print(f"✓ Study created: {study.accession}")
    
    # Step 7: Create Report
    print("\n[7/8] Creating report...")
    report, created = Report.objects.get_or_create(
        study=study,
        defaults={
            'template_version': template_version,
            'status': 'draft',
            'values': {
                'liver': 'Normal size and echotexture',
                'status': 'normal',
                'abnormalities': []
            },
            'narrative': 'The liver appears normal in size and echotexture. No focal lesions identified.',
            'impression': 'Normal abdominal ultrasound.'
        }
    )
    print(f"✓ Report created: {report.id}")
    print(f"  - Status: {report.status}")
    print(f"  - Values: {len(report.values)} fields")
    
    # Step 8: Finalize Report (generate PDF)
    print("\n[8/8] Finalizing report and generating PDF...")
    if report.status == 'draft':
        from apps.reporting.pdf import build_basic_pdf
        report.status = 'final'
        report.finalized_by = user
        from django.utils import timezone
        report.finalized_at = timezone.now()
        
        pdf_file = build_basic_pdf(report)
        report.pdf_file.save(pdf_file.name, pdf_file, save=False)
        report.save()
        
        study.status = 'final'
        study.save()
        
        print(f"✓ Report finalized!")
        print(f"  - PDF generated: {report.pdf_file.name}")
        print(f"  - Study status updated: {study.status}")
    else:
        print(f"✓ Report already finalized")
    
    print("\n" + "=" * 60)
    print("✅ Workflow test completed successfully!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Patient: {patient.mrn} - {patient.name}")
    print(f"  - Study: {study.accession}")
    print(f"  - Report: {report.id} ({report.status})")
    print(f"  - Template: {template.name} v{template_version.version}")
    if report.pdf_file:
        print(f"  - PDF: {report.pdf_file.name}")
    print()

if __name__ == '__main__':
    try:
        test_workflow()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

