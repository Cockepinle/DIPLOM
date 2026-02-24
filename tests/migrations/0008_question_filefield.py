from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('tests', '0007_question_points'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='image',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='question_images/',
                verbose_name='Файл',
            ),
        ),
    ]
