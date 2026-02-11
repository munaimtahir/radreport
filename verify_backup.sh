#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_ROOT="${BACKUP_ROOT:-${PROJECT_ROOT}/backups}"
TARGET="${1:-$(date +%F)}"

if [[ -d "$TARGET" ]]; then
  BACKUP_DIR="$(cd "$TARGET" && pwd)"
else
  BACKUP_DIR="${BACKUP_ROOT}/${TARGET}"
fi

[[ -d "$BACKUP_DIR" ]] || { echo "Backup folder not found: $BACKUP_DIR" >&2; exit 1; }

required=(meta.json app_commit.txt app_status.txt backup.log)
for f in "${required[@]}"; do
  [[ -f "$BACKUP_DIR/$f" ]] || { echo "Missing required file: $f" >&2; exit 1; }
done

if [[ ! -f "$BACKUP_DIR/db.sql.gz" && ! -f "$BACKUP_DIR/db.sql.gz.enc" ]]; then
  echo "Missing database dump (db.sql.gz or db.sql.gz.enc)" >&2
  exit 1
fi
if [[ ! -f "$BACKUP_DIR/infra.tar.gz" && ! -f "$BACKUP_DIR/infra.tar.gz.enc" ]]; then
  echo "Missing infra archive (infra.tar.gz or infra.tar.gz.enc)" >&2
  exit 1
fi

if [[ -f "$BACKUP_DIR/checksums.sha256" ]]; then
  (cd "$BACKUP_DIR" && sha256sum -c checksums.sha256)
else
  echo "checksums.sha256 not found (optional)"
fi

echo "Backup verification OK: $BACKUP_DIR"
