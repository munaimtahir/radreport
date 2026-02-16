#!/usr/bin/env bash
set -euo pipefail

PROJECT="radreport"
docker ps --filter "label=com.docker.compose.project=$PROJECT"
