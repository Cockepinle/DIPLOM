from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


def convert_scores_to_percent(apps, schema_editor):
    TestResult = apps.get_model('results', 'TestResult')
    Question = apps.get_model('tests', 'Question')

    for result in TestResult.objects.exclude(score__isnull=True).iterator():
        total_points = sum(
            Question.objects.filter(test_id=result.test_id).values_list('points', flat=True)
        )
        if total_points > 0:
            percent = int(round((result.score / total_points) * 100))
            if percent > 100:
                percent = 100
            if percent < 0:
                percent = 0
        else:
            percent = 0
        TestResult.objects.filter(pk=result.pk).update(score=percent)


class Migration(migrations.Migration):
    dependencies = [
        ('tests', '0008_test_attempts_thresholds_percent'),
        ('results', '0005_testresult_score_label'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='testresult',
            name='is_trial',
        ),
        migrations.AlterField(
            model_name='testresult',
            name='score',
            field=models.IntegerField(
                blank=True,
                null=True,
                validators=[MinValueValidator(0), MaxValueValidator(100)],
                verbose_name='Результат (%)',
            ),
        ),
        migrations.RunPython(
            convert_scores_to_percent,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
