from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class AuditLog(models.Model):
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='Пользователь'
    )
    action = models.CharField(
        max_length=100,
        verbose_name='Действие'
    )
    object_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Тип объекта'
    )
    object_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='ID объекта'
    )
    message = models.TextField(
        blank=True,
        verbose_name='Сообщение'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Метаданные'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP-адрес'
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='User-Agent'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Журнал аудита'
        verbose_name_plural = 'Журнал аудита'

    def __str__(self):
        return f'{self.action} — {self.created_at:%Y-%m-%d %H:%M}'


class TrainingEvent(models.Model):
    class EventType(models.TextChoices):
        ENROLLMENT_ASSIGNED = 'ENROLLMENT_ASSIGNED', 'Назначен курс'
        COURSE_STARTED = 'COURSE_STARTED', 'Начат курс'
        COURSE_COMPLETED = 'COURSE_COMPLETED', 'Завершён курс'
        TEST_COMPLETED = 'TEST_COMPLETED', 'Пройден тест'
        TASK_SUBMITTED = 'TASK_SUBMITTED', 'Отправлено задание'
        TASK_REVIEWED = 'TASK_REVIEWED', 'Проверено задание'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='training_events',
        verbose_name='Сотрудник'
    )
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        verbose_name='Тип события'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Курс'
    )
    test = models.ForeignKey(
        'tests.Test',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Тест'
    )
    task = models.ForeignKey(
        'courses.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Задание'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Метаданные'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Событие обучения'
        verbose_name_plural = 'События обучения'

    def __str__(self):
        return f'{self.user} — {self.get_event_type_display()}'


class Dashboard(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboards',
        verbose_name='Владелец'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    config = models.JSONField(
        default=dict,
        verbose_name='Конфигурация'
    )
    is_shared = models.BooleanField(
        default=False,
        verbose_name='Общий доступ'
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
        verbose_name = 'Дашборд'
        verbose_name_plural = 'Дашборды'

    def __str__(self):
        return self.title


class Report(models.Model):
    class ReportType(models.TextChoices):
        PROGRESS = 'PROGRESS', 'Прогресс обучения'
        COMPETENCY = 'COMPETENCY', 'Компетенции'
        RESULTS = 'RESULTS', 'Результаты тестов'
        ACTIVITY = 'ACTIVITY', 'Активность'
        CUSTOM = 'CUSTOM', 'Пользовательский'

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Автор'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    report_type = models.CharField(
        max_length=20,
        choices=ReportType.choices,
        default=ReportType.PROGRESS,
        verbose_name='Тип отчёта'
    )
    filters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Фильтры'
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
        verbose_name = 'Отчёт'
        verbose_name_plural = 'Отчёты'

    def __str__(self):
        return self.title


class ReportExport(models.Model):
    class Format(models.TextChoices):
        PDF = 'PDF', 'PDF'
        XLSX = 'XLSX', 'Excel'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'В очереди'
        READY = 'READY', 'Готов'
        FAILED = 'FAILED', 'Ошибка'

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='exports',
        verbose_name='Отчёт'
    )
    export_format = models.CharField(
        max_length=10,
        choices=Format.choices,
        verbose_name='Формат'
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус'
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Путь к файлу'
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата генерации'
    )

    class Meta:
        verbose_name = 'Экспорт отчёта'
        verbose_name_plural = 'Экспорт отчётов'

    def __str__(self):
        return f'{self.report} — {self.export_format}'


class BackupRecord(models.Model):
    class Status(models.TextChoices):
        CREATED = 'CREATED', 'Создано'
        RESTORING = 'RESTORING', 'Восстановление'
        SUCCESS = 'SUCCESS', 'Успешно'
        FAILED = 'FAILED', 'Ошибка'
        DELETED = 'DELETED', 'Удалено'

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='backups',
        verbose_name='Создал'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата'
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.CREATED,
        verbose_name='Статус'
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Путь к файлу'
    )
    size_bytes = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='Размер (байт)'
    )
    checksum = models.CharField(
        max_length=128,
        blank=True,
        verbose_name='Контрольная сумма'
    )
    error_message = models.TextField(
        blank=True,
        verbose_name='Сообщение об ошибке'
    )

    class Meta:
        verbose_name = 'Резервная копия'
        verbose_name_plural = 'Резервные копии'

    def __str__(self):
        return f'Backup {self.created_at:%Y-%m-%d %H:%M}'

