# Generated migration to backfill ReceiptSettings with correct defaults

from django.db import migrations


def backfill_receipt_settings(apps, schema_editor):
    """
    Backfill ReceiptSettings with correct footer and header text.
    Safe and idempotent.
    """
    ReceiptSettings = apps.get_model('studies', 'ReceiptSettings')
    
    # Correct values
    correct_header = "Consultant Place Clinic"
    correct_footer = "Adjacent Excel Labs, Near Arman Pan Shop Faisalabad Road Jaranwala\nFor information/Appointment: Tel: 041 4313 777 | WhatsApp: 03279640897"
    old_wrong_header = "Consultants Clinic Place"
    
    try:
        settings = ReceiptSettings.objects.get(pk=1)
        
        # Fix header if it's the old wrong default
        if settings.header_text == old_wrong_header:
            settings.header_text = correct_header
        
        # Fix footer if it's blank, empty, or whitespace-only
        if not settings.footer_text or not settings.footer_text.strip():
            settings.footer_text = correct_footer
        
        settings.save()
    except ReceiptSettings.DoesNotExist:
        # Create with correct defaults if doesn't exist
        ReceiptSettings.objects.create(
            pk=1,
            header_text=correct_header,
            footer_text=correct_footer
        )


def reverse_migration(apps, schema_editor):
    """Reverse is a no-op since we don't want to revert good data"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0004_receiptsettings_footer_text'),
    ]

    operations = [
        migrations.RunPython(backfill_receipt_settings, reverse_migration),
    ]
