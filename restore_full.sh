#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_ROOT="${BACKUP_ROOT:-${PROJECT_ROOT}/backups}"
DRY_RUN=0
ASSUME_YES=0
ALLOW_SYSTEM_CADDY_OVERWRITE=0
TARGET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1; shift ;;
    --yes)
      ASSUME_YES=1; shift ;;
    --allow-system-caddy-overwrite)
      ALLOW_SYSTEM_CADDY_OVERWRITE=1; shift ;;
    *)
      if [[ -z "$TARGET" ]]; then
        TARGET="$1"
        shift
      else
        echo "Unknown argument: $1" >&2
        exit 1
      fi
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 <backup-date-or-path> [--dry-run] [--yes] [--allow-system-caddy-overwrite]" >&2
  exit 1
fi

if [[ -d "$TARGET" ]]; then
  BACKUP_DIR="$(cd "$TARGET" && pwd)"
else
  BACKUP_DIR="${BACKUP_ROOT}/${TARGET}"
fi

[[ -d "$BACKUP_DIR" ]] || { echo "Backup directory not found: $BACKUP_DIR" >&2; exit 1; }

LOG_FILE="$BACKUP_DIR/restore.log"

log() {
  local level="$1"; shift
  local ts
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "[$ts] [$level] $*" | tee -a "$LOG_FILE"
}

fail() {
  log "ERROR" "$*"
  exit 1
}

detect_compose() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
  else
    fail "Docker Compose not found"
  fi
}

COMPOSE_CMD="$(detect_compose)"
compose() {
  # shellcheck disable=SC2086
  $COMPOSE_CMD "$@"
}

detect_db_service() {
  local svc
  mapfile -t services < <(compose ps --services --status running 2>/dev/null || true)
  for svc in "${services[@]}"; do
    [[ -n "$svc" ]] || continue
    if compose exec -T "$svc" sh -lc 'command -v psql >/dev/null 2>&1 && [ -n "${POSTGRES_DB:-}" ] && [ -n "${POSTGRES_USER:-}" ]' >/dev/null 2>>"$LOG_FILE"; then
      echo "$svc"
      return
    fi
  done
  fail "Could not detect Postgres service"
}

decrypt_if_needed() {
  local src="$1"
  if [[ "$src" != *.enc ]]; then
    echo "$src"
    return
  fi
  [[ -n "${BACKUP_ENCRYPTION_KEY:-}" ]] || fail "Encrypted artifact found but BACKUP_ENCRYPTION_KEY is not set"
  command -v openssl >/dev/null 2>&1 || fail "openssl is required for encrypted restore"
  local out
  out="$(mktemp -t backup-dec-XXXXXX)"
  openssl enc -d -aes-256-cbc -pbkdf2 -pass "pass:${BACKUP_ENCRYPTION_KEY}" -in "$src" -out "$out" >>"$LOG_FILE" 2>&1
  echo "$out"
}

confirm_restore() {
  if [[ "$ASSUME_YES" -eq 1 ]]; then
    return
  fi

  echo
  echo "WARNING: Destructive restore operation"
  echo "Backup: $BACKUP_DIR"
  echo "1) Infra files may be overwritten"
  echo "2) Media files may be replaced"
  echo "3) Database public schema will be dropped and recreated"
  read -r -p 'Type RESTORE NOW to continue: ' reply
  [[ "$reply" == "RESTORE NOW" ]] || fail "Confirmation failed"
}

restore_infra() {
  local infra_file stage sys_caddy
  infra_file=""
  [[ -f "$BACKUP_DIR/infra.tar.gz" ]] && infra_file="$BACKUP_DIR/infra.tar.gz"
  [[ -f "$BACKUP_DIR/infra.tar.gz.enc" ]] && infra_file="$BACKUP_DIR/infra.tar.gz.enc"

  if [[ -z "$infra_file" ]]; then
    log "WARN" "infra archive not found; skipping infra restore"
    return
  fi

  local infra_dec
  infra_dec="$(decrypt_if_needed "$infra_file")"
  stage="$(mktemp -d)"
  tar -xzf "$infra_dec" -C "$stage" >>"$LOG_FILE" 2>&1

  log "INFO" "Infra staging complete: $stage"

  local rel src dst
  for rel in docker-compose.yml .env.production Caddyfile; do
    src="$stage/$rel"
    dst="$PROJECT_ROOT/$rel"
    [[ -f "$src" ]] || continue
    if [[ -f "$dst" ]]; then
      diff -u "$dst" "$src" >>"$LOG_FILE" 2>&1 || true
    fi
    if [[ "$DRY_RUN" -eq 0 ]]; then
      cp -a "$src" "$dst"
      log "INFO" "Restored infra file: $rel"
    else
      log "INFO" "[dry-run] Would restore infra file: $rel"
    fi
  done

  sys_caddy="$stage/etc/caddy/Caddyfile"
  if [[ -f "$sys_caddy" ]]; then
    if [[ "$ALLOW_SYSTEM_CADDY_OVERWRITE" -eq 1 && "$DRY_RUN" -eq 0 ]]; then
      cp -a "$sys_caddy" /etc/caddy/Caddyfile
      log "INFO" "Restored system Caddyfile to /etc/caddy/Caddyfile"
    else
      log "WARN" "System Caddyfile present in backup but not applied. Use --allow-system-caddy-overwrite."
    fi
  fi

  rm -rf "$stage"
  [[ "$infra_dec" == "$infra_file" ]] || rm -f "$infra_dec"
}

restore_media() {
  local media_file media_dec
  media_file=""
  [[ -f "$BACKUP_DIR/media.tar.gz" ]] && media_file="$BACKUP_DIR/media.tar.gz"
  [[ -f "$BACKUP_DIR/media.tar.gz.enc" ]] && media_file="$BACKUP_DIR/media.tar.gz.enc"

  if [[ -z "$media_file" ]]; then
    log "WARN" "media archive not found; skipping media restore"
    return
  fi

  media_dec="$(decrypt_if_needed "$media_file")"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    tar -xzf "$media_dec" -C "$PROJECT_ROOT" >>"$LOG_FILE" 2>&1
    log "INFO" "Media restored"
  else
    log "INFO" "[dry-run] Would restore media from $media_file"
  fi
  [[ "$media_dec" == "$media_file" ]] || rm -f "$media_dec"
}

restore_db() {
  local db_service db_name db_user db_dump db_dec
  db_service="$(detect_db_service)"
  db_name="$(compose exec -T "$db_service" sh -lc 'printf "%s" "${POSTGRES_DB:-}"' 2>>"$LOG_FILE")"
  db_user="$(compose exec -T "$db_service" sh -lc 'printf "%s" "${POSTGRES_USER:-}"' 2>>"$LOG_FILE")"

  db_dump=""
  [[ -f "$BACKUP_DIR/db.sql.gz" ]] && db_dump="$BACKUP_DIR/db.sql.gz"
  [[ -f "$BACKUP_DIR/db.sql.gz.enc" ]] && db_dump="$BACKUP_DIR/db.sql.gz.enc"
  [[ -n "$db_dump" ]] || fail "db.sql.gz (or .enc) not found in backup"

  db_dec="$(decrypt_if_needed "$db_dump")"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "INFO" "[dry-run] Would reset and restore database ${db_name} on service ${db_service}"
    [[ "$db_dec" == "$db_dump" ]] || rm -f "$db_dec"
    return
  fi

  compose exec -T "$db_service" sh -lc "psql -v ON_ERROR_STOP=1 -U \"${db_user}\" -d postgres -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${db_name}' AND pid <> pg_backend_pid();\"" >>"$LOG_FILE" 2>&1
  compose exec -T "$db_service" sh -lc "psql -v ON_ERROR_STOP=1 -U \"${db_user}\" -d \"${db_name}\" -c \"DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;\"" >>"$LOG_FILE" 2>&1
  gunzip -c "$db_dec" | compose exec -T "$db_service" sh -lc "psql -v ON_ERROR_STOP=1 -U \"${db_user}\" -d \"${db_name}\"" >>"$LOG_FILE" 2>&1

  log "INFO" "Database restore complete"
  [[ "$db_dec" == "$db_dump" ]] || rm -f "$db_dec"
}

smoke_checks() {
  local db_service db_name db_user
  db_service="$(detect_db_service)"
  db_name="$(compose exec -T "$db_service" sh -lc 'printf "%s" "${POSTGRES_DB:-}"' 2>>"$LOG_FILE")"
  db_user="$(compose exec -T "$db_service" sh -lc 'printf "%s" "${POSTGRES_USER:-}"' 2>>"$LOG_FILE")"

  if compose exec -T "$db_service" sh -lc "psql -U \"${db_user}\" -d \"${db_name}\" -c 'SELECT 1'" >/dev/null 2>>"$LOG_FILE"; then
    log "INFO" "Smoke: DB connection OK"
  else
    log "ERROR" "Smoke: DB connection failed"
  fi

  if curl -fsS "${BACKUP_HEALTHCHECK_URL:-http://127.0.0.1:8015/api/health/}" >/dev/null 2>>"$LOG_FILE"; then
    log "INFO" "Smoke: Health endpoint OK"
  else
    log "WARN" "Smoke: Health endpoint failed"
  fi

  [[ -f "$PROJECT_ROOT/docker-compose.yml" ]] && log "INFO" "Smoke: docker-compose.yml exists" || log "WARN" "Smoke: docker-compose.yml missing"
  [[ -d "$PROJECT_ROOT/backend/media" ]] && log "INFO" "Smoke: media dir exists" || log "WARN" "Smoke: media dir missing"
}

log "INFO" "Restore requested for ${BACKUP_DIR} (dry_run=${DRY_RUN})"
confirm_restore
restore_infra
restore_media
restore_db
smoke_checks

cat <<NOTES | tee -a "$LOG_FILE"
Recovery notes:
1) Verify application status: docker compose ps
2) Reload Caddy if configuration changed: sudo systemctl reload caddy
3) Re-run smoke: curl -f http://127.0.0.1:8015/api/health/
4) Review restore log: ${LOG_FILE}
NOTES

log "INFO" "Restore workflow finished"
