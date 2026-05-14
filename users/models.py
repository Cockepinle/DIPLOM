from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()
    class Role(models.TextChoices):
        EMPLOYEE = 'EMPLOYEE', 'Сотрудник'
        MANAGER = 'MANAGER', 'Менеджер'
        ANALYST = 'ANALYST', 'Аналитик'
        ADMIN = 'ADMIN', 'Администратор'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        verbose_name='Роль'
    )

    email = models.EmailField(
        unique=True,
        verbose_name='Корпоративная почта'
    )

    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Отдел'
    )

    position = models.ForeignKey(
        'Position',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Должность'
    )
    specialty = models.ForeignKey(
        'Specialty',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Специальность'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Фото'
    )

    class RegistrationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Ожидает подтверждения'
        APPROVED = 'APPROVED', 'Подтверждён'
        REJECTED = 'REJECTED', 'Отклонён'

    registration_status = models.CharField(
        max_length=20,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.APPROVED,
        verbose_name='Статус регистрации',
    )
    registration_requested_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата заявки',
    )
    registration_reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата решения',
    )
    registration_reviewed_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registration_reviews',
        verbose_name='Решение принял',
    )
    registration_review_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий к решению',
    )

    class Meta(AbstractUser.Meta):
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(role='EMPLOYEE', specialty__isnull=False)
                    | ~models.Q(role='EMPLOYEE')
                ),
                name='user_employee_specialty_required',
            ),
        ]

    def __str__(self):
        return f'{self.last_name} {self.first_name} ({self.get_role_display()})'


class Specialty(models.Model):
    name = models.CharField(
        max_length=120,
        unique=True,
        verbose_name='Специальность'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Специальность'
        verbose_name_plural = 'Специальности'

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField(
        max_length=120,
        unique=True,
        verbose_name='Должность'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'

    def __str__(self):
        return self.name


class Competency(models.Model):
    name = models.CharField(
        max_length=120,
        unique=True,
        verbose_name='Компетенция'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    category = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Категория'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    def __str__(self):
        return self.name


class UserCompetency(models.Model):
    class Source(models.TextChoices):
        MANAGER = 'MANAGER', 'Оценка менеджера'
        TEST = 'TEST', 'Результаты тестов'
        TASK = 'TASK', 'Практические задания'
        SELF = 'SELF', 'Самооценка'
        SYSTEM = 'SYSTEM', 'Системная'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='competencies',
        verbose_name='Сотрудник'
    )
    competency = models.ForeignKey(
        Competency,
        on_delete=models.CASCADE,
        related_name='user_levels',
        verbose_name='Компетенция'
    )
    level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='Уровень (0-10)'
    )
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.MANAGER,
        verbose_name='Источник'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        unique_together = ('user', 'competency')
        verbose_name = 'Компетенция сотрудника'
        verbose_name_plural = 'Компетенции сотрудников'

    def __str__(self):
        return f'{self.user} — {self.competency} ({self.level})'


class CompetencyAssessment(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='competency_assessments',
        verbose_name='Сотрудник'
    )
    assessor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='competency_assessments_given',
        verbose_name='Оценил'
    )
    competency = models.ForeignKey(
        Competency,
        on_delete=models.CASCADE,
        related_name='assessments',
        verbose_name='Компетенция'
    )
    level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='Уровень (0-10)'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий'
    )
    test_result = models.ForeignKey(
        'results.TestResult',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Результат теста'
    )
    task_submission = models.ForeignKey(
        'courses.TaskSubmission',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Сдача задания'
    )
    assessed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата оценки'
    )

    class Meta:
        verbose_name = 'Оценка компетенции'
        verbose_name_plural = 'Оценки компетенций'

    def __str__(self):
        return f'{self.user} — {self.competency} ({self.level})'
