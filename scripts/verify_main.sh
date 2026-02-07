#!/bin/bash
set -euo pipefail

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Activate VENV if present (prioritize backend/.venv)
if [ -f "backend/.venv/bin/activate" ]; then
    echo ">>> Activating backend/.venv..."
    source backend/.venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    echo ">>> Activating .venv..."
    source .venv/bin/activate
elif [ -f "backend/venv/bin/activate" ]; then
    echo ">>> Activating backend/venv..."
    source backend/venv/bin/activate
fi

# Create ARTIFACTS dir if not exists
mkdir -p ARTIFACTS

LOG_FILE="ARTIFACTS/verify_main.txt"

# Function to run command and log output
run_step() {
    echo ">>> Executing: $*" | tee -a "$LOG_FILE"
    "$@" 2>&1 | tee -a "$LOG_FILE"
}

# Clear previous log
echo "Verify Main Run - $(date)" > "$LOG_FILE"

echo ">>> 1. Compiling backend/apps..." | tee -a "$LOG_FILE"
run_step python3 -m compileall backend/apps

echo ">>> 2. Running manage.py check..." | tee -a "$LOG_FILE"
run_step python3 backend/manage.py check

echo ">>> 3. Running block library dry-run..." | tee -a "$LOG_FILE"
run_step python3 backend/manage.py import_block_library --dry-run

echo ">>> 4. Running templates v2 dry-run..." | tee -a "$LOG_FILE"
run_step python3 backend/manage.py import_templates_v2 --dry-run

echo ">>> 5. Running pytest (backend/apps/reporting)..." | tee -a "$LOG_FILE"
# Set PYTHONPATH to include backend and define settings module
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/backend"
export DJANGO_SETTINGS_MODULE="rims_backend.settings"

# using python3 -m pytest to ensure we use the python environment's pytest
run_step python3 -m pytest backend/apps/reporting

echo "VERIFY MAIN: PASS" | tee -a "$LOG_FILE"
