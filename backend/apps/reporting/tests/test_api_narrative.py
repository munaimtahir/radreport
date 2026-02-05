import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import Modality, Service
from apps.patients.models import Patient
from apps.workflow.models import ServiceVisit, ServiceVisitItem
from apps.reporting.models import (
    ReportProfile,
    ReportParameter,
    ReportParameterOption,
    ServiceReportProfile,
)


SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots"
API_LOG_DIR = Path("/tmp/rad_audit/logs")


class ApiNarrativeSnapshotTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="api_reporter", password="password"
        )

        self.modality = Modality.objects.create(code="USG", name="Ultrasound")
        self.service = Service.objects.create(
            modality=self.modality,
            name="USG Abdomen",
            code="USG_ABD_API",
            price=1500,
        )
        self.patient = Patient.objects.create(
            name="Snapshot Patient", age=30, gender="Male", phone="1234567890"
        )

        self.profile = ReportProfile.objects.create(
            code="USG_ABD_SNAP",
            name="USG Abdomen Snapshot",
            modality="USG",
            enable_narrative=True,
        )
        ServiceReportProfile.objects.create(service=self.service, profile=self.profile)

        self.p_liver_size = ReportParameter.objects.create(
            profile=self.profile,
            section="1 Liver",
            name="Liver Size",
            parameter_type="number",
            unit="cm",
            order=1,
        )
        self.p_liver_echo = ReportParameter.objects.create(
            profile=self.profile,
            section="1 Liver",
            name="Echogenicity",
            parameter_type="dropdown",
            order=2,
            sentence_template="Echogenicity: {value}.",
        )
        ReportParameterOption.objects.create(
            parameter=self.p_liver_echo, label="Normal", value="normal", order=1
        )
        ReportParameterOption.objects.create(
            parameter=self.p_liver_echo, label="Increased", value="increased", order=2
        )

        self.p_gb_stones = ReportParameter.objects.create(
            profile=self.profile,
            section="2 Gallbladder",
            name="Gallstones",
            parameter_type="boolean",
            order=1,
            sentence_template="Gallstones: {value}.",
        )
        self.p_gb_wall = ReportParameter.objects.create(
            profile=self.profile,
            section="2 Gallbladder",
            name="Wall Thickness",
            parameter_type="number",
            unit="mm",
            order=2,
            sentence_template="Wall thickness: {value}{unit}.",
        )

        self.p_kidney_hydro = ReportParameter.objects.create(
            profile=self.profile,
            section="3 Kidneys",
            name="Hydronephrosis",
            parameter_type="dropdown",
            order=1,
            sentence_template="Hydronephrosis: {value}.",
            omit_if_values=["none"],
        )
        ReportParameterOption.objects.create(
            parameter=self.p_kidney_hydro, label="None", value="none", order=1
        )
        ReportParameterOption.objects.create(
            parameter=self.p_kidney_hydro, label="Mild", value="mild", order=2
        )
        ReportParameterOption.objects.create(
            parameter=self.p_kidney_hydro, label="Moderate", value="moderate", order=3
        )
        ReportParameterOption.objects.create(
            parameter=self.p_kidney_hydro, label="Severe", value="severe", order=4
        )

        self.p_kidney_stones = ReportParameter.objects.create(
            profile=self.profile,
            section="3 Kidneys",
            name="Stones",
            parameter_type="checklist",
            order=2,
            join_label=" and ",
            sentence_template="Stones: {value}.",
        )
        ReportParameterOption.objects.create(
            parameter=self.p_kidney_stones, label="Right", value="right", order=1
        )
        ReportParameterOption.objects.create(
            parameter=self.p_kidney_stones, label="Left", value="left", order=2
        )

        self.p_impression = ReportParameter.objects.create(
            profile=self.profile,
            section="Impression",
            name="Impression",
            parameter_type="long_text",
            order=1,
            narrative_role="impression_hint",
        )
        self.p_limitations = ReportParameter.objects.create(
            profile=self.profile,
            section="Limitations",
            name="Limitations",
            parameter_type="long_text",
            order=1,
            narrative_role="limitation_hint",
        )

    def _render_snapshot(self, narrative):
        findings = narrative.get("findings_text") or ""
        impression = narrative.get("impression_text") or ""
        limitations = narrative.get("limitations_text") or ""
        findings_block = f"{findings}\n\n" if findings else "\n"
        impression_block = f"{impression}\n\n" if impression else "\n"
        limitations_block = f"{limitations}\n\n" if limitations else "\n"
        return (
            "FINDINGS:\n"
            f"{findings_block}"
            "IMPRESSION:\n"
            f"{impression_block}"
            "LIMITATIONS:\n"
            f"{limitations_block}"
        )

    def _load_snapshot(self, filename):
        with open(SNAPSHOT_DIR / filename, "r", encoding="utf-8") as handle:
            return handle.read()

    def _log_case(self, filename, payload, generate_resp, narrative_resp):
        API_LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = API_LOG_DIR / filename
        data = {
            "payload": payload,
            "generate_narrative": generate_resp,
            "narrative": narrative_resp,
        }
        log_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def _create_item(self):
        visit = ServiceVisit.objects.create(patient=self.patient, created_by=self.user)
        return ServiceVisitItem.objects.create(
            service_visit=visit,
            service=self.service,
            status="REGISTERED",
        )

    def test_api_narrative_snapshots(self):
        self.client.force_authenticate(user=self.user)

        cases = [
            (
                "case_01.txt",
                "api_case_01.log",
                {
                    self.p_liver_size: "14",
                    self.p_liver_echo: "normal",
                    self.p_gb_stones: "false",
                    self.p_gb_wall: "3",
                    self.p_kidney_hydro: "none",
                    self.p_kidney_stones: ["right", "left"],
                    self.p_impression: "No acute abnormality",
                },
            ),
            (
                "case_02.txt",
                "api_case_02.log",
                {
                    self.p_liver_echo: "increased",
                    self.p_gb_stones: "true",
                    self.p_kidney_hydro: "mild",
                    self.p_kidney_stones: ["right"],
                    self.p_impression: "Fatty liver suspected",
                    self.p_limitations: "Limited by bowel gas",
                },
            ),
            (
                "case_03.txt",
                "api_case_03.log",
                {
                    self.p_liver_size: "12",
                    self.p_liver_echo: "na",
                    self.p_gb_stones: "false",
                    self.p_kidney_hydro: "none",
                    self.p_kidney_stones: [],
                },
            ),
        ]

        for snapshot_file, log_file, values_by_param in cases:
            item = self._create_item()

            values_payload = []
            for param, value in values_by_param.items():
                values_payload.append(
                    {"parameter_id": str(param.id), "value": value}
                )

            save_url = f"/api/reporting/workitems/{item.id}/save/"
            save_resp = self.client.post(save_url, {"values": values_payload}, format="json")
            self.assertEqual(save_resp.status_code, 200)

            gen_url = f"/api/reporting/workitems/{item.id}/generate-narrative/"
            gen_resp = self.client.post(gen_url, {})
            self.assertEqual(gen_resp.status_code, 200)

            narrative_url = f"/api/reporting/workitems/{item.id}/narrative/"
            narrative_resp = self.client.get(narrative_url)
            self.assertEqual(narrative_resp.status_code, 200)

            rendered = self._render_snapshot(gen_resp.data["narrative"])
            expected = self._load_snapshot(snapshot_file)
            self.assertEqual(rendered, expected, msg=f"Snapshot mismatch for {snapshot_file}")

            self._log_case(
                log_file,
                {"values": values_payload},
                gen_resp.data,
                narrative_resp.data,
            )
