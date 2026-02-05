import csv
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.reporting.views import (
    ReportProfileViewSet,
    ReportParameterViewSet,
    ServiceReportProfileViewSet,
)
from apps.reporting.models import ServiceReportProfile
from apps.catalog.api import ServiceViewSet
from apps.catalog.models import Service
from apps.reporting.models import ReportProfile, ReportInstance, ReportValue
from apps.reporting.services.narrative_v1 import generate_report_narrative
from apps.patients.models import Patient
from apps.workflow.models import ServiceVisit, ServiceVisitItem

PACK_ROOT = settings.BASE_DIR.parent / "baseline_packs"

factory = APIRequestFactory()


@dataclass
class PackMetadata:
    slug: str
    profile_code: str
    profile_name: str
    modality: str
    version: str


def _read_first_profile_row(pack_dir: Path) -> Tuple[str, str, str]:
    profiles_path = pack_dir / "profiles.csv"
    if not profiles_path.exists():
        raise FileNotFoundError(f"profiles.csv missing in {pack_dir.name}")
    with profiles_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        first = next(reader)
        return first.get("code", ""), first.get("name", pack_dir.name), first.get("modality", "")


def list_packs() -> List[PackMetadata]:
    if not PACK_ROOT.exists():
        return []
    packs = []
    for path in sorted(PACK_ROOT.iterdir()):
        if not path.is_dir():
            continue
        try:
            code, name, modality = _read_first_profile_row(path)
        except Exception:
            continue
        version = "v1"
        if "_v" in path.name:
            version = path.name.split("_v")[-1]
            version = f"v{version}" if not version.startswith("v") else version
        packs.append(PackMetadata(slug=path.name, profile_code=code, profile_name=name, modality=modality, version=version))
    return packs


def _load_file_bytes(pack_slug: str, filename: str) -> bytes:
    path = PACK_ROOT / pack_slug / filename
    if not path.exists():
        raise FileNotFoundError(f"{filename} missing for pack {pack_slug}")
    return path.read_bytes()


def build_pack_zip(pack_slug: str) -> bytes:
    pack_dir = PACK_ROOT / pack_slug
    if not pack_dir.exists():
        raise FileNotFoundError(f"Pack {pack_slug} not found")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in ["profiles.csv", "parameters.csv", "services.csv", "linkage.csv", "README.md"]:
            file_path = pack_dir / filename
            if file_path.exists():
                arcname = f"{pack_dir.name}/{filename}"
                zf.writestr(arcname, file_path.read_bytes())
    return buffer.getvalue()


def _run_import(view_cls, action: str, file_bytes: bytes, dry_run: bool, user, url: str):
    upload = SimpleUploadedFile("import.csv", file_bytes, content_type="text/csv")
    request = factory.post(f"{url}?dry_run={'true' if dry_run else 'false'}", {"file": upload}, format="multipart")
    force_authenticate(request, user=user)
    view = view_cls.as_view({"post": action})
    response = view(request)
    return response.status_code, response.data


def _service_codes_from_pack(pack_slug: str) -> List[str]:
    services_path = PACK_ROOT / pack_slug / "services.csv"
    with services_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [row.get("code") for row in reader if row.get("code")]


def seed_pack(pack_slug: str, user, dry_run: bool = True) -> Dict:
    # Ensure files exist
    for fname in ["profiles.csv", "parameters.csv", "services.csv", "linkage.csv"]:
        if not (PACK_ROOT / pack_slug / fname).exists():
            raise FileNotFoundError(f"{fname} missing for pack {pack_slug}")

    steps = []
    errors: List[Dict] = []

    order = [
        (ReportProfileViewSet, "import_csv", "profiles.csv", "/reporting/profiles/import-csv/"),
        (ReportParameterViewSet, "import_csv", "parameters.csv", "/reporting/parameters/import-csv/"),
        (ServiceViewSet, "import_csv", "services.csv", "/services/import-csv/"),
        (ServiceReportProfileViewSet, "import_csv", "linkage.csv", "/reporting/service-profiles/import-csv/"),
    ]

    with transaction.atomic():
        for idx, (view_cls, action, filename, url) in enumerate(order):
            content = _load_file_bytes(pack_slug, filename)
            preview_status, preview_data = _run_import(view_cls, action, content, dry_run, user, url)
            step_result = {"file": filename, "status": preview_status, "data": preview_data}
            steps.append(step_result)
            if preview_status >= 400:
                errors.append({"file": filename, "detail": preview_data})

            # For dry-run: stage dependencies so subsequent previews find rows (rollback at end)
            if dry_run and preview_status < 400 and idx in (0, 2):  # profiles and services
                stage_status, stage_data = _run_import(view_cls, action, content, False, user, url)
                if stage_status >= 400:
                    errors.append({"file": filename, "detail": stage_data})

        if not dry_run and errors:
            transaction.set_rollback(True)
        if dry_run:
            transaction.set_rollback(True)

    result = {
        "pack": pack_slug,
        "dry_run": dry_run,
        "steps": steps,
        "errors": errors,
    }

    if not dry_run and not errors:
        result["verification"] = verify_pack(pack_slug)

    return result


def _count_parameters(profile_code: str) -> int:
    try:
        profile = ReportProfile.objects.get(code=profile_code)
    except ReportProfile.DoesNotExist:
        return 0
    return profile.parameters.count()


def _min_required(profile_code: str) -> int:
    mapping = {
        "USG_ABD": 8,
        "USG_KUB": 6,
        "USG_PELVIS": 8,
    }
    return mapping.get(profile_code, 1)


def _first_section_headings(profile_code: str, limit: int = 2) -> List[str]:
    try:
        profile = ReportProfile.objects.get(code=profile_code)
    except ReportProfile.DoesNotExist:
        return []
    params = profile.parameters.filter(narrative_role="finding").order_by("order")[:limit]
    return list(dict.fromkeys([p.section for p in params]))


def _create_smoke_instance(service_code: str, profile_code: str) -> Dict:
    try:
        service = Service.objects.get(code=service_code)
        profile = ReportProfile.objects.get(code=profile_code)
    except (Service.DoesNotExist, ReportProfile.DoesNotExist):
        return {"status": "fail", "reason": "service_or_profile_missing"}

    patient = Patient.objects.create(name="Baseline Pack Smoke Test", gender="O")
    visit = ServiceVisit.objects.create(patient=patient)
    item = ServiceVisitItem.objects.create(service_visit=visit, service=service)
    instance = ReportInstance.objects.create(service_visit_item=item, profile=profile)

    params = list(profile.parameters.filter(narrative_role="finding").order_by("order")[:2])
    for idx, param in enumerate(params):
        value = "Present" if param.parameter_type in ["dropdown", "checklist", "short_text", "long_text"] else "10"
        if param.parameter_type == "dropdown":
            opts = param.options.all()
            if opts:
                value = opts.first().value
        ReportValue.objects.create(report=instance, parameter=param, value=value)

    narrative = generate_report_narrative(str(instance.id))
    return {
        "status": "ok",
        "findings_text": narrative.get("findings_text", ""),
        "sections": [p.section for p in params],
    }


def verify_pack(pack_slug: str) -> Dict:
    service_codes = _service_codes_from_pack(pack_slug)
    profile_codes = []
    try:
        profiles_bytes = _load_file_bytes(pack_slug, "profiles.csv")
        reader = csv.DictReader(io.StringIO(profiles_bytes.decode("utf-8-sig")))
        profile_codes = [row.get("code") for row in reader if row.get("code")]
    except Exception:
        profile_codes = []

    checks = []

    # Linkage completeness
    linkage_failures = []
    for code in service_codes:
        try:
            service = Service.objects.get(code=code, is_active=True)
        except Service.DoesNotExist:
            linkage_failures.append(f"Service {code} missing")
            continue
        link_exists = ServiceReportProfile.objects.filter(service=service).exists()
        if not link_exists:
            linkage_failures.append(f"No profile linked for service {code}")
    checks.append({"name": "linkage", "status": "pass" if not linkage_failures else "fail", "details": linkage_failures})

    # Template completeness
    template_issues = []
    for p_code in profile_codes:
        count = _count_parameters(p_code)
        if count < _min_required(p_code):
            template_issues.append(f"Profile {p_code} has {count} parameters (< {_min_required(p_code)})")
    checks.append({"name": "template_completeness", "status": "pass" if not template_issues else "fail", "details": template_issues})

    # Narrative smoke test (only first service/profile pair)
    narrative_issue = []
    if service_codes and profile_codes:
        smoke = _create_smoke_instance(service_codes[0], profile_codes[0])
        if smoke.get("status") != "ok":
            narrative_issue.append(smoke.get("reason", "unknown_error"))
            findings_text = ""
            sections = []
        else:
            findings_text = smoke.get("findings_text", "")
            sections = smoke.get("sections", [])
            missing_sections = [sec for sec in sections if sec and sec not in findings_text]
            if missing_sections:
                narrative_issue.append(f"Missing sections in narrative: {', '.join(missing_sections)}")
    checks.append({"name": "narrative_smoke", "status": "pass" if not narrative_issue else "fail", "details": narrative_issue})

    overall_status = "pass" if all(c["status"] == "pass" for c in checks) else "fail"
    return {"status": overall_status, "checks": checks}
