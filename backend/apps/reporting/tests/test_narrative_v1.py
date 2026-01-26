from django.test import TestCase
from apps.reporting.models import ReportProfile, ReportParameter, ReportInstance, ReportValue, ReportParameterOption
from apps.reporting.services.narrative_v1 import generate_report_narrative
from apps.workflow.models import ServiceVisitItem, ServiceVisit
# Mocking ServiceVisit/Item is painful due to foreign keys, 
# but we only need ReportInstance for the service.
# Actually ReportInstance requires ServiceVisitItem.
# We will create minimal objects.

class NarrativeGeneratorTests(TestCase):
    def setUp(self):
        # Create Profile
        self.profile = ReportProfile.objects.create(
            code="TEST_PROF", 
            name="Test Profile", 
            enable_narrative=True
        )
        
        # Create Parameters
        self.p_text = ReportParameter.objects.create(
            profile=self.profile,
            section="Section A",
            name="Text Param",
            parameter_type="short_text",
            order=1,
            sentence_template="{name} shows {value}."
        )
        
        self.p_bool = ReportParameter.objects.create(
            profile=self.profile,
            section="Section A",
            name="Bool Param",
            parameter_type="boolean",
            order=2,
            sentence_template="Bool is {value}."
        )
        
        self.p_omit = ReportParameter.objects.create(
            profile=self.profile,
            section="Section B",
            name="Omit Param",
            parameter_type="dropdown",
            order=1,
            omit_if_values=["Normal", "na"]
        )
        ReportParameterOption.objects.create(parameter=self.p_omit, label="Normal", value="Normal")
        ReportParameterOption.objects.create(parameter=self.p_omit, label="Abnormal", value="Abnormal")

        self.p_checklist = ReportParameter.objects.create(
            profile=self.profile,
            section="Section B",
            name="Checklist Param",
            parameter_type="checklist",
            join_label=" and ",
            order=2,
            sentence_template="Includes {value}."
        )
        self.opt1 = ReportParameterOption.objects.create(parameter=self.p_checklist, label="A", value="a")
        self.opt2 = ReportParameterOption.objects.create(parameter=self.p_checklist, label="B", value="b")

        self.p_imp = ReportParameter.objects.create(
            profile=self.profile,
            section="Conclusion",
            name="Impression",
            parameter_type="long_text",
            narrative_role="impression_hint",
            order=1
        )
        
        # Create Instance (Mocking dependencies)
        # We need a ServiceVisitItem. 
        # Since we are testing service function, we can just mock the ID lookup 
        # OR create the DB objects if Django Test DB is used.
        # It's better to create real objects in integration test.
        # But ReportInstance constraints require ServiceVisitItem.
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create(username="testuser")
        
        # We assume catalog/workflow models exist but might be heavy to setup.
        # Let's try to bypass if possible or create minimal.
        # Since I am in 'apps/reporting', I should have access to workflow models? 
        # Yes, imports are there.
        
        # Note: If ServiceVisitItem creation is complex, this test might fail setup.
        # Let's try to create them via standard means if possible, or use raw SQL?
        # Standard means:
        # service = Service(...)
        # visit = ServiceVisit(...)
        # item = ServiceVisitItem(...)
        # For unit testing the logic, we ideally shouldn't depend on Workflow.
        # But ReportInstance has OneToOne with ServiceVisitItem.
        # So we MUST create it.
        
        # We can mock `ReportInstance.objects.get` in the service?
        # No, let's try to create. 
        # If this fails, I'll use mocks.
        pass

    def test_generate_narrative_logic(self):
        # We will mock the DB access in the service to avoid complex setup
        # or just create the instance if simple.
        
        # Let's try creating a dummy ReportInstance without full relation
        # Wait, Foreign Key constraint will fail.
        
        # Let's Mock `ReportInstance.objects.select_related(...).get`
        # and `ReportValue.objects.filter`
        
        from unittest.mock import MagicMock, patch
        
        mock_instance = MagicMock(spec=ReportInstance)
        mock_instance.profile = self.profile
        mock_instance.id = "mock-id"
        
        with patch("apps.reporting.services.narrative_v1.ReportInstance.objects.select_related") as mock_select:
             mock_select.return_value.get.return_value = mock_instance
             
             with patch("apps.reporting.services.narrative_v1.ReportValue.objects.filter") as mock_values:
                 # Setup Values
                 v1 = MagicMock(spec=ReportValue, parameter_id=self.p_text.id, value="Something", parameter=self.p_text)
                 v2 = MagicMock(spec=ReportValue, parameter_id=self.p_bool.id, value="true", parameter=self.p_bool) # JSON 'true' or python True? TextField stores string "true" usually or "True"
                 v3 = MagicMock(spec=ReportValue, parameter_id=self.p_omit.id, value="Normal", parameter=self.p_omit) # Should omit
                 v4 = MagicMock(spec=ReportValue, parameter_id=self.p_checklist.id, value='["a", "b"]', parameter=self.p_checklist)
                 v5 = MagicMock(spec=ReportValue, parameter_id=self.p_imp.id, value="Overall bad.", parameter=self.p_imp)
                 
                 mock_values.return_value = [v1, v2, v3, v4, v5]
                 
                 result = generate_report_narrative("mock-id")
                 
                 # Assertions
                 findings = result["findings_text"]
                 impression = result["impression_text"]
                 
                 # Text
                 self.assertIn("Text Param shows Something.", findings)
                 
                 # Boolean
                 self.assertIn("Bool is Yes.", findings) # "true" -> Yes
                 
                 # Omit
                 self.assertNotIn("Normal", findings)
                 self.assertNotIn("Omit Param", findings)
                 
                 # Checklist
                 # Should join "A" and "B" (labels) with " and "
                 self.assertIn("Includes A and B.", findings)
                 
                 # Impression
                 self.assertIn("Overall bad.", impression)
                 
                 # Section grouping
                 self.assertIn("Section A:", findings)
                 self.assertIn("Section B:", findings)

