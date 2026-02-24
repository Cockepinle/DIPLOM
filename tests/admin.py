from django.contrib import admin
from .models import Test, Question, Answer, MatchingPair, OrderingItem


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


class MatchingPairInline(admin.TabularInline):
    model = MatchingPair
    extra = 1


class OrderingItemInline(admin.TabularInline):
    model = OrderingItem
    extra = 1


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'course',
        'passing_score',
        'evaluation_type',
        'attempts',
        'warning_threshold',
        'success_threshold',
        'retake_requires_new_attempt',
        'due_date',
        'is_published',
    )
    search_fields = ('title', 'course__title')
    list_filter = (
        'course',
        'evaluation_type',
        'retake_requires_new_attempt',
        'is_published',
        'due_date',
    )
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'type', 'test', 'points')
    search_fields = ('text', 'test__title')
    list_filter = ('test',)
    inlines = [AnswerInline, MatchingPairInline, OrderingItemInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    search_fields = ('text', 'question__text')
    list_filter = ('is_correct',)
