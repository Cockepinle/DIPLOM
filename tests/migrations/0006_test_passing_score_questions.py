from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('tests', '0005_test_review_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='test',
            name='passing_score',
            field=models.IntegerField(default=1, verbose_name='Проходной балл (вопросов)'),
        ),
    ]
