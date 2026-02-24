from django.contrib import admin
from .models import TestResult, TestAnswer


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'test',
        'status',
        'score',
        'passed',
        'attempt_number',
        'completed_at',
    )
    list_filter = ('status', 'passed', 'completed_at')


@admin.register(TestAnswer)
class TestAnswerAdmin(admin.ModelAdmin):
    list_display = ('test_result', 'question', 'answer', 'answer_text', 'attachment', 'is_correct', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('test_result__user__email', 'question__text', 'answer__text', 'answer_text')
