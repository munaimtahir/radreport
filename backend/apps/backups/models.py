import uuid

from django.db import models


class BackupJob(models.Model):
    STATUS_RUNNING = "RUNNING"
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = (
        (STATUS_RUNNING, "Running"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    )

    OP_BACKUP = "BACKUP"
    OP_RESTORE = "RESTORE"
    OP_UPLOAD = "UPLOAD"
    OP_IMPORT = "IMPORT"
    OP_DELETE = "DELETE"
    OP_TEST_CLOUD = "TEST_CLOUD"
    OP_CHOICES = (
        (OP_BACKUP, "Backup"),
        (OP_RESTORE, "Restore"),
        (OP_UPLOAD, "Upload"),
        (OP_IMPORT, "Import"),
        (OP_DELETE, "Delete"),
        (OP_TEST_CLOUD, "Test Cloud"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.CharField(max_length=150, default="system")
    trigger = models.CharField(max_length=32, default="manual", db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_RUNNING, db_index=True)

    operation = models.CharField(max_length=24, choices=OP_CHOICES, default=OP_BACKUP)
    backup_path = models.CharField(max_length=512, blank=True, default="")
    db_path = models.CharField(max_length=512, blank=True, default="")
    media_path = models.CharField(max_length=512, blank=True, default="")
    infra_path = models.CharField(max_length=512, blank=True, default="")
    logs_path = models.CharField(max_length=512, blank=True, default="")
    meta_path = models.CharField(max_length=512, blank=True, default="")
    error_message = models.TextField(blank=True, default="")

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_sec = models.PositiveIntegerField(null=True, blank=True)

    is_deletable = models.BooleanField(default=False)
    uploaded = models.BooleanField(default=False)
    upload_remote = models.CharField(max_length=255, blank=True, default="")
    upload_log_path = models.CharField(max_length=512, blank=True, default="")

    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.id} {self.operation} {self.status}"
