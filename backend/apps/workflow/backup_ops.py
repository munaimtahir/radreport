import datetime as dt
import json
import os
import re
import shutil
import socket
import subprocess
import tarfile
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Optional

import fcntl
from django.conf import settings
from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

EXECUTOR = ThreadPoolExecutor(max_workers=2)
JOBS_LOCK = threading.Lock()
JOBS: dict[str, dict] = {}


ProgressReporter = Optional[Callable[[int, str, str], None]]


def _require_admin(request):
    if not request.user.is_superuser:
        return Response({"detail": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
    return None


def _env_db_config():
    db = settings.DATABASES.get("default", {})
    return {
        "name": os.getenv("DB_NAME") or db.get("NAME") or "rims",
        "user": os.getenv("DB_USER") or db.get("USER") or "rims",
        "password": os.getenv("DB_PASSWORD") or db.get("PASSWORD") or "",
        "host": os.getenv("DB_HOST") or db.get("HOST") or "db",
        "port": str(os.getenv("DB_PORT") or db.get("PORT") or "5432"),
    }


def _resolve_backup_root() -> Path:
    requested = Path(os.getenv("BACKUP_ROOT", str(Path(settings.MEDIA_ROOT) / "backups")))
    fallback = Path("/backups")

    for candidate in (requested, fallback):
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return candidate
        except Exception:
            continue

    raise RuntimeError("No writable backup root available")


def _jobs_dir(root: Path) -> Path:
    out = root / ".jobs"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _job_path(root: Path, job_id: str) -> Path:
    return _jobs_dir(root) / f"{job_id}.json"


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


def _project_root() -> Path:
    explicit = os.getenv("PROJECT_ROOT")
    if explicit:
        return Path(explicit)
    return Path(settings.BASE_DIR)


def _run(cmd, env=None, input_text=None, cwd=None):
    completed = subprocess.run(
        cmd,
        input=input_text,
        text=True,
        capture_output=True,
        env=env,
        cwd=cwd,
        check=False,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


@contextmanager
def _lock(root: Path, name: str):
    lock_dir = root / ".locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"{name}.lock"
    handle = open(lock_path, "w", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        raise RuntimeError(f"{name} operation already running")
    try:
        yield
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _dir_size_bytes(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except FileNotFoundError:
                pass
    return total


def _list_backups(root: Path):
    backups = []
    if not root.exists():
        return backups

    for entry in sorted(root.iterdir(), key=lambda x: x.name, reverse=True):
        if not entry.is_dir() or not DATE_DIR_RE.match(entry.name):
            continue
        db_file = entry / "db.sql.gz"
        media_file = entry / "media.tar.gz"
        infra_file = entry / "infra.tar.gz"
        commit_file = entry / "app_commit.txt"
        backups.append(
            {
                "date": entry.name,
                "path": str(entry),
                "has_db": db_file.exists(),
                "has_media": media_file.exists(),
                "has_infra": infra_file.exists(),
                "has_commit": commit_file.exists(),
                "auto_created": (entry / ".auto_backup").exists(),
                "size_bytes": _dir_size_bytes(entry),
                "modified_at": dt.datetime.fromtimestamp(entry.stat().st_mtime, tz=dt.timezone.utc).isoformat(),
            }
        )
    return backups


def _tail_file(path: Path, limit: int = 20):
    if not path.exists() or not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return lines[-limit:]
    except Exception:
        return []


def _apply_retention(root: Path, keep: int = 7):
    candidates = []
    for entry in sorted(root.iterdir(), key=lambda x: x.name):
        if entry.is_dir() and DATE_DIR_RE.match(entry.name) and (entry / ".auto_backup").exists():
            candidates.append(entry)

    if len(candidates) <= keep:
        return []

    to_delete = candidates[: len(candidates) - keep]
    deleted = []
    for old in to_delete:
        shutil.rmtree(old, ignore_errors=True)
        deleted.append(old.name)
    return deleted


def _persist_job(root: Path, payload: dict):
    _job_path(root, payload["id"]).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _create_job(root: Path, job_type: str, requested_by: str, params: dict):
    now = dt.datetime.now(tz=dt.timezone.utc).isoformat()
    payload = {
        "id": uuid.uuid4().hex,
        "type": job_type,
        "status": "queued",
        "progress": 0,
        "step": "queued",
        "message": "Waiting for worker",
        "params": params,
        "requested_by": requested_by,
        "requested_at": now,
        "started_at": None,
        "finished_at": None,
        "result": None,
        "error": None,
    }
    with JOBS_LOCK:
        JOBS[payload["id"]] = payload
    _persist_job(root, payload)
    return payload


def _update_job(root: Path, job_id: str, **fields):
    with JOBS_LOCK:
        payload = JOBS.get(job_id)
        if payload is None:
            file_path = _job_path(root, job_id)
            if not file_path.exists():
                return None
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            JOBS[job_id] = payload
        payload.update(fields)
        updated = dict(payload)
    _persist_job(root, updated)
    return updated


def _get_job(root: Path, job_id: str):
    with JOBS_LOCK:
        payload = JOBS.get(job_id)
        if payload:
            return dict(payload)
    path = _job_path(root, job_id)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    with JOBS_LOCK:
        JOBS[job_id] = payload
    return payload


def _list_recent_jobs(root: Path, limit: int = 25):
    items = []
    for p in _jobs_dir(root).glob("*.json"):
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
            items.append(payload)
        except Exception:
            continue
    items.sort(key=lambda x: x.get("requested_at") or "", reverse=True)
    return items[:limit]


def _progress(root: Path, job_id: str, percent: int, step: str, message: str):
    _update_job(root, job_id, progress=max(0, min(100, int(percent))), step=step, message=message)


def _run_job(root: Path, job_id: str, task: Callable[[ProgressReporter], dict]):
    _update_job(
        root,
        job_id,
        status="running",
        started_at=dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        step="starting",
        message="Job started",
    )

    try:
        def reporter(percent: int, step: str, message: str):
            _progress(root, job_id, percent, step, message)

        result = task(reporter)
        _update_job(
            root,
            job_id,
            status="succeeded",
            progress=100,
            step="completed",
            message="Job completed",
            result=result,
            finished_at=dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        )
    except Exception as exc:
        _update_job(
            root,
            job_id,
            status="failed",
            step="failed",
            message="Job failed",
            error=str(exc),
            finished_at=dt.datetime.now(tz=dt.timezone.utc).isoformat(),
        )


def _submit_job(root: Path, job_type: str, requested_by: str, params: dict, task_factory: Callable[[], Callable[[ProgressReporter], dict]]):
    payload = _create_job(root, job_type, requested_by, params)
    EXECUTOR.submit(_run_job, root, payload["id"], task_factory())
    return payload


def _perform_backup(root: Path, force: bool = False, reporter: ProgressReporter = None):
    if reporter:
        reporter(5, "init", "Preparing backup directory")

    today = dt.date.today().isoformat()
    backup_dir = root / today
    db_dump = backup_dir / "db.sql.gz"

    if backup_dir.exists() and db_dump.exists() and not force:
        if reporter:
            reporter(100, "skipped", "Backup already exists for today")
        return {
            "date": today,
            "status": "skipped",
            "message": "Backup already exists for today. Use force=true to rebuild.",
        }

    backup_dir.mkdir(parents=True, exist_ok=True)
    db_cfg = _env_db_config()

    if reporter:
        reporter(20, "database", "Creating database dump")

    env = os.environ.copy()
    env["PGPASSWORD"] = db_cfg["password"]

    pg_cmd = [
        "pg_dump",
        "-h",
        db_cfg["host"],
        "-p",
        db_cfg["port"],
        "-U",
        db_cfg["user"],
        "-d",
        db_cfg["name"],
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-privileges",
    ]

    with open(db_dump, "wb") as out_f:
        p1 = subprocess.Popen(pg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        p2 = subprocess.Popen(["gzip", "-c"], stdin=p1.stdout, stdout=out_f, stderr=subprocess.PIPE)
        if p1.stdout:
            p1.stdout.close()
        _, pg_err = p1.communicate()
        _, gz_err = p2.communicate()

    if p1.returncode != 0 or p2.returncode != 0:
        raise RuntimeError(
            f"Database dump failed: {pg_err.decode('utf-8', 'ignore').strip()} {gz_err.decode('utf-8', 'ignore').strip()}".strip()
        )

    media_root = Path(settings.MEDIA_ROOT)
    if media_root.exists():
        if reporter:
            reporter(50, "media", "Archiving media files")
        media_archive = backup_dir / "media.tar.gz"
        rc, _, err = _run(["tar", "-czpf", str(media_archive), "-C", str(media_root.parent), media_root.name])
        if rc != 0:
            raise RuntimeError(f"Media backup failed: {err}")

    if reporter:
        reporter(70, "infra", "Archiving infrastructure files")

    infra_archive = backup_dir / "infra.tar.gz"
    project_root = _project_root()
    infra_candidates = [
        (project_root / "docker-compose.yml", "docker-compose.yml"),
        (project_root / ".env.production", ".env.production"),
        (project_root / "Caddyfile", "Caddyfile"),
        (Path("/etc/caddy/Caddyfile"), "etc/caddy/Caddyfile"),
        (project_root / "backup_full.sh", "scripts/backup_full.sh"),
        (project_root / "restore_full.sh", "scripts/restore_full.sh"),
    ]

    with tarfile.open(infra_archive, "w:gz") as tar:
        for src, arc in infra_candidates:
            if src.exists() and src.is_file():
                tar.add(src, arcname=arc)

    if reporter:
        reporter(85, "git", "Saving git commit snapshot")

    commit_file = backup_dir / "app_commit.txt"
    rc, out, _ = _run(["git", "rev-parse", "HEAD"], cwd=str(project_root))
    commit_file.write_text((out if rc == 0 else "unknown") + "\n", encoding="utf-8")

    (backup_dir / ".auto_backup").touch(exist_ok=True)

    if reporter:
        reporter(92, "retention", "Applying retention policy")

    deleted = _apply_retention(root)

    if reporter:
        reporter(100, "done", "Backup completed")

    return {
        "date": today,
        "status": "ok",
        "deleted": deleted,
        "backup_dir": str(backup_dir),
    }


def _perform_restore(root: Path, backup_date: str, reporter: ProgressReporter = None):
    if not DATE_DIR_RE.match(backup_date):
        raise RuntimeError("Invalid date format. Expected YYYY-MM-DD")

    backup_dir = root / backup_date
    db_dump = backup_dir / "db.sql.gz"
    if not db_dump.exists():
        raise RuntimeError(f"Database dump missing: {db_dump}")

    db_cfg = _env_db_config()
    env = os.environ.copy()
    env["PGPASSWORD"] = db_cfg["password"]
    safe_db_name = db_cfg["name"].replace("'", "''")

    if reporter:
        reporter(10, "database", "Terminating active DB connections")

    rc, _, err = _run(
        [
            "psql",
            "-h",
            db_cfg["host"],
            "-p",
            db_cfg["port"],
            "-U",
            db_cfg["user"],
            "-d",
            "postgres",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{safe_db_name}' AND pid <> pg_backend_pid();",
        ],
        env=env,
    )
    if rc != 0:
        raise RuntimeError(f"Failed to terminate active DB connections: {err}")

    if reporter:
        reporter(25, "database", "Resetting public schema")

    rc, _, err = _run(
        [
            "psql",
            "-h",
            db_cfg["host"],
            "-p",
            db_cfg["port"],
            "-U",
            db_cfg["user"],
            "-d",
            db_cfg["name"],
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;",
        ],
        env=env,
    )
    if rc != 0:
        raise RuntimeError(f"Failed to reset public schema: {err}")

    if reporter:
        reporter(45, "database", "Importing SQL dump")

    p1 = subprocess.Popen(["gunzip", "-c", str(db_dump)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p2 = subprocess.Popen(
        [
            "psql",
            "-h",
            db_cfg["host"],
            "-p",
            db_cfg["port"],
            "-U",
            db_cfg["user"],
            "-d",
            db_cfg["name"],
            "-v",
            "ON_ERROR_STOP=1",
        ],
        stdin=p1.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    if p1.stdout:
        p1.stdout.close()
    _, gz_err = p1.communicate()
    _, psql_err = p2.communicate()
    if p1.returncode != 0 or p2.returncode != 0:
        raise RuntimeError(
            f"Database restore failed: {gz_err.decode('utf-8', 'ignore').strip()} {psql_err.decode('utf-8', 'ignore').strip()}".strip()
        )

    media_archive = backup_dir / "media.tar.gz"
    media_root = Path(settings.MEDIA_ROOT)
    if media_archive.exists():
        if reporter:
            reporter(70, "media", "Restoring media archive")
        rc, _, err = _run(["tar", "-xzpf", str(media_archive), "-C", str(media_root.parent)])
        if rc != 0:
            raise RuntimeError(f"Media restore failed: {err}")

    infra_archive = backup_dir / "infra.tar.gz"
    project_root = _project_root()
    if infra_archive.exists() and project_root.exists():
        if reporter:
            reporter(85, "infra", "Restoring infra archive")
        _run(["tar", "-xzpf", str(infra_archive), "-C", str(project_root)])

    if reporter:
        reporter(100, "done", "Restore completed")

    return {"date": backup_date, "status": "ok"}


def _perform_sync(root: Path, backup_date: str, reporter: ProgressReporter = None):
    if reporter:
        reporter(15, "cloud", "Checking rclone availability")
    if shutil.which("rclone") is None:
        raise RuntimeError("rclone is not installed")

    rc, out, _ = _run(["rclone", "listremotes"])
    if rc != 0 or "offsite:" not in out.splitlines():
        raise RuntimeError("rclone remote 'offsite' is not configured")

    backup_dir = root / backup_date
    if not backup_dir.exists():
        raise RuntimeError(f"Backup not found: {backup_date}")

    if reporter:
        reporter(40, "cloud", "Syncing backup to offsite remote")

    remote = f"offsite:radreport-backups/{socket.gethostname()}/{backup_date}"
    rc, sout, serr = _run(["rclone", "sync", str(backup_dir), remote])
    if rc != 0:
        raise RuntimeError(f"Offsite sync failed: {serr or sout}")

    if reporter:
        reporter(100, "done", "Cloud sync completed")

    return {"date": backup_date, "remote": remote, "status": "ok"}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def backup_ops_status(request):
    denied = _require_admin(request)
    if denied:
        return denied

    root = _resolve_backup_root()
    backups = _list_backups(root)
    latest = backups[0] if backups else None
    today = dt.date.today().isoformat()

    log_path = Path("/var/log/radreport-backup.log")
    last_backup_age_days = None
    if latest:
        latest_date = dt.date.fromisoformat(latest["date"])
        last_backup_age_days = (dt.date.today() - latest_date).days

    jobs = _list_recent_jobs(root)
    active_jobs = [j for j in jobs if j.get("status") in {"queued", "running"}]

    return Response(
        {
            "backup_root": str(root),
            "today": today,
            "latest": latest,
            "backups": backups[:60],
            "health": {
                "has_recent_backup": (last_backup_age_days is not None and last_backup_age_days <= 1),
                "last_backup_age_days": last_backup_age_days,
            },
            "automation": {
                "cron_expected": "0 2 * * *",
                "log_file": str(log_path),
                "log_tail": _tail_file(log_path, limit=20),
            },
            "cloud": {
                "rclone_installed": shutil.which("rclone") is not None,
            },
            "jobs": {
                "active": active_jobs,
                "recent": jobs,
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def backup_ops_job_status(request, job_id: str):
    denied = _require_admin(request)
    if denied:
        return denied

    root = _resolve_backup_root()
    payload = _get_job(root, job_id)
    if payload is None:
        return Response({"detail": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(payload)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def backup_ops_backup_now(request):
    denied = _require_admin(request)
    if denied:
        return denied

    force = _as_bool(request.data.get("force", False))
    root = _resolve_backup_root()

    payload = _submit_job(
        root,
        "backup",
        request.user.username,
        {"force": force},
        lambda: (lambda reporter: _perform_backup(root, force=force, reporter=reporter)),
    )
    return Response(payload, status=status.HTTP_202_ACCEPTED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def backup_ops_restore(request):
    denied = _require_admin(request)
    if denied:
        return denied

    backup_date = str(request.data.get("date", "")).strip()
    confirm_text = str(request.data.get("confirm", "")).strip()
    if confirm_text != "RESTORE":
        return Response({"detail": "Confirmation text must be RESTORE"}, status=status.HTTP_400_BAD_REQUEST)

    root = _resolve_backup_root()

    payload = _submit_job(
        root,
        "restore",
        request.user.username,
        {"date": backup_date},
        lambda: (lambda reporter: _perform_restore(root, backup_date, reporter=reporter)),
    )
    return Response(payload, status=status.HTTP_202_ACCEPTED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def backup_ops_sync(request):
    denied = _require_admin(request)
    if denied:
        return denied

    backup_date = str(request.data.get("date", "")).strip()
    root = _resolve_backup_root()

    backups = _list_backups(root)
    if not backup_date:
        if not backups:
            return Response({"detail": "No backups available"}, status=status.HTTP_400_BAD_REQUEST)
        backup_date = backups[0]["date"]

    payload = _submit_job(
        root,
        "sync",
        request.user.username,
        {"date": backup_date},
        lambda: (lambda reporter: _perform_sync(root, backup_date, reporter=reporter)),
    )
    return Response(payload, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def backup_ops_export(request, backup_date: str):
    denied = _require_admin(request)
    if denied:
        return denied

    root = _resolve_backup_root()
    backup_dir = root / backup_date
    if not backup_dir.exists() or not backup_dir.is_dir():
        return Response({"detail": "Backup not found"}, status=status.HTTP_404_NOT_FOUND)

    artifact = str(request.query_params.get("artifact", "full")).strip().lower()
    if artifact == "db":
        target = backup_dir / "db.sql.gz"
        filename = f"{backup_date}-db.sql.gz"
    elif artifact == "media":
        target = backup_dir / "media.tar.gz"
        filename = f"{backup_date}-media.tar.gz"
    elif artifact == "infra":
        target = backup_dir / "infra.tar.gz"
        filename = f"{backup_date}-infra.tar.gz"
    elif artifact == "commit":
        target = backup_dir / "app_commit.txt"
        filename = f"{backup_date}-app_commit.txt"
    else:
        tmp = tempfile.NamedTemporaryFile(prefix=f"backup-{backup_date}-", suffix=".tar.gz", delete=False)
        tmp.close()
        with tarfile.open(tmp.name, "w:gz") as tar:
            tar.add(backup_dir, arcname=backup_dir.name)
        target = Path(tmp.name)
        filename = f"backup-{backup_date}-full.tar.gz"

    if not target.exists():
        return Response({"detail": f"Artifact missing: {artifact}"}, status=status.HTTP_404_NOT_FOUND)

    return FileResponse(open(target, "rb"), as_attachment=True, filename=filename)
