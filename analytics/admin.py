from django.contrib import admin
from .models import (
    AuditLog,
    BackupRecord,
    Dashboard,
    Report,
    ReportExport,
    TrainingEvent,
)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor', 'object_type', 'object_id', 'created_at')
    list_filter = ('action', 'object_type', 'created_at')
    search_fields = ('action', 'object_id', 'actor__email')


@admin.register(TrainingEvent)
class TrainingEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'course', 'test', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('user__email', 'user__last_name')


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'is_shared', 'created_at')
    list_filter = ('is_shared', 'created_at')
    search_fields = ('title', 'owner__email')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'report_type', 'created_at')
    list_filter = ('report_type', 'created_at')
    search_fields = ('title', 'owner__email')


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ('report', 'export_format', 'status', 'generated_at')
    list_filter = ('export_format', 'status')
    search_fields = ('report__title',)


@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'status', 'created_at', 'size_bytes')
    list_filter = ('status', 'created_at')
    search_fields = ('created_by__email',)
