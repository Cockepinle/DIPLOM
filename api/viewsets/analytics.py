import hashlib
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.http import FileResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from api.viewsets.base import BaseModelViewSet
from api.serializers import (
    AuditLogSerializer,
    TrainingEventSerializer,
    DashboardSerializer,
    ReportSerializer,
    ReportExportSerializer,
    BackupRecordSerializer,
)
from analytics.models import AuditLog, TrainingEvent, Dashboard, Report, ReportExport, BackupRecord

ROLE_ANALYST = 'ANALYST'
ROLE_ADMIN = 'ADMIN'


class AuditLogViewSet(BaseModelViewSet):
    """Audit log events."""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    schema_tags = ['Audit Logs']
    read_roles = [ROLE_ADMIN, ROLE_ANALYST]
    write_roles = [ROLE_ADMIN, ROLE_ANALYST]
    ordering_fields = ['id', 'created_at']
    filterset_fields = ['actor', 'action', 'object_type']

    def perform_create(self, serializer):
        serializer.save(actor=self.request.user)


class TrainingEventViewSet(BaseModelViewSet):
    """Training activity events."""
    queryset = TrainingEvent.objects.all()
    serializer_class = TrainingEventSerializer
    schema_tags = ['Training Events']
    read_roles = [ROLE_ADMIN, ROLE_ANALYST]
    write_roles = [ROLE_ADMIN, ROLE_ANALYST]
    ordering_fields = ['id', 'created_at']
    filterset_fields = ['user', 'event_type', 'course', 'test', 'task']

    @action(detail=False, methods=['post'])
    def sync_overdue(self, request):
        """Call DB procedure to mark overdue enrollments."""
        if connection.vendor != 'postgresql':
            return Response(
                {'detail': 'SQL procedures are available only for PostgreSQL.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with connection.cursor() as cursor:
            cursor.execute('CALL sp_mark_overdue_enrollments();')
            cursor.execute("SELECT COUNT(*) FROM courses_enrollment WHERE status = 'OVERDUE';")
            overdue_count = cursor.fetchone()[0]
        return Response({'detail': 'Процедура выполнена.', 'overdue_count': overdue_count})

    @action(detail=False, methods=['post'])
    def log_manual_event(self, request):
        """Call DB procedure to append manual training event + audit log."""
        if connection.vendor != 'postgresql':
            return Response(
                {'detail': 'SQL procedures are available only for PostgreSQL.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = request.data.get('user_id') or request.user.id
        event_type = request.data.get('event_type') or 'TASK_REVIEWED'
        course_id = request.data.get('course_id')
        message = request.data.get('message') or 'Событие добавлено через API-процедуру.'

        with connection.cursor() as cursor:
            cursor.execute(
                'CALL sp_log_manual_event(%s, %s, %s, %s);',
                [user_id, event_type, course_id, message],
            )

        return Response({'detail': 'Событие записано через процедуру БД.'})

    @action(detail=False, methods=['get'])
    def db_objects_stats(self, request):
        """Read data from SQL views and SQL functions."""
        if connection.vendor != 'postgresql':
            return Response(
                {'detail': 'SQL views/functions are available only for PostgreSQL.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT course_id, course_title, total_enrollments, completed_enrollments, overdue_enrollments, completion_rate
                FROM vw_course_progress_summary
                ORDER BY course_id
                LIMIT 10;
                """
            )
            course_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT user_id, email, assigned_courses, completed_courses, avg_test_score, total_test_attempts
                FROM vw_employee_performance_summary
                ORDER BY user_id
                LIMIT 10;
                """
            )
            employee_rows = cursor.fetchall()

            cursor.execute('SELECT fn_employee_average_score(%s);', [request.user.id])
            my_avg_score = cursor.fetchone()[0]

        return Response(
            {
                'course_progress_summary': [
                    {
                        'course_id': row[0],
                        'course_title': row[1],
                        'total_enrollments': row[2],
                        'completed_enrollments': row[3],
                        'overdue_enrollments': row[4],
                        'completion_rate': row[5],
                    }
                    for row in course_rows
                ],
                'employee_performance_summary': [
                    {
                        'user_id': row[0],
                        'email': row[1],
                        'assigned_courses': row[2],
                        'completed_courses': row[3],
                        'avg_test_score': row[4],
                        'total_test_attempts': row[5],
                    }
                    for row in employee_rows
                ],
                'my_avg_score_via_function': my_avg_score,
            }
        )


class DashboardViewSet(BaseModelViewSet):
    """Analytics dashboards."""
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    schema_tags = ['Dashboards']
    read_roles = [ROLE_ADMIN, ROLE_ANALYST]
    write_roles = [ROLE_ADMIN, ROLE_ANALYST]
    ordering_fields = ['id', 'created_at', 'updated_at']
    filterset_fields = ['owner', 'is_shared']

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superuser', False) or user.role == ROLE_ADMIN:
            return Dashboard.objects.all()
        return Dashboard.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ReportViewSet(BaseModelViewSet):
    """Analytics reports."""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    schema_tags = ['Reports']
    read_roles = [ROLE_ADMIN, ROLE_ANALYST]
    write_roles = [ROLE_ADMIN, ROLE_ANALYST]
    ordering_fields = ['id', 'created_at', 'updated_at']
    filterset_fields = ['owner', 'report_type']

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superuser', False) or user.role == ROLE_ADMIN:
            return Report.objects.all()
        return Report.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ReportExportViewSet(BaseModelViewSet):
    queryset = ReportExport.objects.all()
    serializer_class = ReportExportSerializer
    schema_tags = ['Report Exports']
    read_roles = [ROLE_ADMIN, ROLE_ANALYST]
    write_roles = [ROLE_ADMIN, ROLE_ANALYST]
    ordering_fields = ['id', 'generated_at']
    filterset_fields = ['report', 'export_format', 'status']


class BackupRecordViewSet(BaseModelViewSet):
    queryset = BackupRecord.objects.all()
    serializer_class = BackupRecordSerializer
    schema_tags = ['Backups']
    read_roles = [ROLE_ADMIN, ROLE_ANALYST]
    write_roles = [ROLE_ADMIN, ROLE_ANALYST]
    ordering_fields = ['id', 'created_at', 'status']
    filterset_fields = ['created_by', 'status']

    class RestoreKeyPermission(BasePermission):
        def has_permission(self, request, view):
            expected = getattr(settings, 'BACKUP_RESTORE_KEY', '')
            if not expected:
                return False
            key = request.headers.get('X-Restore-Key') or request.query_params.get('restore_key')
            return bool(key) and key == expected

    def _has_restore_key(self):
        expected = getattr(settings, 'BACKUP_RESTORE_KEY', '')
        if not expected:
            return False
        key = self.request.headers.get('X-Restore-Key') or self.request.query_params.get('restore_key')
        return bool(key) and key == expected

    def get_permissions(self):
        if self.action in {'list', 'retrieve', 'download', 'restore', 'restore_upload'} and (
            self._allow_unauth_restore() or self._has_restore_key()
        ):
            return [AllowAny()]
        return super().get_permissions()

    def _is_local_request(self):
        addr = self.request.META.get('REMOTE_ADDR')
        return addr in {'127.0.0.1', '::1'}

    def _allow_unauth_restore(self):
        return bool(getattr(settings, 'DEBUG', False)) and self._is_local_request()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def _backup_root(self):
        return Path(settings.MEDIA_ROOT) / 'backups'

    def _resolve_backup_path(self, file_path):
        if not file_path:
            return None
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(settings.MEDIA_ROOT) / file_path
        backup_root = self._backup_root().resolve()
        try:
            path.resolve().relative_to(backup_root)
        except ValueError:
            return None
        return path

    def _hash_file(self, file_path):
        digest = hashlib.sha256()
        with open(file_path, 'rb') as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(chunk)
        return digest.hexdigest()

    def _create_backup_file(self):
        backup_root = self._backup_root()
        backup_root.mkdir(parents=True, exist_ok=True)
        stamp = timezone.now().strftime('%Y%m%d-%H%M%S')
        filename = f'backup-{stamp}.json'
        file_path = backup_root / filename
        call_command(
            'dumpdata',
            output=str(file_path),
            indent=2,
            natural_foreign=True,
            natural_primary=True,
        )
        size_bytes = file_path.stat().st_size
        checksum = self._hash_file(file_path)
        rel_path = str(Path('backups') / filename)
        return rel_path, size_bytes, checksum

    def _ensure_utf8_json(self, file_path):
        data = Path(file_path).read_bytes()
        text = None
        encoding_used = None
        for encoding in ('utf-8-sig', 'utf-8', 'cp1251'):
            try:
                text = data.decode(encoding)
                encoding_used = encoding
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            raise ValueError('Неподдерживаемая кодировка бэкапа. Используйте UTF-8.')
        if encoding_used == 'utf-8':
            return Path(file_path), None
        backup_root = self._backup_root()
        backup_root.mkdir(parents=True, exist_ok=True)
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            suffix='.json',
            delete=False,
            dir=str(backup_root),
        )
        temp_file.write(text)
        temp_file.close()
        return Path(temp_file.name), temp_file.name

    def _restore_from_file(self, file_path):
        normalized_path, temp_path = self._ensure_utf8_json(file_path)
        try:
            call_command('migrate', interactive=False, verbosity=0)
            call_command('flush', interactive=False, verbosity=0)
            call_command('loaddata', str(normalized_path), verbosity=0)
        finally:
            if temp_path:
                try:
                    Path(temp_path).unlink(missing_ok=True)
                except Exception:
                    pass

    def _issue_restore_tokens(self):
        User = get_user_model()
        user = (
            User.objects.filter(is_superuser=True).order_by('id').first()
            or User.objects.filter(role=ROLE_ADMIN).order_by('id').first()
            or User.objects.order_by('id').first()
        )
        if not user:
            return {}
        refresh = RefreshToken.for_user(user)
        return {'access': str(refresh.access_token), 'refresh': str(refresh)}

    def create(self, request, *args, **kwargs):
        try:
            rel_path, size_bytes, checksum = self._create_backup_file()
        except Exception as exc:  # noqa: BLE001 - return useful message
            record = BackupRecord.objects.create(
                created_by=request.user,
                status=BackupRecord.Status.FAILED,
            )
            return Response(
                {'error': {'message': f'Ошибка создания резервной копии: {exc}'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        record = BackupRecord.objects.create(
            created_by=request.user,
            status=BackupRecord.Status.CREATED,
            file_path=rel_path,
            size_bytes=size_bytes,
            checksum=checksum,
        )
        serializer = self.get_serializer(record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        record = self.get_object()
        file_path = self._resolve_backup_path(record.file_path)
        if not file_path or not file_path.exists():
            return Response(
                {'error': {'message': 'Файл резервной копии не найден.'}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=file_path.name)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        record = self.get_object()
        file_path = self._resolve_backup_path(record.file_path)
        if not file_path or not file_path.exists():
            return Response(
                {'error': {'message': 'Файл резервной копии не найден.'}},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            self._restore_from_file(file_path)
        except Exception as exc:  # noqa: BLE001 - return useful message
            return Response(
                {'error': {'message': f'Ошибка восстановления: {exc}'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        payload = {'detail': 'Восстановление выполнено.'}
        payload.update(self._issue_restore_tokens())
        return Response(payload)

    @action(detail=False, methods=['post'])
    def restore_upload(self, request):
        uploaded = request.FILES.get('backup_file')
        if not uploaded:
            return Response(
                {'error': {'message': 'Загрузите файл backup_file.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        backup_root = self._backup_root()
        backup_root.mkdir(parents=True, exist_ok=True)
        stamp = timezone.now().strftime('%Y%m%d-%H%M%S')
        filename = f'backup-upload-{stamp}.json'
        file_path = backup_root / filename
        with open(file_path, 'wb') as handle:
            for chunk in uploaded.chunks():
                handle.write(chunk)
        rel_path = str(Path('backups') / filename)
        size_bytes = file_path.stat().st_size
        checksum = self._hash_file(file_path)
        record = BackupRecord.objects.create(
            created_by=request.user,
            status=BackupRecord.Status.CREATED,
            file_path=rel_path,
            size_bytes=size_bytes,
            checksum=checksum,
        )
        try:
            self._restore_from_file(file_path)
        except Exception as exc:  # noqa: BLE001 - return useful message
            record.status = BackupRecord.Status.FAILED
            record.save(update_fields=['status'])
            return Response(
                {'error': {'message': f'Ошибка восстановления: {exc}'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        serializer = self.get_serializer(record)
        payload = serializer.data
        payload.update(self._issue_restore_tokens())
        return Response(payload, status=status.HTTP_201_CREATED)
