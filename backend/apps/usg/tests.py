"""
USG Reporting Subsystem - Basic smoke tests
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.patients.models import Patient
from apps.studies.models import Visit
from apps.usg.models import (
    UsgTemplate, UsgStudy, UsgFieldValue, UsgPublishedSnapshot
)
from apps.usg.renderer import render_usg_report

User = get_user_model()


class UsgModelTests(TestCase):
    """Test USG models"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.patient = Patient.objects.create(
            name='Test Patient',
            age=45,
            gender='Male'
        )
        self.visit = Visit.objects.create(
            patient=self.patient,
            created_by=self.user
        )
        self.template = UsgTemplate.objects.create(
            code='TEST_TEMPLATE',
            name='Test Template',
            category='test',
            version=1,
            is_locked=False,
            schema_json={
                'sections': [
                    {
                        'section_key': 'test_section',
                        'title': 'Test Section',
                        'fields': [
                            {
                                'field_key': 'test_field',
                                'label': 'Test Field',
                                'type': 'text'
                            }
                        ]
                    }
                ]
            }
        )
    
    def test_create_draft_study(self):
        """Test creating a draft USG study"""
        study = UsgStudy.objects.create(
            patient=self.patient,
            visit=self.visit,
            service_code='TEST_SERVICE',
            template=self.template,
            created_by=self.user
        )
        self.assertEqual(study.status, 'draft')
        self.assertFalse(study.is_locked)
    
    def test_field_values(self):
        """Test adding field values to a study"""
        study = UsgStudy.objects.create(
            patient=self.patient,
            visit=self.visit,
            service_code='TEST_SERVICE',
            template=self.template,
            created_by=self.user
        )
        
        field_value = UsgFieldValue.objects.create(
            study=study,
            field_key='test_field',
            value_json='Test value',
            is_not_applicable=False
        )
        
        self.assertEqual(field_value.field_key, 'test_field')
        self.assertEqual(study.field_values.count(), 1)
    
    def test_na_field_excluded_from_render(self):
        """Test that NA fields are excluded from rendering"""
        template_schema = {
            'sections': [
                {
                    'section_key': 'section1',
                    'title': 'Section 1',
                    'fields': [
                        {
                            'field_key': 'field1',
                            'label': 'Field 1',
                            'type': 'text'
                        },
                        {
                            'field_key': 'field2',
                            'label': 'Field 2',
                            'type': 'text'
                        }
                    ]
                }
            ]
        }
        
        field_values = {
            'field1': {'value_json': 'Visible text', 'is_not_applicable': False},
            'field2': {'value_json': 'Hidden text', 'is_not_applicable': True}
        }
        
        narrative = render_usg_report(template_schema, field_values)
        
        self.assertIn('Visible text', narrative)
        self.assertNotIn('Hidden text', narrative)
    
    def test_empty_section_excluded_from_render(self):
        """Test that sections with no printable fields are excluded"""
        template_schema = {
            'sections': [
                {
                    'section_key': 'empty_section',
                    'title': 'Empty Section',
                    'fields': [
                        {
                            'field_key': 'field1',
                            'label': 'Field 1',
                            'type': 'text'
                        }
                    ]
                }
            ]
        }
        
        field_values = {
            'field1': {'value_json': None, 'is_not_applicable': True}
        }
        
        narrative = render_usg_report(template_schema, field_values)
        
        self.assertNotIn('Empty Section', narrative)
    
    def test_published_study_immutability(self):
        """Test that published studies cannot be modified"""
        study = UsgStudy.objects.create(
            patient=self.patient,
            visit=self.visit,
            service_code='TEST_SERVICE',
            template=self.template,
            created_by=self.user,
            status='published'
        )
        
        # Create field value for published study
        with self.assertRaises(Exception):
            UsgFieldValue.objects.create(
                study=study,
                field_key='test_field',
                value_json='Test value'
            )


class UsgRendererTests(TestCase):
    """Test narrative rendering logic"""
    
    def test_render_single_choice(self):
        """Test rendering single choice fields"""
        template_schema = {
            'sections': [
                {
                    'section_key': 'liver',
                    'title': 'Liver',
                    'fields': [
                        {
                            'field_key': 'liver_size',
                            'label': 'Liver Size',
                            'type': 'single_choice',
                            'options': [
                                {'label': 'Normal', 'value': 'normal'},
                                {'label': 'Enlarged', 'value': 'enlarged'}
                            ]
                        }
                    ]
                }
            ]
        }
        
        field_values = {
            'liver_size': {'value_json': 'normal', 'is_not_applicable': False}
        }
        
        narrative = render_usg_report(template_schema, field_values)
        
        self.assertIn('Liver:', narrative)
        self.assertIn('Liver Size: Normal', narrative)
    
    def test_render_number_field(self):
        """Test rendering number fields"""
        template_schema = {
            'sections': [
                {
                    'section_key': 'measurements',
                    'title': 'Measurements',
                    'fields': [
                        {
                            'field_key': 'liver_span',
                            'label': 'Liver Span (cm)',
                            'type': 'number'
                        }
                    ]
                }
            ]
        }
        
        field_values = {
            'liver_span': {'value_json': 14.5, 'is_not_applicable': False}
        }
        
        narrative = render_usg_report(template_schema, field_values)
        
        self.assertIn('Liver Span (cm): 14.5', narrative)
