import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import BackupJob
from .permissions import IsBackupManager, IsBackupRestoreSuperuser
from .serializers import CloudSettingsSerializer, CreateBackupSerializer, RestoreRequestSerializer
from .services import (
    BackupError,
    backup_root,
    can_delete_job,
    import_backup_archive,
    list_backups,
    resolve_backup_ref,
    run_backup_job,
    run_restore_job,
    run_upload_job,
    stream_backup_archive,
    test_cloud_connection,
)

EXECUTOR = ThreadPoolExecutor(max_workers=2)


def _is_manager(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    groups = set(g.lower() for g in user.groups.values_list("name", flat=True))
    return bool(groups.intersection({"manager", "admin"}))


def _job_payload(job: BackupJob) -> dict:
    return {
        "id": str(job.id),
        "created_at": job.created_at,
        "created_by": job.created_by,
        "trigger": job.trigger,
        "status": job.status,
        "operation": job.operation,
        "backup_path": job.backup_path,
        "db_path": job.db_path,
        "media_path": job.media_path,
        "infra_path": job.infra_path,
        "logs_path": job.logs_path,
        "meta_path": job.meta_path,
        "error_message": job.error_message,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "duration_sec": job.duration_sec,
        "is_deletable": job.is_deletable,
        "uploaded": job.uploaded,
        "upload_remote": job.upload_remote,
        "upload_log_path": job.upload_log_path,
        "extra": job.extra,
    }


def _start_background(fn, *args, **kwargs):
    def _runner():
        try:
            fn(*args, **kwargs)
        except Exception:
            # job state is updated in service layer
            return

    EXECUTOR.submit(_runner)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def backups_collection(request):
    if not _is_manager(request.user):
        return Response({"detail": "Backup manager access required"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        payload = {
            "items": list_backups(),
            "running_jobs": [
                _job_payload(job)
                for job in BackupJob.objects.filter(status=BackupJob.STATUS_RUNNING).order_by("-created_at")[:20]
            ],
            "cloud": {
                "remote_name": os.getenv("BACKUP_RCLONE_REMOTE", "offsite"),
                "remote_path": os.getenv("BACKUP_RCLONE_PATH", "radreport-backups"),
                "connected": bool(shutil.which("rclone")),
            },
            "restore_in_progress": (backup_root() / ".restore_in_progress").exists(),
            "police_mode": os.getenv("BACKUP_POLICE_MODE", "0").lower() in {"1", "true", "yes"},
        }
        return Response(payload)

    serializer = CreateBackupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    force = serializer.validated_data["force"]
    deletable = serializer.validated_data["deletable"]

    day = Path(backup_root() / Path(os.getenv("BACKUP_DATE_OVERRIDE", "")).name).name
    if not day:
        import datetime as dt

        day = dt.date.today().isoformat()

    backup_dir = backup_root() / day
    job = BackupJob.objects.create(
        created_by=request.user.username,
        trigger="manual",
        operation=BackupJob.OP_BACKUP,
        status=BackupJob.STATUS_RUNNING,
        backup_path=str(backup_dir),
        is_deletable=deletable,
    )
    _start_background(run_backup_job, job=job, actor=request.user, force=force)
    return Response(_job_payload(job), status=status.HTTP_202_ACCEPTED)


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def backup_detail(request, backup_id: str):
    if not _is_manager(request.user):
        return Response({"detail": "Backup manager access required"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        job = BackupJob.objects.filter(id=backup_id).first()
        if job:
            _, backup_dir = resolve_backup_ref(backup_id)
            payload = _job_payload(job)
            payload["meta"] = _load_json(Path(job.meta_path)) if job.meta_path else _load_json(backup_dir / "meta.json")
            payload["logs_tail"] = _tail(Path(job.logs_path)) if job.logs_path else _tail(backup_dir / "backup.log")
            payload["checksums"] = _checksums_map(backup_dir / "checksums.sha256")
            payload["can_delete"] = can_delete_job(job)
            return Response(payload)

        try:
            _, backup_dir = resolve_backup_ref(backup_id)
        except BackupError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "id": backup_id,
                "status": "SUCCESS",
                "backup_path": str(backup_dir),
                "meta": _load_json(backup_dir / "meta.json"),
                "logs_tail": _tail(backup_dir / "backup.log"),
                "checksums": _checksums_map(backup_dir / "checksums.sha256"),
                "can_delete": False,
            }
        )

    job = BackupJob.objects.filter(id=backup_id).first()
    if not job:
        return Response({"detail": "Delete allowed only for tracked backup jobs"}, status=status.HTTP_400_BAD_REQUEST)
    if not can_delete_job(job):
        return Response({"detail": "Backup is not deletable by policy"}, status=status.HTTP_400_BAD_REQUEST)

    backup_dir = Path(job.backup_path)
    if backup_dir.exists():
        import shutil

        shutil.rmtree(backup_dir, ignore_errors=True)
    job.operation = BackupJob.OP_DELETE
    job.status = BackupJob.STATUS_SUCCESS
    job.finished_at = job.finished_at or job.created_at
    job.save(update_fields=["operation", "status", "finished_at"])
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def backup_export(request, backup_id: str):
    if not _is_manager(request.user):
        return Response({"detail": "Backup manager access required"}, status=status.HTTP_403_FORBIDDEN)
    try:
        _, backup_dir = resolve_backup_ref(backup_id)
    except BackupError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

    artifact = str(request.query_params.get("artifact", "full")).strip().lower()
    if artifact == "db":
        target = _artifact_file(backup_dir, "db.sql.gz")
        if not target:
            target = _artifact_file(backup_dir, "db.sql.gz.enc")
        if not target:
            return Response({"detail": "Database artifact not found"}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(target, "rb"), as_attachment=True, filename=target.name)
    if artifact == "media":
        target = _artifact_file(backup_dir, "media.tar.gz")
        if not target:
            target = _artifact_file(backup_dir, "media.tar.gz.enc")
        if not target:
            return Response({"detail": "Media artifact not found"}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(target, "rb"), as_attachment=True, filename=target.name)
    if artifact == "infra":
        target = _artifact_file(backup_dir, "infra.tar.gz")
        if not target:
            target = _artifact_file(backup_dir, "infra.tar.gz.enc")
        if not target:
            return Response({"detail": "Infra artifact not found"}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(target, "rb"), as_attachment=True, filename=target.name)
    if artifact == "meta":
        target = _artifact_file(backup_dir, "meta.json")
        if not target:
            return Response({"detail": "meta.json not found"}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(target, "rb"), as_attachment=True, filename="meta.json")
    if artifact == "checksums":
        target = _artifact_file(backup_dir, "checksums.sha256")
        if not target:
            return Response({"detail": "checksums.sha256 not found"}, status=status.HTTP_404_NOT_FOUND)
        return FileResponse(open(target, "rb"), as_attachment=True, filename="checksums.sha256")

    file_obj = stream_backup_archive(backup_dir)
    return FileResponse(file_obj, as_attachment=True, filename=f"backup-{backup_dir.name}.tar.gz")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def backup_upload(request, backup_id: str):
    if not _is_manager(request.user):
        return Response({"detail": "Backup manager access required"}, status=status.HTTP_403_FORBIDDEN)

    job = BackupJob.objects.create(
        created_by=request.user.username,
        trigger="api",
        operation=BackupJob.OP_UPLOAD,
        status=BackupJob.STATUS_RUNNING,
    )
    _start_background(run_upload_job, job=job, backup_id=backup_id, actor=request.user)
    return Response(_job_payload(job), status=status.HTTP_202_ACCEPTED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def backup_import(request):
    if not _is_manager(request.user):
        return Response({"detail": "Backup manager access required"}, status=status.HTTP_403_FORBIDDEN)

    upload = request.FILES.get("file")
    if upload is None:
        return Response({"detail": "Missing upload file"}, status=status.HTTP_400_BAD_REQUEST)

    suffix = Path(upload.name).suffix.lower()
    if suffix not in {".zip", ".gz", ".tgz", ".tar"} and not upload.name.endswith(".tar.gz"):
        return Response({"detail": "Supported formats: .zip .tar .tar.gz .tgz"}, status=status.HTTP_400_BAD_REQUEST)

    with tempfile.NamedTemporaryFile(prefix="backup-import-", suffix="-upload", delete=False) as temp_file:
        for chunk in upload.chunks():
            temp_file.write(chunk)
        temp_path = Path(temp_file.name)

    try:
        job = import_backup_archive(archive_path=temp_path, actor=request.user, created_by=request.user.username)
    except Exception as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    finally:
        temp_path.unlink(missing_ok=True)

    return Response(_job_payload(job), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def backup_restore(request, backup_id: str):
    if not IsBackupRestoreSuperuser().has_permission(request, None):
        return Response({"detail": "Superuser access required for restore"}, status=status.HTTP_403_FORBIDDEN)

    serializer = RestoreRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    job = BackupJob.objects.create(
        created_by=request.user.username,
        trigger="api",
        operation=BackupJob.OP_RESTORE,
        status=BackupJob.STATUS_RUNNING,
    )
    _start_background(
        run_restore_job,
        job=job,
        backup_id=backup_id,
        actor=request.user,
        confirm_phrase=serializer.validated_data["confirm_phrase"],
        dry_run=serializer.validated_data["dry_run"],
        yes=serializer.validated_data["yes"],
        allow_system_caddy_overwrite=serializer.validated_data["allow_system_caddy_overwrite"],
    )
    return Response(_job_payload(job), status=status.HTTP_202_ACCEPTED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def backup_cloud_test(request):
    if not _is_manager(request.user):
        return Response({"detail": "Backup manager access required"}, status=status.HTTP_403_FORBIDDEN)

    serializer = CloudSettingsSerializer(data=request.data or {})
    serializer.is_valid(raise_exception=True)
    remote_name = serializer.validated_data["remote_name"]
    remote_path = serializer.validated_data["remote_path"]

    old_remote = os.getenv("BACKUP_RCLONE_REMOTE")
    old_path = os.getenv("BACKUP_RCLONE_PATH")
    os.environ["BACKUP_RCLONE_REMOTE"] = remote_name
    os.environ["BACKUP_RCLONE_PATH"] = remote_path
    try:
        job = test_cloud_connection(actor=request.user, created_by=request.user.username)
    except Exception as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    finally:
        if old_remote is None:
            os.environ.pop("BACKUP_RCLONE_REMOTE", None)
        else:
            os.environ["BACKUP_RCLONE_REMOTE"] = old_remote
        if old_path is None:
            os.environ.pop("BACKUP_RCLONE_PATH", None)
        else:
            os.environ["BACKUP_RCLONE_PATH"] = old_path

    return Response(_job_payload(job))


def _tail(path: Path, limit: int = 80) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return lines[-limit:]


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _checksums_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or "  " not in line:
            continue
        digest, name = line.split("  ", 1)
        out[name] = digest
    return out


def _artifact_file(root: Path, name: str) -> Path | None:
    p = root / name
    if p.exists() and p.is_file():
        return p
    return None
