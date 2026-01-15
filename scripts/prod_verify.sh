#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <domain> [jwt_token]" >&2
  exit 2
fi

DOMAIN="$1"
TOKEN="${2:-}"

curl -fsS "https://${DOMAIN}/api/health/" >/dev/null

echo "Running USG smoke command..."
SMOKE_OUTPUT=$(python manage.py smoke_prod_usg)
echo "$SMOKE_OUTPUT"

PDF_ABS=$(echo "$SMOKE_OUTPUT" | rg -o "PDF: .*" | sed "s/PDF: //" || true)
if [[ -z "$PDF_ABS" ]]; then
  echo "Could not find PDF path in smoke output." >&2
  exit 1
fi

MEDIA_ROOT=$(python - <<'PY'
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()
from django.conf import settings
print(settings.MEDIA_ROOT)
PY
)

PDF_REL=$(python - <<PY
from pathlib import Path
media_root = Path("$MEDIA_ROOT").resolve()
pdf_path = Path("$PDF_ABS").resolve()
try:
    rel = pdf_path.relative_to(media_root)
    print(rel.as_posix())
except Exception:
    print(pdf_path.name)
PY
)

if [[ -n "$TOKEN" ]]; then
  curl -fsS -H "Authorization: Bearer ${TOKEN}" "https://${DOMAIN}/api/health/auth/" >/dev/null
fi

curl -fsSI "https://${DOMAIN}/media/${PDF_REL}" >/dev/null

echo "Smoke verification OK: https://${DOMAIN}/media/${PDF_REL}"
