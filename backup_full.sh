#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_ROOT="${BACKUP_ROOT:-${PROJECT_ROOT}/backups}"
TRIGGER="${BACKUP_TRIGGER:-cron}"
CREATED_BY="${BACKUP_CREATED_BY:-system}"
FORCE=0
DELETABLE="${BACKUP_DELETABLE:-false}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --trigger)
      TRIGGER="$2"; shift 2 ;;
    --created-by)
      CREATED_BY="$2"; shift 2 ;;
    --force)
      FORCE=1; shift ;;
    --deletable)
      DELETABLE="true"; shift ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1 ;;
  esac
done

DATE_DIR="$(date +%F)"
BACKUP_DIR="${BACKUP_ROOT}/${DATE_DIR}"
LOG_FILE="${BACKUP_DIR}/backup.log"
META_FILE="${BACKUP_DIR}/meta.json"
CHECKSUMS_FILE="${BACKUP_DIR}/checksums.sha256"

mkdir -p "$BACKUP_DIR"
chmod 750 "$BACKUP_ROOT" "$BACKUP_DIR" || true

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

DB_SUCCESS=false
MEDIA_SUCCESS=false
INFRA_SUCCESS=false
ERRORS=()
ENCRYPTION_ENABLED=false

if [[ -f "$META_FILE" && "$FORCE" -ne 1 ]]; then
  fail "Backup for ${DATE_DIR} already exists. Use --force to overwrite."
fi

run_db_backup() {
  local db_service db_name db_user db_dump
  db_dump="$BACKUP_DIR/db.sql.gz"

  mapfile -t services < <(compose ps --services --status running 2>/dev/null || true)
  for svc in "${services[@]}"; do
    [[ -n "$svc" ]] || continue
    if compose exec -T "$svc" sh -lc 'command -v pg_dump >/dev/null 2>&1 && [ -n "${POSTGRES_DB:-}" ] && [ -n "${POSTGRES_USER:-}" ]' >/dev/null 2>>"$LOG_FILE"; then
      db_service="$svc"
      break
    fi
  done

  [[ -n "${db_service:-}" ]] || fail "Could not auto-detect Postgres service from docker compose"

  db_name="$(compose exec -T "$db_service" sh -lc 'printf "%s" "${POSTGRES_DB:-}"' 2>>"$LOG_FILE")"
  db_user="$(compose exec -T "$db_service" sh -lc 'printf "%s" "${POSTGRES_USER:-}"' 2>>"$LOG_FILE")"
  [[ -n "$db_name" && -n "$db_user" ]] || fail "Failed to read POSTGRES_DB/POSTGRES_USER from DB service"

  log "INFO" "Detected DB service '${db_service}' (db=${db_name}, user=${db_user})"
  if compose exec -T "$db_service" sh -lc "pg_dump --clean --if-exists --no-owner --no-privileges -U \"${db_user}\" -d \"${db_name}\"" 2>>"$LOG_FILE" | gzip -c > "$db_dump"; then
    DB_SUCCESS=true
    log "INFO" "Database dump written: $db_dump"
  else
    fail "Database backup failed"
  fi
}

encrypt_artifact() {
  local path="$1"
  if [[ -z "${BACKUP_ENCRYPTION_KEY:-}" ]]; then
    echo "$path"
    return
  fi
  ENCRYPTION_ENABLED=true
  command -v openssl >/dev/null 2>&1 || fail "BACKUP_ENCRYPTION_KEY set but openssl not found"
  local out="${path}.enc"
  openssl enc -aes-256-cbc -pbkdf2 -salt -pass "pass:${BACKUP_ENCRYPTION_KEY}" -in "$path" -out "$out" >>"$LOG_FILE" 2>&1
  rm -f "$path"
  echo "$out"
}

run_media_backup() {
  local media_src="${PROJECT_ROOT}/backend/media"
  local media_tar="$BACKUP_DIR/media.tar.gz"

  if [[ ! -d "$media_src" ]]; then
    log "WARN" "Media directory not found; skipping (${media_src})"
    MEDIA_SUCCESS=false
    return
  fi

  tar -czpf "$media_tar" -C "$PROJECT_ROOT" backend/media >>"$LOG_FILE" 2>&1
  media_tar="$(encrypt_artifact "$media_tar")"
  MEDIA_SUCCESS=true
  log "INFO" "Media archive written: ${media_tar}"
}

run_infra_backup() {
  local stage infra_tar caddy_src
  stage="$(mktemp -d)"
  infra_tar="$BACKUP_DIR/infra.tar.gz"

  copy_if_exists() {
    local src="$1" rel="$2"
    if [[ -f "$src" ]]; then
      mkdir -p "$stage/$(dirname "$rel")"
      cp -a "$src" "$stage/$rel"
    fi
  }

  copy_if_exists "$PROJECT_ROOT/docker-compose.yml" "docker-compose.yml"
  copy_if_exists "$PROJECT_ROOT/.env.production" ".env.production"

  if [[ -f "/etc/caddy/Caddyfile" ]]; then
    caddy_src="/etc/caddy/Caddyfile"
    copy_if_exists "$caddy_src" "etc/caddy/Caddyfile"
  elif [[ -f "$PROJECT_ROOT/Caddyfile" ]]; then
    caddy_src="$PROJECT_ROOT/Caddyfile"
    copy_if_exists "$caddy_src" "Caddyfile"
  else
    caddy_src="none"
  fi

  copy_if_exists "$PROJECT_ROOT/backup_full.sh" "scripts/backup_full.sh"
  copy_if_exists "$PROJECT_ROOT/restore_full.sh" "scripts/restore_full.sh"
  copy_if_exists "$PROJECT_ROOT/install_cron.sh" "scripts/install_cron.sh"
  copy_if_exists "$PROJECT_ROOT/verify_backup.sh" "scripts/verify_backup.sh"
  copy_if_exists "$PROJECT_ROOT/BACKUP_README.md" "BACKUP_README.md"

  tar -czpf "$infra_tar" -C "$stage" . >>"$LOG_FILE" 2>&1
  rm -rf "$stage"

  infra_tar="$(encrypt_artifact "$infra_tar")"
  INFRA_SUCCESS=true
  log "INFO" "Infra archive written: ${infra_tar} (caddy_source=${caddy_src})"
}

write_git_snapshot() {
  local commit status_summary untracked_count dirty
  if git -C "$PROJECT_ROOT" rev-parse --verify HEAD >/dev/null 2>&1; then
    commit="$(git -C "$PROJECT_ROOT" rev-parse HEAD)"
  else
    commit="unknown"
  fi
  printf "%s\n" "$commit" > "$BACKUP_DIR/app_commit.txt"

  status_summary="$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null || true)"
  untracked_count="$(printf "%s\n" "$status_summary" | grep -c '^??' || true)"
  if [[ -z "$status_summary" ]]; then
    dirty="false"
  else
    dirty="true"
  fi
  {
    printf "clean=%s\n" "$( [[ "$dirty" == "false" ]] && echo true || echo false )"
    printf "dirty=%s\n" "$dirty"
    printf "untracked_count=%s\n" "$untracked_count"
  } > "$BACKUP_DIR/app_status.txt"
}

write_meta() {
  local db_size media_size infra_size git_commit
  git_commit="$(cat "$BACKUP_DIR/app_commit.txt" 2>/dev/null || echo unknown)"

  db_size=0
  media_size=0
  infra_size=0
  [[ -f "$BACKUP_DIR/db.sql.gz" ]] && db_size="$(stat -c%s "$BACKUP_DIR/db.sql.gz")"
  [[ -f "$BACKUP_DIR/db.sql.gz.enc" ]] && db_size="$(stat -c%s "$BACKUP_DIR/db.sql.gz.enc")"
  [[ -f "$BACKUP_DIR/media.tar.gz" ]] && media_size="$(stat -c%s "$BACKUP_DIR/media.tar.gz")"
  [[ -f "$BACKUP_DIR/media.tar.gz.enc" ]] && media_size="$(stat -c%s "$BACKUP_DIR/media.tar.gz.enc")"
  [[ -f "$BACKUP_DIR/infra.tar.gz" ]] && infra_size="$(stat -c%s "$BACKUP_DIR/infra.tar.gz")"
  [[ -f "$BACKUP_DIR/infra.tar.gz.enc" ]] && infra_size="$(stat -c%s "$BACKUP_DIR/infra.tar.gz.enc")"

  cat > "$META_FILE" <<JSON
{
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "created_by": "${CREATED_BY}",
  "trigger": "${TRIGGER}",
  "git_commit": "${git_commit}",
  "db_dump_size_bytes": ${db_size},
  "media_size_bytes": ${media_size},
  "infra_size_bytes": ${infra_size},
  "success": {
    "db": ${DB_SUCCESS},
    "media": ${MEDIA_SUCCESS},
    "infra": ${INFRA_SUCCESS}
  },
  "errors": [],
  "encryption_enabled": ${ENCRYPTION_ENABLED},
  "deletable": ${DELETABLE}
}
JSON
}

write_checksums() {
  : > "$CHECKSUMS_FILE"
  local f
  for f in db.sql.gz db.sql.gz.enc media.tar.gz media.tar.gz.enc infra.tar.gz infra.tar.gz.enc app_commit.txt app_status.txt meta.json; do
    if [[ -f "$BACKUP_DIR/$f" ]]; then
      (cd "$BACKUP_DIR" && sha256sum "$f") >> "$CHECKSUMS_FILE"
    fi
  done
}

apply_retention() {
  mapfile -t cron_dirs < <(find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -name '????-??-??' | sort)
  local keep=()
  local dir

  for dir in "${cron_dirs[@]}"; do
    if [[ -f "$dir/meta.json" ]] && python3 - "$dir/meta.json" <<'PY' >/dev/null 2>&1
import json,sys
p=sys.argv[1]
try:
    m=json.load(open(p))
    ok=(m.get("trigger")=="cron" and bool(m.get("success",{}).get("db")))
    raise SystemExit(0 if ok else 1)
except Exception:
    raise SystemExit(1)
PY
    then
      keep+=("$dir")
    fi
  done

  local total="${#keep[@]}"
  if (( total <= 7 )); then
    log "INFO" "Retention: ${total} cron backups found, nothing deleted"
    return
  fi

  local delete_count=$(( total - 7 ))
  local i
  for (( i=0; i<delete_count; i++ )); do
    rm -rf "${keep[$i]}"
    log "INFO" "Retention deleted old cron backup: ${keep[$i]}"
  done
}

log "INFO" "Backup started at ${BACKUP_DIR}"
run_db_backup
run_media_backup
run_infra_backup
write_git_snapshot
write_meta
write_checksums

if [[ "$TRIGGER" == "cron" ]]; then
  apply_retention
fi

log "INFO" "Backup completed successfully"
