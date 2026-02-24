from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from tests.models import Test, Question, Answer

User = settings.AUTH_USER_MODEL


class TestResult(models.Model):
    class Status(models.TextChoices):
        UNDER_REVIEW = 'UNDER_REVIEW', 'На проверке'
        PASSED = 'PASSED', 'Пройден'
        FAILED = 'FAILED', 'Провален'
        RETURNED = 'RETURNED', 'На пересдаче'
        DECLINED = 'DECLINED', 'Отказался от пересдачи'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Сотрудник'
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        verbose_name='Тест'
    )
    score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Результат (%)'
    )
    passed = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='Пройден'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UNDER_REVIEW,
        verbose_name='Статус'
    )
    attempt_number = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Номер попытки'
    )
    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата прохождения'
    )
    retake_accepted = models.BooleanField(
        default=False,
        verbose_name='Пересдача принята'
    )

    def __str__(self):
        if self.score is None:
            return f'{self.user} — {self.test} — {self.get_status_display()}'
        return f'{self.user} — {self.test} — {self.score}'


class TestAnswer(models.Model):
    test_result = models.ForeignKey(
        TestResult,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Результат теста'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        verbose_name='Вопрос'
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Ответ'
    )
    answer_text = models.TextField(
        null=True,
        blank=True,
        verbose_name='Ответ текстом'
    )
    answer_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Ответ (данные)'
    )
    attachment = models.FileField(
        upload_to='test_answers/',
        blank=True,
        null=True,
        verbose_name='Файл'
    )
    is_correct = models.BooleanField(
        null=True,
        blank=True,
        default=None,
        verbose_name='Правильный ответ'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата'
    )

    class Meta:
        verbose_name = 'Ответ теста'
        verbose_name_plural = 'Ответы теста'
