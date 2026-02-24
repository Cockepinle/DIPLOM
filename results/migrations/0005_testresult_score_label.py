from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('results', '0004_testanswer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testresult',
            name='score',
            field=models.IntegerField(blank=True, null=True, verbose_name='Результат (баллы)'),
        ),
    ]
