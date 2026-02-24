from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('analytics', '0002_remove_trainingevent_program_and_event_types'),
        ('courses', '0005_remove_task_program'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ProgramCourse',
        ),
        migrations.DeleteModel(
            name='ProgramEnrollment',
        ),
        migrations.DeleteModel(
            name='LearningProgram',
        ),
    ]
