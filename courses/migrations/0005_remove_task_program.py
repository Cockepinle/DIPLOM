from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('courses', '0004_course_specialty_task_due_date_task_is_published'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='program',
        ),
    ]
