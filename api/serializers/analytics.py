from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from analytics.models import (
    AuditLog,
    TrainingEvent,
    Dashboard,
    Report,
    ReportExport,
    BackupRecord,
)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'AuditLog',
            value={
                'id': 1,
                'actor': 1,
                'action': 'LOGIN',
                'object_type': 'Пользователь',
                'object_id': '1',
                'message': 'Пользователь вошёл в систему',
                'metadata': {},
                'ip_address': '127.0.0.1',
                'user_agent': 'Mozilla/5.0',
                'created_at': '2026-02-05T10:00:00Z',
            },
            response_only=True,
        )
    ]
)
class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'actor',
            'action',
            'object_type',
            'object_id',
            'message',
            'metadata',
            'ip_address',
            'user_agent',
            'created_at',
        ]
        read_only_fields = ['actor', 'created_at']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'TrainingEvent',
            value={
                'id': 1,
                'user': 1,
                'event_type': 'COURSE_COMPLETED',
                'course': 1,
                'test': None,
                'task': None,
                'metadata': {},
                'created_at': '2026-02-05T10:00:00Z',
            },
            response_only=True,
        )
    ]
)
class TrainingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingEvent
        fields = [
            'id',
            'user',
            'event_type',
            'course',
            'test',
            'task',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['created_at']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Dashboard',
            value={
                'id': 1,
                'owner': 1,
                'title': 'Team Progress',
                'config': {},
                'is_shared': False,
                'created_at': '2026-02-05T10:00:00Z',
            },
            response_only=True,
        )
    ]
)
class DashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = [
            'id',
            'owner',
            'title',
            'config',
            'is_shared',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Report',
            value={
                'id': 1,
                'owner': 1,
                'title': 'Monthly Report',
                'report_type': 'PROGRESS',
                'filters': {},
                'created_at': '2026-02-05T10:00:00Z',
            },
            response_only=True,
        )
    ]
)
class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            'id',
            'owner',
            'title',
            'report_type',
            'filters',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'ReportExport',
            value={
                'id': 1,
                'report': 1,
                'export_format': 'PDF',
                'status': 'PENDING',
                'file_path': '',
                'generated_at': '2026-02-05T10:00:00Z',
            },
            response_only=True,
        )
    ]
)
class ReportExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportExport
        fields = [
            'id',
            'report',
            'export_format',
            'status',
            'file_path',
            'generated_at',
        ]
        read_only_fields = ['generated_at']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'BackupRecord',
            value={
                'id': 1,
                'created_by': 1,
                'status': 'CREATED',
                'file_path': '/backups/backup-1.zip',
                'size_bytes': 1024,
                'checksum': 'abc123',
                'created_at': '2026-02-05T10:00:00Z',
            },
            response_only=True,
        )
    ]
)
class BackupRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupRecord
        fields = [
            'id',
            'created_by',
            'created_at',
            'status',
            'file_path',
            'size_bytes',
            'checksum',
        ]
        read_only_fields = ['created_by', 'created_at']
