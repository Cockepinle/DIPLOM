from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0007_task_attachment'),
        ('tests', '0010_question_types_and_pairs'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursematerial',
            name='test',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='materials',
                to='tests.test',
                verbose_name='Тест',
            ),
        ),
        migrations.AddField(
            model_name='coursematerial',
            name='image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='course_materials/images/',
                verbose_name='Изображение',
            ),
        ),
        migrations.AddField(
            model_name='coursematerial',
            name='accent_color',
            field=models.CharField(
                blank=True,
                default='#f3b6d2',
                max_length=7,
                verbose_name='Акцентный цвет',
            ),
        ),
    ]
