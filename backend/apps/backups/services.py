import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import tarfile
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import fcntl
import requests
from django.conf import settings
from django.utils import timezone

from apps.audit.models import AuditLog

from .models import BackupJob

DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class BackupError(RuntimeError):
    pass


def _project_root() -> Path:
    return Path(settings.BASE_DIR).resolve().parent


def backup_root() -> Path:
    root = Path(os.getenv("BACKUP_ROOT", str(_project_root() / "backups"))).resolve()
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o750)
    return root


def _lock_dir() -> Path:
    p = backup_root() / ".locks"
    p.mkdir(parents=True, exist_ok=True)
    return p


@contextmanager
def global_lock(name: str = "backup_restore.lock"):
    handle_path = _lock_dir() / name
    with handle_path.open("w", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise BackupError("Another backup/restore job is already running") from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, check: bool = True, stderr_file=None) -> subprocess.CompletedProcess:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=stderr_file if stderr_file is not None else subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        err = ""
        if stderr_file is None:
            err = (result.stderr or "").strip()
        raise BackupError(f"Command failed ({' '.join(cmd)}): {err}")
    return result


def _db_config() -> dict[str, str]:
    cfg = settings.DATABASES.get("default", {})
    return {
        "name": str(os.getenv("DB_NAME") or cfg.get("NAME") or "rims"),
        "user": str(os.getenv("DB_USER") or cfg.get("USER") or "rims"),
        "password": str(os.getenv("DB_PASSWORD") or cfg.get("PASSWORD") or ""),
        "host": str(os.getenv("DB_HOST") or cfg.get("HOST") or "db"),
        "port": str(os.getenv("DB_PORT") or cfg.get("PORT") or "5432"),
    }


def _encrypt_if_enabled(path: Path, meta: dict[str, Any], log_file) -> Path:
    key = os.getenv("BACKUP_ENCRYPTION_KEY", "")
    if not key:
        meta["encryption_enabled"] = False
        return path

    if shutil.which("openssl") is None:
        raise BackupError("BACKUP_ENCRYPTION_KEY is set but openssl is not installed")

    target = Path(f"{path}.enc")
    cmd = [
        "openssl",
        "enc",
        "-aes-256-cbc",
        "-pbkdf2",
        "-salt",
        "-pass",
        f"pass:{key}",
        "-in",
        str(path),
        "-out",
        str(target),
    ]
    _run(cmd, check=True, stderr_file=log_file)
    path.unlink(missing_ok=True)
    meta["encryption_enabled"] = True
    return target


def _decrypt_to_temp(path: Path, log_file) -> Path:
    key = os.getenv("BACKUP_ENCRYPTION_KEY", "")
    if not path.name.endswith(".enc"):
        return path
    if not key:
        raise BackupError("Encrypted artifact found but BACKUP_ENCRYPTION_KEY is not set")

    out = Path(tempfile.mkdtemp(prefix="backup-dec-")) / path.name.removesuffix(".enc")
    cmd = [
        "openssl",
        "enc",
        "-d",
        "-aes-256-cbc",
        "-pbkdf2",
        "-pass",
        f"pass:{key}",
        "-in",
        str(path),
        "-out",
        str(out),
    ]
    _run(cmd, check=True, stderr_file=log_file)
    return out


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_git_snapshot(output_dir: Path) -> tuple[str, str]:
    project = _project_root()
    commit_file = output_dir / "app_commit.txt"
    status_file = output_dir / "app_status.txt"

    commit = "unknown"
    clean = False
    untracked = 0
    if (project / ".git").exists():
        commit_res = _run(["git", "rev-parse", "HEAD"], cwd=project, check=False)
        if commit_res.returncode == 0 and commit_res.stdout:
            commit = commit_res.stdout.strip()

        status_res = _run(["git", "status", "--porcelain"], cwd=project, check=False)
        lines = [line for line in status_res.stdout.splitlines() if line.strip()]
        untracked = len([line for line in lines if line.startswith("??")])
        clean = len(lines) == 0

    commit_file.write_text(f"{commit}\n", encoding="utf-8")
    status_file.write_text(
        f"clean={str(clean).lower()}\nuntracked_count={untracked}\n",
        encoding="utf-8",
    )
    return commit, str(status_file)


def _active_caddyfile() -> list[tuple[Path, str]]:
    project = _project_root()
    candidates: list[tuple[Path, str]] = []
    system = Path("/etc/caddy/Caddyfile")
    local = project / "Caddyfile"
    if system.exists():
        candidates.append((system, "etc/caddy/Caddyfile"))
    elif local.exists():
        candidates.append((local, "Caddyfile"))
    else:
        if local.exists():
            candidates.append((local, "Caddyfile"))
        if system.exists():
            candidates.append((system, "etc/caddy/Caddyfile"))
    return candidates


def _build_infra_archive(output_dir: Path, log_file) -> Path:
    project = _project_root()
    stage = Path(tempfile.mkdtemp(prefix="backup-infra-"))
    try:
        copies = [
            (project / "docker-compose.yml", "docker-compose.yml"),
            (project / ".env.production", ".env.production"),
            (project / "backup_full.sh", "scripts/backup_full.sh"),
            (project / "restore_full.sh", "scripts/restore_full.sh"),
            (project / "install_cron.sh", "scripts/install_cron.sh"),
            (project / "verify_backup.sh", "scripts/verify_backup.sh"),
            (project / "BACKUP_README.md", "BACKUP_README.md"),
        ]
        copies.extend(_active_caddyfile())

        for src, rel in copies:
            if not src.exists() or not src.is_file():
                continue
            target = stage / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)

        out = output_dir / "infra.tar.gz"
        with tarfile.open(out, "w:gz") as tar:
            tar.add(stage, arcname=".")
        return out
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def _run_db_dump(output_dir: Path, log_file) -> Path:
    db = _db_config()
    env = os.environ.copy()
    env["PGPASSWORD"] = db["password"]

    target = output_dir / "db.sql.gz"
    pg_cmd = [
        "pg_dump",
        "-h",
        db["host"],
        "-p",
        db["port"],
        "-U",
        db["user"],
        "-d",
        db["name"],
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-privileges",
    ]

    with target.open("wb") as out_f:
        p1 = subprocess.Popen(pg_cmd, stdout=subprocess.PIPE, stderr=log_file, env=env)
        p2 = subprocess.Popen(["gzip", "-c"], stdin=p1.stdout, stdout=out_f, stderr=log_file)
        if p1.stdout:
            p1.stdout.close()
        p1.wait()
        p2.wait()
    if p1.returncode != 0 or p2.returncode != 0:
        raise BackupError("pg_dump pipeline failed; check backup.log")
    return target


def _build_media_archive(output_dir: Path) -> Path | None:
    media_dir = Path(settings.MEDIA_ROOT)
    if not media_dir.exists() or not media_dir.is_dir():
        return None
    target = output_dir / "media.tar.gz"
    with tarfile.open(target, "w:gz") as tar:
        tar.add(media_dir, arcname=media_dir.relative_to(media_dir.parent))
    return target


def _checksums(output_dir: Path) -> Path:
    lines: list[str] = []
    for name in ("db.sql.gz", "db.sql.gz.enc", "media.tar.gz", "media.tar.gz.enc", "infra.tar.gz", "infra.tar.gz.enc", "app_commit.txt", "app_status.txt", "meta.json"):
        p = output_dir / name
        if p.exists():
            lines.append(f"{_sha256(p)}  {name}")
    cs = output_dir / "checksums.sha256"
    cs.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return cs


def _tail(path: Path, limit: int = 80) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return lines[-limit:]


def _job_update(job: BackupJob, **kwargs):
    for key, val in kwargs.items():
        setattr(job, key, val)
    job.save(update_fields=list(kwargs.keys()))


def _audit(actor, action: str, entity_id: str, meta: dict[str, Any] | None = None):
    AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        entity_type="backup",
        entity_id=entity_id,
        meta=meta or {},
    )


def run_backup_job(*, job: BackupJob, actor=None, force: bool = False) -> BackupJob:
    root = backup_root()
    day = timezone.localdate().isoformat()
    output_dir = root / day

    if output_dir.exists() and not force:
        marker = output_dir / "meta.json"
        if marker.exists():
            raise BackupError(f"Backup for {day} already exists. Use force to rebuild.")

    job.backup_path = str(output_dir)
    job.status = BackupJob.STATUS_RUNNING
    if not job.started_at:
        job.started_at = timezone.now()
    job.save(update_fields=["backup_path", "status", "started_at"])
    _audit(actor, "backup.create", str(job.id), {"trigger": job.trigger})

    errors: list[str] = []
    meta: dict[str, Any] = {
        "created_at": timezone.now().isoformat(),
        "created_by": job.created_by,
        "trigger": job.trigger,
        "git_commit": "unknown",
        "db_dump_size_bytes": 0,
        "media_size_bytes": 0,
        "infra_size_bytes": 0,
        "success": {"db": False, "media": False, "infra": False},
        "errors": errors,
        "encryption_enabled": False,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "backup.log"

    started = timezone.now()
    try:
        with global_lock("backup_restore.lock"):
            with log_path.open("a", encoding="utf-8") as log_file:
                log_file.write(f"[{timezone.now().isoformat()}] backup started\n")
                db_file = _run_db_dump(output_dir, log_file)
                db_file = _encrypt_if_enabled(db_file, meta, log_file)
                meta["success"]["db"] = True
                meta["db_dump_size_bytes"] = db_file.stat().st_size

                media_file = _build_media_archive(output_dir)
                if media_file is not None:
                    media_file = _encrypt_if_enabled(media_file, meta, log_file)
                    meta["success"]["media"] = True
                    meta["media_size_bytes"] = media_file.stat().st_size
                else:
                    log_file.write("media directory missing; skipped\n")

                infra_file = _build_infra_archive(output_dir, log_file)
                infra_file = _encrypt_if_enabled(infra_file, meta, log_file)
                meta["success"]["infra"] = True
                meta["infra_size_bytes"] = infra_file.stat().st_size

                commit, _ = _write_git_snapshot(output_dir)
                meta["git_commit"] = commit

                meta_path = output_dir / "meta.json"
                meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                _checksums(output_dir)

                _job_update(
                    job,
                    status=BackupJob.STATUS_SUCCESS,
                    db_path=str(db_file),
                    media_path=str(media_file) if media_file is not None else "",
                    infra_path=str(infra_file),
                    logs_path=str(log_path),
                    meta_path=str(meta_path),
                )

            if job.trigger == "cron":
                deleted = apply_retention_policy()
                if deleted:
                    job.extra = {**job.extra, "retention_deleted": deleted}
                    job.save(update_fields=["extra"])
    except Exception as exc:
        errors.append(str(exc))
        meta_path = output_dir / "meta.json"
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        _job_update(
            job,
            status=BackupJob.STATUS_FAILED,
            error_message=str(exc),
            logs_path=str(log_path),
            meta_path=str(meta_path),
        )
        _audit(actor, "backup.failed", str(job.id), {"error": str(exc)})
        raise
    finally:
        finished = timezone.now()
        job.finished_at = finished
        job.duration_sec = max(0, int((finished - started).total_seconds()))
        job.save(update_fields=["finished_at", "duration_sec"])

    _audit(actor, "backup.success", str(job.id), {"path": str(output_dir)})
    return job


def create_backup_job(*, actor=None, created_by: str, trigger: str, deletable: bool = False, force: bool = False) -> BackupJob:
    job = BackupJob.objects.create(
        created_by=created_by,
        trigger=trigger,
        operation=BackupJob.OP_BACKUP,
        status=BackupJob.STATUS_RUNNING,
        started_at=timezone.now(),
        is_deletable=deletable,
    )
    return run_backup_job(job=job, actor=actor, force=force)


def apply_retention_policy() -> list[str]:
    jobs = list(
        BackupJob.objects.filter(operation=BackupJob.OP_BACKUP, status=BackupJob.STATUS_SUCCESS, trigger="cron")
        .order_by("-created_at")
    )
    if len(jobs) <= 7:
        return []

    to_delete = jobs[7:]
    deleted: list[str] = []
    for job in to_delete:
        if not job.backup_path:
            continue
        path = Path(job.backup_path)
        if path.exists() and path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            deleted.append(path.name)
    return deleted


def list_backups() -> list[dict[str, Any]]:
    root = backup_root()
    fs_entries: dict[str, dict[str, Any]] = {}
    for entry in sorted(root.iterdir(), key=lambda p: p.name, reverse=True):
        if not entry.is_dir() or not DATE_DIR_RE.match(entry.name):
            continue
        meta_path = entry / "meta.json"
        meta: dict[str, Any] = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                meta = {}

        db_file = _artifact(entry, "db.sql.gz") or _artifact(entry, "db.sql.gz.enc")
        media_file = _artifact(entry, "media.tar.gz") or _artifact(entry, "media.tar.gz.enc")
        infra_file = _artifact(entry, "infra.tar.gz") or _artifact(entry, "infra.tar.gz.enc")
        fs_entries[entry.name] = {
            "id": f"fs-{entry.name}",
            "date": entry.name,
            "backup_path": str(entry),
            "db_path": str(db_file) if db_file else "",
            "media_path": str(media_file) if media_file else "",
            "infra_path": str(infra_file) if infra_file else "",
            "meta": meta,
            "status": "SUCCESS" if meta.get("success", {}).get("db") else "UNKNOWN",
            "trigger": meta.get("trigger", "unknown"),
            "created_by": meta.get("created_by", "unknown"),
            "uploaded": False,
            "provider": "",
            "size": {
                "db": db_file.stat().st_size if db_file and db_file.exists() else 0,
                "media": media_file.stat().st_size if media_file and media_file.exists() else 0,
                "infra": infra_file.stat().st_size if infra_file and infra_file.exists() else 0,
            },
            "logs_tail": _tail(entry / "backup.log", 40),
            "can_delete": False,
            "job_id": None,
        }

    for job in BackupJob.objects.filter(operation=BackupJob.OP_BACKUP).order_by("-created_at"):
        date_key = ""
        if job.backup_path:
            date_key = Path(job.backup_path).name
        payload = {
            "id": str(job.id),
            "date": date_key,
            "backup_path": job.backup_path,
            "db_path": job.db_path,
            "media_path": job.media_path,
            "infra_path": job.infra_path,
            "meta": load_meta(job.meta_path),
            "status": job.status,
            "trigger": job.trigger,
            "created_by": job.created_by,
            "uploaded": job.uploaded,
            "provider": job.upload_remote,
            "size": {
                "db": _size(Path(job.db_path)) if job.db_path else 0,
                "media": _size(Path(job.media_path)) if job.media_path else 0,
                "infra": _size(Path(job.infra_path)) if job.infra_path else 0,
            },
            "logs_tail": _tail(Path(job.logs_path), 40) if job.logs_path else [],
            "can_delete": can_delete_job(job),
            "job_id": str(job.id),
        }
        if date_key and date_key in fs_entries:
            fs_entries[date_key] = {**fs_entries[date_key], **payload}
        else:
            fs_entries[str(job.id)] = payload

    return list(fs_entries.values())


def load_meta(meta_path: str) -> dict[str, Any]:
    if not meta_path:
        return {}
    p = Path(meta_path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _artifact(root: Path, name: str) -> Path | None:
    p = root / name
    return p if p.exists() and p.is_file() else None


def _size(path: Path) -> int:
    try:
        return path.stat().st_size
    except Exception:
        return 0


def can_delete_job(job: BackupJob) -> bool:
    if job.status != BackupJob.STATUS_SUCCESS:
        return False
    if job.trigger == "cron":
        return False
    return bool(job.is_deletable)


def resolve_backup_ref(backup_id: str) -> tuple[BackupJob | None, Path]:
    try:
        job = BackupJob.objects.filter(id=backup_id).first()
    except Exception:
        job = None
    if job and job.backup_path:
        return job, Path(job.backup_path)

    if backup_id.startswith("fs-"):
        backup_id = backup_id[3:]

    root = backup_root()
    candidate = root / backup_id
    if candidate.exists() and candidate.is_dir():
        return None, candidate

    for entry in root.iterdir():
        if entry.is_dir() and entry.name == backup_id:
            return None, entry
    raise BackupError("Backup not found")


def stream_backup_archive(backup_dir: Path) -> io.BufferedReader:
    temp = tempfile.NamedTemporaryFile(prefix=f"backup-{backup_dir.name}-", suffix=".tar.gz", delete=False)
    temp.close()
    with tarfile.open(temp.name, "w:gz") as tar:
        tar.add(backup_dir, arcname=backup_dir.name)
    return open(temp.name, "rb")


def import_backup_archive(*, archive_path: Path, actor=None, created_by: str) -> BackupJob:
    root = backup_root()
    temp_dir = Path(tempfile.mkdtemp(prefix="backup-import-"))

    job = BackupJob.objects.create(
        created_by=created_by,
        trigger="api",
        operation=BackupJob.OP_IMPORT,
        status=BackupJob.STATUS_RUNNING,
        started_at=timezone.now(),
    )
    _audit(actor, "backup.import.start", str(job.id), {})

    try:
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(temp_dir)
        else:
            with tarfile.open(archive_path, "r:*") as tar:
                tar.extractall(temp_dir)

        root_candidates = [p for p in temp_dir.iterdir() if p.is_dir()]
        if len(root_candidates) == 1:
            extracted = root_candidates[0]
        else:
            extracted = temp_dir

        meta_file = extracted / "meta.json"
        if not meta_file.exists():
            raise BackupError("Imported backup missing meta.json")

        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        for required in ("created_at", "created_by", "trigger", "success"):
            if required not in meta:
                raise BackupError(f"meta.json missing required key: {required}")

        checksums = extracted / "checksums.sha256"
        if checksums.exists():
            for line in checksums.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                digest, file_name = line.split("  ", 1)
                target = extracted / file_name
                if target.exists() and _sha256(target) != digest:
                    raise BackupError(f"Checksum mismatch for {file_name}")

        date_folder = dt.datetime.fromisoformat(meta["created_at"]).date().isoformat()
        destination = root / date_folder
        if destination.exists():
            destination = root / f"{date_folder}-import-{job.id.hex[:8]}"

        shutil.copytree(extracted, destination)

        job.status = BackupJob.STATUS_SUCCESS
        job.backup_path = str(destination)
        job.meta_path = str(destination / "meta.json")
        job.logs_path = str(destination / "backup.log")
        job.finished_at = timezone.now()
        job.duration_sec = int((job.finished_at - job.started_at).total_seconds()) if job.started_at else 0
        job.save(update_fields=["status", "backup_path", "meta_path", "logs_path", "finished_at", "duration_sec"])
        _audit(actor, "backup.import.success", str(job.id), {"path": str(destination)})
        return job
    except Exception as exc:
        job.status = BackupJob.STATUS_FAILED
        job.error_message = str(exc)
        job.finished_at = timezone.now()
        job.duration_sec = int((job.finished_at - job.started_at).total_seconds()) if job.started_at else 0
        job.save(update_fields=["status", "error_message", "finished_at", "duration_sec"])
        _audit(actor, "backup.import.failed", str(job.id), {"error": str(exc)})
        raise
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_upload_job(*, job: BackupJob, backup_id: str, actor=None) -> BackupJob:
    if shutil.which("rclone") is None:
        raise BackupError("rclone is not installed")

    remote_name = os.getenv("BACKUP_RCLONE_REMOTE", "offsite")
    remote_path = os.getenv("BACKUP_RCLONE_PATH", "radreport-backups")

    _, backup_dir = resolve_backup_ref(backup_id)
    job.status = BackupJob.STATUS_RUNNING
    job.backup_path = str(backup_dir)
    if not job.started_at:
        job.started_at = timezone.now()
    job.save(update_fields=["status", "backup_path", "started_at"])
    _audit(actor, "backup.upload.start", str(job.id), {"backup": backup_id})

    log_path = backup_dir / f"upload-{job.id}.log"
    remote = f"{remote_name}:{remote_path.rstrip('/')}/{socket.gethostname()}/{backup_dir.name}"

    try:
        with log_path.open("a", encoding="utf-8") as logf:
            check = _run(["rclone", "listremotes"], check=False)
            if check.returncode != 0 or f"{remote_name}:" not in check.stdout.splitlines():
                raise BackupError(f"rclone remote '{remote_name}:' is not configured")

            sync = _run(["rclone", "sync", str(backup_dir), remote], check=False)
            logf.write(sync.stdout or "")
            if sync.returncode != 0:
                raise BackupError("rclone sync failed; see upload log")

        job.status = BackupJob.STATUS_SUCCESS
        job.uploaded = True
        job.upload_remote = remote
        job.upload_log_path = str(log_path)
        job.finished_at = timezone.now()
        job.duration_sec = int((job.finished_at - job.started_at).total_seconds()) if job.started_at else 0
        job.save(update_fields=["status", "uploaded", "upload_remote", "upload_log_path", "finished_at", "duration_sec"])

        backup_job = BackupJob.objects.filter(operation=BackupJob.OP_BACKUP, backup_path=str(backup_dir)).order_by("-created_at").first()
        if backup_job:
            backup_job.uploaded = True
            backup_job.upload_remote = remote_name
            backup_job.upload_log_path = str(log_path)
            backup_job.save(update_fields=["uploaded", "upload_remote", "upload_log_path"])

        _audit(actor, "backup.upload.success", str(job.id), {"remote": remote})
        return job
    except Exception as exc:
        job.status = BackupJob.STATUS_FAILED
        job.error_message = str(exc)
        job.upload_log_path = str(log_path)
        job.finished_at = timezone.now()
        job.duration_sec = int((job.finished_at - job.started_at).total_seconds()) if job.started_at else 0
        job.save(update_fields=["status", "error_message", "upload_log_path", "finished_at", "duration_sec"])
        _audit(actor, "backup.upload.failed", str(job.id), {"error": str(exc)})
        raise


def upload_backup_to_cloud(*, backup_id: str, actor=None, created_by: str) -> BackupJob:
    job = BackupJob.objects.create(
        created_by=created_by,
        trigger="api",
        operation=BackupJob.OP_UPLOAD,
        status=BackupJob.STATUS_RUNNING,
        started_at=timezone.now(),
    )
    return run_upload_job(job=job, backup_id=backup_id, actor=actor)


def test_cloud_connection(*, actor=None, created_by: str) -> BackupJob:
    remote_name = os.getenv("BACKUP_RCLONE_REMOTE", "offsite")
    remote_path = os.getenv("BACKUP_RCLONE_PATH", "radreport-backups")
    job = BackupJob.objects.create(
        created_by=created_by,
        trigger="api",
        operation=BackupJob.OP_TEST_CLOUD,
        status=BackupJob.STATUS_RUNNING,
        started_at=timezone.now(),
    )

    try:
        if shutil.which("rclone") is None:
            raise BackupError("rclone is not installed")
        out = _run(["rclone", "lsd", f"{remote_name}:{remote_path}"], check=False)
        if out.returncode != 0:
            raise BackupError("rclone connection test failed")

        job.status = BackupJob.STATUS_SUCCESS
        job.extra = {"remote": remote_name, "path": remote_path}
        job.finished_at = timezone.now()
        job.duration_sec = int((job.finished_at - job.started_at).total_seconds()) if job.started_at else 0
        job.save(update_fields=["status", "extra", "finished_at", "duration_sec"])
        _audit(actor, "backup.cloud_test.success", str(job.id), job.extra)
        return job
    except Exception as exc:
        job.status = BackupJob.STATUS_FAILED
        job.error_message = str(exc)
        job.finished_at = timezone.now()
        job.duration_sec = int((job.finished_at - job.started_at).total_seconds()) if job.started_at else 0
        job.save(update_fields=["status", "error_message", "finished_at", "duration_sec"])
        _audit(actor, "backup.cloud_test.failed", str(job.id), {"error": str(exc)})
        raise


def delete_backup(*, backup_id: str, actor=None, created_by: str):
    job, backup_dir = resolve_backup_ref(backup_id)
    if job and not can_delete_job(job):
        raise BackupError("Backup is not deletable by policy")
    if not backup_dir.exists():
        raise BackupError("Backup path not found")

    delete_job = BackupJob.objects.create(
        created_by=created_by,
        trigger="api",
        operation=BackupJob.OP_DELETE,
        status=BackupJob.STATUS_RUNNING,
        started_at=timezone.now(),
        backup_path=str(backup_dir),
    )

    try:
        shutil.rmtree(backup_dir)
        delete_job.status = BackupJob.STATUS_SUCCESS
        delete_job.finished_at = timezone.now()
        delete_job.duration_sec = int((delete_job.finished_at - delete_job.started_at).total_seconds()) if delete_job.started_at else 0
        delete_job.save(update_fields=["status", "finished_at", "duration_sec"])
        _audit(actor, "backup.delete.success", str(delete_job.id), {"path": str(backup_dir)})
    except Exception as exc:
        delete_job.status = BackupJob.STATUS_FAILED
        delete_job.error_message = str(exc)
        delete_job.finished_at = timezone.now()
        delete_job.duration_sec = int((delete_job.finished_at - delete_job.started_at).total_seconds()) if delete_job.started_at else 0
        delete_job.save(update_fields=["status", "error_message", "finished_at", "duration_sec"])
        _audit(actor, "backup.delete.failed", str(delete_job.id), {"error": str(exc)})
        raise


def run_restore_job(
    *,
    job: BackupJob,
    backup_id: str,
    actor=None,
    confirm_phrase: str,
    dry_run: bool = False,
    yes: bool = False,
    allow_system_caddy_overwrite: bool = False,
) -> BackupJob:
    if confirm_phrase != "RESTORE NOW":
        raise BackupError("Confirmation phrase must be RESTORE NOW")

    _, backup_dir = resolve_backup_ref(backup_id)
    db_dump = _artifact(backup_dir, "db.sql.gz") or _artifact(backup_dir, "db.sql.gz.enc")
    if db_dump is None:
        raise BackupError("Backup is missing db.sql.gz/db.sql.gz.enc")

    job.status = BackupJob.STATUS_RUNNING
    job.backup_path = str(backup_dir)
    if not job.started_at:
        job.started_at = timezone.now()
    job.save(update_fields=["status", "backup_path", "started_at"])
    _audit(actor, "backup.restore.start", str(job.id), {"backup": backup_id, "dry_run": dry_run})

    root = backup_root()
    freeze_file = root / ".restore_in_progress"
    log_path = backup_dir / f"restore-{job.id}.log"
    started = timezone.now()

    try:
        with global_lock("backup_restore.lock"):
            freeze_file.write_text(f"started_at={timezone.now().isoformat()}\n", encoding="utf-8")
            with log_path.open("a", encoding="utf-8") as logf:
                logf.write(f"[{timezone.now().isoformat()}] restore started\n")
                stage = Path(tempfile.mkdtemp(prefix="restore-infra-"))
                try:
                    infra = _artifact(backup_dir, "infra.tar.gz") or _artifact(backup_dir, "infra.tar.gz.enc")
                    if infra and not dry_run:
                        dec = _decrypt_to_temp(infra, logf)
                        with tarfile.open(dec, "r:gz") as tar:
                            tar.extractall(stage)

                        project = _project_root()
                        for rel in ("docker-compose.yml", ".env.production", "Caddyfile"):
                            src = stage / rel
                            if src.exists():
                                target = project / rel
                                if target.exists():
                                    diff = _run(["diff", "-u", str(target), str(src)], check=False)
                                    if diff.stdout:
                                        logf.write(diff.stdout)
                                shutil.copy2(src, target)

                        sys_caddy = stage / "etc/caddy/Caddyfile"
                        if sys_caddy.exists() and allow_system_caddy_overwrite:
                            shutil.copy2(sys_caddy, Path("/etc/caddy/Caddyfile"))

                    media = _artifact(backup_dir, "media.tar.gz") or _artifact(backup_dir, "media.tar.gz.enc")
                    if media and not dry_run:
                        dec = _decrypt_to_temp(media, logf)
                        with tarfile.open(dec, "r:gz") as tar:
                            tar.extractall(_project_root())

                    if not dry_run:
                        db = _db_config()
                        env = os.environ.copy()
                        env["PGPASSWORD"] = db["password"]
                        safe_db = db["name"].replace("'", "''")

                        _run(
                            [
                                "psql",
                                "-h",
                                db["host"],
                                "-p",
                                db["port"],
                                "-U",
                                db["user"],
                                "-d",
                                "postgres",
                                "-v",
                                "ON_ERROR_STOP=1",
                                "-c",
                                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{safe_db}' AND pid <> pg_backend_pid();",
                            ],
                            env=env,
                            stderr_file=logf,
                        )
                        _run(
                            [
                                "psql",
                                "-h",
                                db["host"],
                                "-p",
                                db["port"],
                                "-U",
                                db["user"],
                                "-d",
                                db["name"],
                                "-v",
                                "ON_ERROR_STOP=1",
                                "-c",
                                "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;",
                            ],
                            env=env,
                            stderr_file=logf,
                        )

                        dec_db = _decrypt_to_temp(db_dump, logf)
                        p1 = subprocess.Popen(["gunzip", "-c", str(dec_db)], stdout=subprocess.PIPE, stderr=logf)
                        p2 = subprocess.Popen(
                            [
                                "psql",
                                "-h",
                                db["host"],
                                "-p",
                                db["port"],
                                "-U",
                                db["user"],
                                "-d",
                                db["name"],
                                "-v",
                                "ON_ERROR_STOP=1",
                            ],
                            stdin=p1.stdout,
                            stdout=logf,
                            stderr=logf,
                            env=env,
                        )
                        if p1.stdout:
                            p1.stdout.close()
                        p1.wait()
                        p2.wait()
                        if p1.returncode != 0 or p2.returncode != 0:
                            raise BackupError("Database restore failed; check restore log")

                    smoke = smoke_checks()
                    logf.write(json.dumps(smoke, indent=2) + "\n")
                finally:
                    shutil.rmtree(stage, ignore_errors=True)

        job.status = BackupJob.STATUS_SUCCESS
        job.logs_path = str(log_path)
        job.finished_at = timezone.now()
        job.duration_sec = int((job.finished_at - started).total_seconds())
        job.save(update_fields=["status", "logs_path", "finished_at", "duration_sec"])
        _audit(actor, "backup.restore.success", str(job.id), {"backup": backup_id, "dry_run": dry_run, "yes": yes})
        return job
    except Exception as exc:
        job.status = BackupJob.STATUS_FAILED
        job.error_message = str(exc)
        job.logs_path = str(log_path)
        job.finished_at = timezone.now()
        job.duration_sec = int((job.finished_at - started).total_seconds())
        job.save(update_fields=["status", "error_message", "logs_path", "finished_at", "duration_sec"])
        _audit(actor, "backup.restore.failed", str(job.id), {"error": str(exc)})
        raise
    finally:
        freeze_file.unlink(missing_ok=True)


def restore_backup(
    *,
    backup_id: str,
    created_by: str,
    actor=None,
    confirm_phrase: str,
    dry_run: bool = False,
    yes: bool = False,
    allow_system_caddy_overwrite: bool = False,
) -> BackupJob:
    job = BackupJob.objects.create(
        created_by=created_by,
        trigger="api",
        operation=BackupJob.OP_RESTORE,
        status=BackupJob.STATUS_RUNNING,
        started_at=timezone.now(),
    )
    return run_restore_job(
        job=job,
        backup_id=backup_id,
        actor=actor,
        confirm_phrase=confirm_phrase,
        dry_run=dry_run,
        yes=yes,
        allow_system_caddy_overwrite=allow_system_caddy_overwrite,
    )


def smoke_checks() -> dict[str, Any]:
    checks: dict[str, Any] = {"db": False, "health": False, "files": {}}
    db = _db_config()
    env = os.environ.copy()
    env["PGPASSWORD"] = db["password"]
    probe = _run(
        ["psql", "-h", db["host"], "-p", db["port"], "-U", db["user"], "-d", db["name"], "-c", "SELECT 1"],
        env=env,
        check=False,
    )
    checks["db"] = probe.returncode == 0

    health_url = os.getenv("BACKUP_HEALTHCHECK_URL", "http://127.0.0.1:8015/api/health/")
    try:
        res = requests.get(health_url, timeout=5)
        checks["health"] = res.ok
        checks["health_status"] = res.status_code
    except Exception:
        checks["health"] = False

    project = _project_root()
    for rel in ("docker-compose.yml", ".env.production", "backend/media"):
        checks["files"][rel] = (project / rel).exists()
    return checks
