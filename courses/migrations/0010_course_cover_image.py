from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_lesson_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='cover_image',
            field=models.ImageField(blank=True, null=True, upload_to='course_covers/', verbose_name='Обложка курса'),
        ),
    ]
