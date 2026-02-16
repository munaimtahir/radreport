#!/usr/bin/env bash
set -euo pipefail

PROJECT="radreport"
docker compose -p "$PROJECT" restart
