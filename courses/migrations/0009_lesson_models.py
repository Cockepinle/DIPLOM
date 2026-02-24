from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0008_coursematerial_test_image_accent_color'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Название урока')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('pages', models.JSONField(default=list, verbose_name='Страницы')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('is_published', models.BooleanField(default=True, verbose_name='Опубликован')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='courses.course', verbose_name='Курс')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_lessons', to='users.user', verbose_name='Создатель')),
            ],
            options={
                'verbose_name': 'Урок',
                'verbose_name_plural': 'Уроки',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='LessonAsset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='lesson_assets/', verbose_name='Файл')),
                ('asset_type', models.CharField(choices=[('IMAGE', 'Изображение'), ('FILE', 'Файл'), ('VIDEO', 'Видео')], max_length=10, verbose_name='Тип')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lesson_assets', to='users.user', verbose_name='Загрузил')),
            ],
            options={
                'verbose_name': 'Файл урока',
                'verbose_name_plural': 'Файлы уроков',
                'ordering': ['-created_at'],
            },
        ),
    ]
