import os

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from courses.models import Course

User = settings.AUTH_USER_MODEL

QUESTION_TYPE_SINGLE = 'SINGLE'
QUESTION_TYPE_MULTI = 'MULTI'
QUESTION_TYPE_MATCHING = 'MATCHING'
QUESTION_TYPE_ORDERING = 'ORDERING'
QUESTION_TYPE_SHORT = 'SHORT'
QUESTION_TYPE_LONG = 'LONG'

QUESTION_TYPE_CHOICES = (
    (QUESTION_TYPE_SINGLE, 'Вопрос-ответ (один вариант)'),
    (QUESTION_TYPE_MULTI, 'Вопрос-ответ (несколько вариантов)'),
    (QUESTION_TYPE_MATCHING, 'Сопоставление'),
    (QUESTION_TYPE_ORDERING, 'Последовательность'),
    (QUESTION_TYPE_SHORT, 'Краткий ответ'),
    (QUESTION_TYPE_LONG, 'Развернутый ответ'),
)

AUTO_QUESTION_TYPES = {
    QUESTION_TYPE_SINGLE,
    QUESTION_TYPE_MULTI,
    QUESTION_TYPE_MATCHING,
    QUESTION_TYPE_ORDERING,
}

MANUAL_QUESTION_TYPES = {
    QUESTION_TYPE_SHORT,
    QUESTION_TYPE_LONG,
}


class Test(models.Model):
    class EvaluationType(models.TextChoices):
        AUTO = 'AUTO', 'Автопроверка'
        MANUAL = 'MANUAL', 'На проверке'

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='tests',
        verbose_name='Курс'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Название теста'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание теста'
    )
    passing_score = models.IntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Проходной балл (%)'
    )
    evaluation_type = models.CharField(
        max_length=10,
        choices=EvaluationType.choices,
        default=EvaluationType.AUTO,
        verbose_name='Тип проверки'
    )
    attempts = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Попытки'
    )
    warning_threshold = models.PositiveSmallIntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Порог (желтый, %)'
    )
    success_threshold = models.PositiveSmallIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Порог (зеленый, %)'
    )
    retake_requires_new_attempt = models.BooleanField(
        default=True,
        verbose_name='Пересдача тратит попытку'
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Срок прохождения'
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name='Опубликован'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tests',
        verbose_name='Создатель'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    def __str__(self):
        return self.title

    def refresh_evaluation_type(self):
        manual_exists = self.questions.filter(type__in=MANUAL_QUESTION_TYPES).exists()
        new_type = self.EvaluationType.MANUAL if manual_exists else self.EvaluationType.AUTO
        if self.evaluation_type != new_type:
            Test.objects.filter(pk=self.pk).update(evaluation_type=new_type)


class Question(models.Model):
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Тест'
    )
    type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default=QUESTION_TYPE_SINGLE,
        verbose_name='Тип вопроса'
    )
    text = models.TextField(
        verbose_name='Текст вопроса'
    )
    points = models.IntegerField(
        default=1,
        verbose_name='Баллы'
    )
    image = models.FileField(
        upload_to='question_images/',
        blank=True,
        null=True,
        verbose_name='Файл'
    )

    def __str__(self):
        return self.text[:50]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.test_id:
            self.test.refresh_evaluation_type()

    def delete(self, *args, **kwargs):
        test_id = self.test_id
        result = super().delete(*args, **kwargs)
        if test_id:
            test = Test.objects.filter(pk=test_id).first()
            if test:
                test.refresh_evaluation_type()
        return result

    def is_image(self):
        if not self.image:
            return False
        ext = os.path.splitext(self.image.name)[1].lower()
        return ext in {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'}


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Вопрос'
    )
    text = models.CharField(
        max_length=255,
        verbose_name='Вариант ответа'
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name='Правильный ответ'
    )


class MatchingPair(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='matching_pairs',
        verbose_name='Вопрос'
    )
    left_text = models.CharField(
        max_length=255,
        verbose_name='Левая часть'
    )
    right_text = models.CharField(
        max_length=255,
        verbose_name='Правая часть'
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Порядок'
    )

    class Meta:
        verbose_name = 'Пара сопоставления'
        verbose_name_plural = 'Пары сопоставления'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.left_text} — {self.right_text}'


class OrderingItem(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='ordering_items',
        verbose_name='Вопрос'
    )
    text = models.CharField(
        max_length=255,
        verbose_name='Элемент'
    )
    position = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Правильная позиция'
    )

    class Meta:
        verbose_name = 'Элемент последовательности'
        verbose_name_plural = 'Элементы последовательности'
        ordering = ['position', 'id']

    def __str__(self):
        return self.text
