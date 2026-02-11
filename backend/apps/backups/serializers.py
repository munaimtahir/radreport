from rest_framework import serializers

from .models import BackupJob


class BackupJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupJob
        fields = "__all__"


class RestoreRequestSerializer(serializers.Serializer):
    confirm_phrase = serializers.CharField()
    dry_run = serializers.BooleanField(default=False)
    yes = serializers.BooleanField(default=False)
    allow_system_caddy_overwrite = serializers.BooleanField(default=False)


class CreateBackupSerializer(serializers.Serializer):
    force = serializers.BooleanField(default=False)
    deletable = serializers.BooleanField(default=True)


class CloudSettingsSerializer(serializers.Serializer):
    remote_name = serializers.CharField(default="offsite")
    remote_path = serializers.CharField(default="radreport-backups")
