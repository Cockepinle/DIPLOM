from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = settings.AUTH_USER_MODEL


class Course(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name='Название курса'
    )
    description = models.TextField(
        verbose_name='Описание курса'
    )
    cover_image = models.ImageField(
        upload_to='course_covers/',
        blank=True,
        null=True,
        verbose_name='Обложка курса'
    )
    specialty = models.ForeignKey(
        'users.Specialty',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='Специальность'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_courses',
        verbose_name='Создатель курса'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )

    def __str__(self):
        return self.title


class CourseMaterial(models.Model):
    class MaterialType(models.TextChoices):
        TEXT = 'TEXT', 'Текст'
        LINK = 'LINK', 'Ссылка'
        FILE = 'FILE', 'Файл'

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='materials',
        verbose_name='Курс'
    )
    test = models.ForeignKey(
        'tests.Test',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='materials',
        verbose_name='Тест'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Название материала'
    )
    material_type = models.CharField(
        max_length=10,
        choices=MaterialType.choices,
        default=MaterialType.TEXT,
        verbose_name='Тип материала'
    )
    content = models.TextField(
        blank=True,
        verbose_name='Содержание'
    )
    url = models.URLField(
        blank=True,
        verbose_name='Ссылка'
    )
    file = models.FileField(
        upload_to='course_materials/',
        blank=True,
        null=True,
        verbose_name='Файл'
    )
    image = models.ImageField(
        upload_to='course_materials/images/',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )
    accent_color = models.CharField(
        max_length=7,
        blank=True,
        default='#f3b6d2',
        verbose_name='Акцентный цвет'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок'
    )
    is_required = models.BooleanField(
        default=True,
        verbose_name='Обязательный'
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Материал курса'
        verbose_name_plural = 'Материалы курсов'

    def __str__(self):
        return f'{self.course} — {self.title}'


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = 'ASSIGNED', 'Назначен'
        IN_PROGRESS = 'IN_PROGRESS', 'В процессе'
        COMPLETED = 'COMPLETED', 'Завершён'
        OVERDUE = 'OVERDUE', 'Просрочен'
        CANCELLED = 'CANCELLED', 'Отменён'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='course_enrollments',
        verbose_name='Сотрудник'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Курс'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='course_assignments',
        verbose_name='Назначил'
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        verbose_name='Дата назначения'
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Срок прохождения'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата начала'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата завершения'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ASSIGNED,
        verbose_name='Статус'
    )
    progress = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Прогресс (%)'
    )
    completed = models.BooleanField(
        default=False,
        verbose_name='Завершён'
    )

    class Meta:
        unique_together = ('user', 'course')
        verbose_name = 'Запись на курс'
        verbose_name_plural = 'Записи на курсы'

    def __str__(self):
        return f'{self.user} — {self.course}'


class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Курс'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Название урока'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    pages = models.JSONField(
        default=list,
        verbose_name='Страницы'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок'
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликован'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_lessons',
        verbose_name='Создатель'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'

    def __str__(self):
        return f'{self.course} — {self.title}'


class LessonAsset(models.Model):
    class AssetType(models.TextChoices):
        IMAGE = 'IMAGE', 'Изображение'
        FILE = 'FILE', 'Файл'
        VIDEO = 'VIDEO', 'Видео'

    file = models.FileField(
        upload_to='lesson_assets/',
        verbose_name='Файл'
    )
    asset_type = models.CharField(
        max_length=10,
        choices=AssetType.choices,
        verbose_name='Тип'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_assets',
        verbose_name='Загрузил'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Файл урока'
        verbose_name_plural = 'Файлы уроков'


class Task(models.Model):
    class TaskType(models.TextChoices):
        PRACTICAL = 'PRACTICAL', 'Практическое'
        CASE = 'CASE', 'Кейс'
        ESSAY = 'ESSAY', 'Эссе'
        PROJECT = 'PROJECT', 'Проект'

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True,
        verbose_name='Курс'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Название задания'
    )
    description = models.TextField(
        verbose_name='Описание задания'
    )
    attachment = models.FileField(
        upload_to='task_files/',
        blank=True,
        null=True,
        verbose_name='Файл задания'
    )
    criteria = models.TextField(
        blank=True,
        verbose_name='Критерии оценки'
    )
    task_type = models.CharField(
        max_length=20,
        choices=TaskType.choices,
        default=TaskType.PRACTICAL,
        verbose_name='Тип задания'
    )
    max_score = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Максимальный балл'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tasks',
        verbose_name='Создатель'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Срок выполнения'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name='Опубликовано'
    )

    def __str__(self):
        return self.title


class TaskAssignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = 'ASSIGNED', 'Назначено'
        IN_PROGRESS = 'IN_PROGRESS', 'В процессе'
        SUBMITTED = 'SUBMITTED', 'Отправлено'
        REVIEWED = 'REVIEWED', 'Проверено'
        RETURNED = 'RETURNED', 'Возвращено'
        CANCELLED = 'CANCELLED', 'Отменено'

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name='Задание'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='task_assignments',
        verbose_name='Сотрудник'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='task_assignments_given',
        verbose_name='Назначил'
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        verbose_name='Дата назначения'
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Срок выполнения'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ASSIGNED,
        verbose_name='Статус'
    )
    priority = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Приоритет (1-5)'
    )

    class Meta:
        verbose_name = 'Назначение задания'
        verbose_name_plural = 'Назначения заданий'

    def __str__(self):
        return f'{self.user} — {self.task}'


class TaskSubmission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Отправлено'
        NEEDS_CHANGES = 'NEEDS_CHANGES', 'Нужны правки'
        APPROVED = 'APPROVED', 'Принято'

    assignment = models.ForeignKey(
        TaskAssignment,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Назначение'
    )
    content = models.TextField(
        blank=True,
        verbose_name='Ответ'
    )
    file = models.FileField(
        upload_to='task_submissions/',
        blank=True,
        null=True,
        verbose_name='Файл'
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата отправки'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
        verbose_name='Статус'
    )
    score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Оценка'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата проверки'
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='task_reviews',
        verbose_name='Проверил'
    )

    class Meta:
        verbose_name = 'Сдача задания'
        verbose_name_plural = 'Сдачи заданий'

    def __str__(self):
        return f'{self.assignment} — {self.submitted_at:%Y-%m-%d}'
