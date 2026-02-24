from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('courses', '0006_remove_program_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='attachment',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='task_files/',
                verbose_name='Файл задания',
            ),
        ),
    ]
