from django.contrib import admin
from .models import Feedback, TaskReview


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('manager', 'test_result', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('manager__email', 'test_result__user__email', 'test_result__test__title')


@admin.register(TaskReview)
class TaskReviewAdmin(admin.ModelAdmin):
    list_display = ('manager', 'task_submission', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('manager__email', 'task_submission__assignment__user__email', 'task_submission__assignment__task__title')
