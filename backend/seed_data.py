#!/usr/bin/env python
"""
Data seeding script for RIMS
Creates modalities, services, patients, studies, and one finalized report
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from django.contrib.auth import get_user_model
from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.studies.models import Study
from apps.templates.models import Template, TemplateSection, TemplateField, FieldOption, TemplateVersion
from apps.reporting.models import Report
from apps.reporting.pdf import build_basic_pdf

User = get_user_model()

def seed_data():
    print("=" * 60)
    print("RIMS Data Seeding")
    print("=" * 60)
    
    # Create or get superuser
    print("\n[1/7] Creating superuser...")
    user, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@rims.local",
            "is_staff": True,
            "is_superuser": True,
        }
    )
    if created:
        user.set_password("admin123")
        user.save()
        print(f"✓ Created superuser: {user.username} / admin123")
    else:
        print(f"✓ Superuser exists: {user.username}")
    
    # Create Modalities
    print("\n[2/7] Creating modalities...")
    modalities = {}
    for code, name in [("USG", "Ultrasound"), ("XRAY", "X-Ray"), ("CT", "CT Scan"), ("MRI", "MRI")]:
        mod, created = Modality.objects.get_or_create(code=code, defaults={"name": name})
        modalities[code] = mod
        print(f"✓ {'Created' if created else 'Exists'}: {code} - {name}")
    
    # Create Services
    print("\n[3/7] Creating services...")
    services = {}
    service_templates = [
        ("USG", "Abdominal Ultrasound", 5000, 120),
        ("USG", "Pelvic Ultrasound", 4500, 120),
        ("XRAY", "Chest X-Ray", 2000, 60),
        ("XRAY", "Limb X-Ray", 1500, 60),
        ("CT", "CT Head", 15000, 240),
        ("CT", "CT Chest", 20000, 240),
    ]
    for mod_code, name, price, tat in service_templates:
        svc, created = Service.objects.get_or_create(
            modality=modalities[mod_code],
            name=name,
            defaults={"price": price, "tat_minutes": tat}
        )
        services[f"{mod_code}_{name}"] = svc
        print(f"✓ {'Created' if created else 'Exists'}: {mod_code} - {name}")
    
    # Create Template
    print("\n[4/7] Creating template...")
    template, created = Template.objects.get_or_create(
        name="Abdominal USG Template",
        modality_code="USG",
        defaults={"is_active": True}
    )
    
    if created:
        # Create sections and fields
        section1, _ = TemplateSection.objects.get_or_create(
            template=template,
            title="Findings",
            defaults={"order": 1}
        )
        
        # Liver field
        liver_field, _ = TemplateField.objects.get_or_create(
            section=section1,
            key="liver",
            defaults={
                "label": "Liver",
                "field_type": "paragraph",
                "required": False,
                "order": 1,
            }
        )
        
        # Status field with dropdown
        status_field, _ = TemplateField.objects.get_or_create(
            section=section1,
            key="status",
            defaults={
                "label": "Overall Status",
                "field_type": "dropdown",
                "required": True,
                "order": 2,
            }
        )
        
        # Create options for status
        for label, value in [("Normal", "normal"), ("Abnormal", "abnormal"), ("Inconclusive", "inconclusive")]:
            FieldOption.objects.get_or_create(
                field=status_field,
                value=value,
                defaults={"label": label, "order": 0}
            )
        
        # Abnormalities checklist
        abn_field, _ = TemplateField.objects.get_or_create(
            section=section1,
            key="abnormalities",
            defaults={
                "label": "Abnormalities",
                "field_type": "checklist",
                "required": False,
                "order": 3,
            }
        )
        
        for label, value in [
            ("Gallstones", "gallstones"),
            ("Liver mass", "liver_mass"),
            ("Ascites", "ascites"),
            ("Hepatomegaly", "hepatomegaly"),
        ]:
            FieldOption.objects.get_or_create(
                field=abn_field,
                value=value,
                defaults={"label": label, "order": 0}
            )
        
        print("✓ Created template with sections and fields")
    else:
        print("✓ Template exists")
    
    # Publish template version
    latest_version = template.versions.order_by("-version").first()
    if not latest_version or not latest_version.is_published:
        # Build schema manually (same logic as in api.py)
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
                    "help_text": f.help_text,
                    "placeholder": f.placeholder,
                    "unit": f.unit,
                    "order": f.order,
                    "options": [{"label": o.label, "value": o.value, "order": o.order} for o in f.options.all().order_by("order")]
                }
                sec_obj["fields"].append(field_obj)
            schema["sections"].append(sec_obj)
        
        version_num = 1 if not latest_version else latest_version.version + 1
        TemplateVersion.objects.create(
            template=template,
            version=version_num,
            schema=schema,
            is_published=True
        )
        print("✓ Published template version")
    else:
        print("✓ Template version exists")
    
    latest_version = template.versions.filter(is_published=True).order_by("-version").first()
    
    # Link template to service
    if services.get("USG_Abdominal Ultrasound"):
        services["USG_Abdominal Ultrasound"].default_template = template
        services["USG_Abdominal Ultrasound"].save()
        print("✓ Linked template to Abdominal USG service")
    
    # Create Patients
    print("\n[5/7] Creating patients...")
    patients = []
    patient_data = [
        ("MRN001", "John Doe", 45, "M", "03001234567", "Lahore", "Dr. Smith"),
        ("MRN002", "Jane Smith", 32, "F", "03009876543", "Karachi", "Dr. Ali"),
        ("MRN003", "Ahmed Khan", 28, "M", "03005555666", "Islamabad", "Dr. Hassan"),
    ]
    for mrn, name, age, gender, phone, address, referrer in patient_data:
        p, created = Patient.objects.get_or_create(
            mrn=mrn,
            defaults={
                "name": name,
                "age": age,
                "gender": gender,
                "phone": phone,
                "address": address,
                "referrer": referrer,
            }
        )
        patients.append(p)
        print(f"✓ {'Created' if created else 'Exists'}: {mrn} - {name}")
    
    # Create Studies
    print("\n[6/7] Creating studies...")
    studies = []
    service = services.get("USG_Abdominal Ultrasound")
    if service:
        for i, patient in enumerate(patients):
            now = timezone.now()
            prefix = now.strftime("%Y%m%d")
            accession = f"{prefix}{str(i+1).zfill(4)}"
            
            study, created = Study.objects.get_or_create(
                accession=accession,
                defaults={
                    "patient": patient,
                    "service": service,
                    "indication": "Routine checkup",
                    "status": "draft" if i == 0 else "registered",
                    "created_by": user,
                }
            )
            studies.append(study)
            print(f"✓ {'Created' if created else 'Exists'}: {accession} - {patient.name}")
    
    # Create one finalized report
    print("\n[7/7] Creating finalized report...")
    if studies and latest_version:
        study = studies[0]
        report, created = Report.objects.get_or_create(
            study=study,
            defaults={
                "template_version": latest_version,
                "status": "draft",
                "values": {
                    "liver": "Normal size and echotexture",
                    "status": "normal",
                    "abnormalities": []
                },
                "narrative": "The liver appears normal in size and echotexture. No focal lesions identified. Gallbladder is normal. Spleen is normal in size.",
                "impression": "Normal abdominal ultrasound with no significant findings.",
            }
        )
        
        if created or report.status == "draft":
            # Finalize the report
            report.status = "final"
            report.finalized_by = user
            report.finalized_at = timezone.now()
            
            # Generate PDF
            pdf_file = build_basic_pdf(report)
            report.pdf_file.save(pdf_file.name, pdf_file, save=False)
            report.save()
            
            # Update study status
            study.status = "final"
            study.save()
            
            print(f"✓ Created and finalized report for {study.accession}")
            print(f"  - PDF: {report.pdf_file.name}")
        else:
            print(f"✓ Report already finalized for {study.accession}")
    
    print("\n" + "=" * 60)
    print("✅ Data seeding completed!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Modalities: {Modality.objects.count()}")
    print(f"  - Services: {Service.objects.count()}")
    print(f"  - Patients: {Patient.objects.count()}")
    print(f"  - Studies: {Study.objects.count()}")
    print(f"  - Templates: {Template.objects.count()}")
    print(f"  - Reports: {Report.objects.count()}")
    print(f"  - Finalized Reports: {Report.objects.filter(status='final').count()}")
    print(f"\nLogin: admin / admin123")

if __name__ == "__main__":
    seed_data()

