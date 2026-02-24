from django.conf import settings
from django.db import models
from results.models import TestResult

User = settings.AUTH_USER_MODEL


class Feedback(models.Model):
    manager = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedback_given',
        verbose_name='Менеджер'
    )
    test_result = models.ForeignKey(
        TestResult,
        on_delete=models.CASCADE,
        verbose_name='Результат теста'
    )
    comment = models.TextField(
        verbose_name='Комментарий'
    )
    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Оценка'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата'
    )


class TaskReview(models.Model):
    manager = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='task_reviews_given',
        verbose_name='Менеджер'
    )
    task_submission = models.ForeignKey(
        'courses.TaskSubmission',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Сдача задания'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий'
    )
    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Оценка'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата'
    )

    class Meta:
        verbose_name = 'Отзыв по заданию'
        verbose_name_plural = 'Отзывы по заданиям'

    def __str__(self):
        return f'{self.task_submission} — {self.manager}'
