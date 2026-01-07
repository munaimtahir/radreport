#!/usr/bin/env python3
"""
Workflow smoke test using public API endpoints.
Requires a valid user with permissions. Provide credentials via env:
  BASE_URL=https://rims.alshifalab.pk RIMS_USER=... RIMS_PASS=... python scripts/smoke_workflow.py
"""
import json
import os
import sys
from urllib.parse import urljoin

import requests


def fail(msg: str, code: int = 1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def main():
    base_url = os.environ.get("BASE_URL", "https://rims.alshifalab.pk").rstrip("/") + "/"
    username = os.environ.get("RIMS_USER")
    password = os.environ.get("RIMS_PASS")

    if not username or not password:
        fail("Missing RIMS_USER/RIMS_PASS in env")

    print(f"==> Workflow smoke test against {base_url}")

    # 1) Health
    r = requests.get(urljoin(base_url, "api/health/"), timeout=8)
    r.raise_for_status()
    if r.json().get("status") != "ok":
        fail("Health check not OK")

    # 2) Auth
    token_url = urljoin(base_url, "api/auth/token/")
    r = requests.post(token_url, json={"username": username, "password": password}, timeout=8)
    r.raise_for_status()
    access = r.json().get("access")
    if not access:
        fail("No access token returned")
    headers = {"Authorization": f"Bearer {access}", "Content-Type": "application/json"}

    # 3) List services (catalog)
    r = requests.get(urljoin(base_url, "api/workflow/service-catalog/"), headers=headers, timeout=8)
    r.raise_for_status()
    services = r.json()
    if not isinstance(services, list):
        fail("Service catalog did not return a list")
    service_id = services[0]["id"] if services else None
    if not service_id:
        fail("No active services in catalog")

    # 4) Create patient (simple)
    patient_body = {
        "name": "Smoke Test",
        "mrn": "SMK" + os.urandom(3).hex(),
        "age": 30,
        "gender": "M",
        "phone": "000-0000",
    }
    r = requests.post(urljoin(base_url, "api/patients/"), headers=headers, data=json.dumps(patient_body), timeout=8)
    r.raise_for_status()
    patient = r.json()
    patient_id = patient.get("id")
    if not patient_id:
        fail("Failed to create patient")

    # 5) Create workflow service visit
    visit_body = {
        "patient_id": patient_id,
        "service_id": service_id,
        "payment_method": "cash",
    }
    r = requests.post(urljoin(base_url, "api/workflow/visits/"), headers=headers, data=json.dumps(visit_body), timeout=8)
    r.raise_for_status()
    visit = r.json()
    visit_id = visit.get("id")
    if not visit_id:
        fail("Failed to create service visit")

    # 6) Transition through statuses
    for to_status in ["IN_PROGRESS", "PENDING_VERIFICATION", "PUBLISHED"]:
        r = requests.post(
            urljoin(base_url, f"api/workflow/visits/{visit_id}/transition_status/"),
            headers=headers,
            data=json.dumps({"to_status": to_status}),
            timeout=8,
        )
        r.raise_for_status()

    print("OK: Workflow smoke completed")


if __name__ == "__main__":
    main()

