from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('analytics', '0001_initial'),
        ('courses', '0005_remove_task_program'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trainingevent',
            name='program',
        ),
        migrations.AlterField(
            model_name='trainingevent',
            name='event_type',
            field=models.CharField(
                choices=[
                    ('ENROLLMENT_ASSIGNED', 'Назначен курс'),
                    ('COURSE_STARTED', 'Начат курс'),
                    ('COURSE_COMPLETED', 'Завершён курс'),
                    ('TEST_COMPLETED', 'Пройден тест'),
                    ('TASK_SUBMITTED', 'Отправлено задание'),
                    ('TASK_REVIEWED', 'Проверено задание'),
                ],
                max_length=30,
                verbose_name='Тип события',
            ),
        ),
    ]
