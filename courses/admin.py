from django.contrib import admin
from .models import (
    Course,
    CourseMaterial,
    Enrollment,
    Lesson,
    LessonAsset,
    Task,
    TaskAssignment,
    TaskSubmission,
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'specialty', 'created_by', 'created_at', 'is_active')
    search_fields = ('title', 'specialty__name')
    list_filter = ('specialty', 'is_active', 'created_at')


@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'test', 'material_type', 'order', 'is_required')
    list_filter = ('material_type', 'is_required')
    search_fields = ('title', 'course__title')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'progress', 'completed')
    list_filter = ('status', 'completed', 'course')
    search_fields = ('user__email', 'user__last_name', 'course__title')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task_type', 'course', 'max_score', 'due_date', 'is_published', 'is_active')
    list_filter = ('task_type', 'is_published', 'is_active')
    search_fields = ('title',)


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'status', 'priority', 'due_date')
    list_filter = ('status', 'priority')
    search_fields = ('task__title', 'user__email')


@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'status', 'score', 'submitted_at', 'reviewed_at')
    list_filter = ('status', 'submitted_at', 'reviewed_at')
    search_fields = ('assignment__task__title', 'assignment__user__email', 'reviewer__email')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_published', 'created_by')
    list_filter = ('is_published', 'course')
    search_fields = ('title', 'course__title')


@admin.register(LessonAsset)
class LessonAssetAdmin(admin.ModelAdmin):
    list_display = ('file', 'asset_type', 'created_by', 'created_at')
    list_filter = ('asset_type',)
