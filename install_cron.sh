#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_LOG="/var/log/app_backup_cron.log"
CRON_EXPR="0 2 * * *"
CRON_CMD="cd ${PROJECT_ROOT} && BACKUP_TRIGGER=cron BACKUP_CREATED_BY=system ${PROJECT_ROOT}/backup_full.sh --trigger cron --created-by system >> ${CRON_LOG} 2>&1"
CRON_LINE="${CRON_EXPR} ${CRON_CMD}"

existing="$(crontab -l 2>/dev/null || true)"
cleaned="$(printf '%s\n' "$existing" | grep -v -F "${PROJECT_ROOT}/backup_full.sh" || true)"

{
  printf '%s\n' "$cleaned"
  printf '%s\n' "$CRON_LINE"
} | sed '/^$/d' | awk '!seen[$0]++' | crontab -

echo "Installed cron entry: ${CRON_LINE}"
crontab -l
