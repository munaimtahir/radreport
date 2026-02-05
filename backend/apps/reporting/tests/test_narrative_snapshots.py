import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.reporting.models import ReportProfile, ReportParameter, ReportParameterOption
from apps.reporting.services.narrative_v1 import generate_report_narrative


SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots"


class NarrativeSnapshotTests(TestCase):
    def setUp(self):
        self.profile = ReportProfile.objects.create(
            code="SNAP_USG_ABD",
            name="USG Abdomen Snapshot",
            modality="USG",
            enable_narrative=True,
        )

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
        findings = narrative["findings_text"] or ""
        impression = narrative["impression_text"] or ""
        limitations = narrative["limitations_text"] or ""
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
        path = SNAPSHOT_DIR / filename
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()

    def _build_values(self, values_by_param):
        values = []
        for param, raw_val in values_by_param.items():
            values.append(
                MagicMock(
                    parameter_id=param.id,
                    value=raw_val,
                    parameter=param,
                )
            )
        return values

    def test_narrative_snapshots(self):
        cases = [
            (
                "case_01.txt",
                {
                    self.p_liver_size: "14",
                    self.p_liver_echo: "normal",
                    self.p_gb_stones: "false",
                    self.p_gb_wall: "3",
                    self.p_kidney_hydro: "none",
                    self.p_kidney_stones: '["right", "left"]',
                    self.p_impression: "No acute abnormality",
                },
            ),
            (
                "case_02.txt",
                {
                    self.p_liver_echo: "increased",
                    self.p_gb_stones: "true",
                    self.p_kidney_hydro: "mild",
                    self.p_kidney_stones: '["right"]',
                    self.p_impression: "Fatty liver suspected",
                    self.p_limitations: "Limited by bowel gas",
                },
            ),
            (
                "case_03.txt",
                {
                    self.p_liver_size: "12",
                    self.p_liver_echo: "na",
                    self.p_gb_stones: "false",
                    self.p_kidney_hydro: "none",
                    self.p_kidney_stones: "[]",
                },
            ),
            (
                "case_04.txt",
                {
                    self.p_liver_size: "16",
                    self.p_liver_echo: "normal",
                    self.p_gb_stones: "true",
                    self.p_gb_wall: "0",
                    self.p_kidney_hydro: "none",
                    self.p_kidney_stones: "[]",
                    self.p_impression: "Cholelithiasis",
                },
            ),
            (
                "case_05.txt",
                {
                    self.p_liver_size: "13",
                    self.p_liver_echo: "na",
                    self.p_gb_stones: "false",
                    self.p_gb_wall: "4",
                    self.p_kidney_hydro: "moderate",
                    self.p_kidney_stones: '["left"]',
                    self.p_impression: "Left renal calculus",
                    self.p_limitations: "Patient uncooperative",
                },
            ),
            (
                "case_06.txt",
                {
                    self.p_liver_echo: "",
                    self.p_gb_stones: "false",
                    self.p_kidney_hydro: "none",
                    self.p_kidney_stones: "[]",
                    self.p_impression: "Normal ultrasound",
                },
            ),
            (
                "case_07.txt",
                {
                    self.p_liver_size: "15",
                    self.p_liver_echo: "increased",
                    self.p_gb_stones: "true",
                    self.p_gb_wall: "5",
                    self.p_kidney_hydro: "severe",
                    self.p_kidney_stones: '["right", "left"]',
                    self.p_impression: "Severe hydronephrosis",
                    self.p_limitations: "Limited by obesity",
                },
            ),
            (
                "case_08.txt",
                {
                    self.p_kidney_hydro: "mild",
                    self.p_kidney_stones: '["left"]',
                },
            ),
            (
                "case_09.txt",
                {
                    self.p_liver_echo: "normal",
                    self.p_gb_stones: "false",
                    self.p_gb_wall: "2",
                    self.p_kidney_hydro: "none",
                    self.p_kidney_stones: "[]",
                    self.p_impression: "Gallbladder polyp",
                    self.p_limitations: "Limited by patient motion",
                },
            ),
            (
                "case_10.txt",
                {
                    self.p_liver_size: "11",
                    self.p_liver_echo: "normal",
                    self.p_gb_stones: "true",
                    self.p_gb_wall: "3",
                    self.p_kidney_hydro: "moderate",
                    self.p_kidney_stones: '["right"]',
                    self.p_impression: "Right renal calculus and cholelithiasis",
                    self.p_limitations: "Suboptimal due to bowel gas",
                },
            ),
        ]

        for filename, values_by_param in cases:
            mock_instance = MagicMock()
            mock_instance.profile = self.profile
            mock_instance.id = "snapshot-id"

            with patch(
                "apps.reporting.services.narrative_v1.ReportInstance.objects.select_related"
            ) as mock_select:
                mock_select.return_value.get.return_value = mock_instance
                with patch(
                    "apps.reporting.services.narrative_v1.ReportValue.objects.filter"
                ) as mock_values:
                    mock_values.return_value = self._build_values(values_by_param)
                    narrative = generate_report_narrative("snapshot-id")

            rendered = self._render_snapshot(narrative)
            expected = self._load_snapshot(filename)
            self.assertEqual(
                rendered,
                expected,
                msg=f"Snapshot mismatch for {filename}",
            )
