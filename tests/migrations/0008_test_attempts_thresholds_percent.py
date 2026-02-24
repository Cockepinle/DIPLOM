from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


def convert_passing_score_to_percent(apps, schema_editor):
    Test = apps.get_model('tests', 'Test')
    Question = apps.get_model('tests', 'Question')

    for test in Test.objects.all().iterator():
        total_points = sum(
            Question.objects.filter(test_id=test.id).values_list('points', flat=True)
        )
        if total_points > 0:
            percent = int(round((test.passing_score / total_points) * 100))
            if percent > 100:
                percent = 100
            if percent < 0:
                percent = 0
        else:
            percent = 0
        Test.objects.filter(pk=test.pk).update(passing_score=percent)


def combine_attempts(apps, schema_editor):
    Test = apps.get_model('tests', 'Test')
    for test in Test.objects.all().only('id', 'attempts', 'trial_attempts'):
        total = (test.attempts or 0) + (test.trial_attempts or 0)
        Test.objects.filter(pk=test.pk).update(attempts=total)


class Migration(migrations.Migration):
    dependencies = [
        ('tests', '0007_question_points'),
    ]

    operations = [
        migrations.RenameField(
            model_name='test',
            old_name='final_attempts',
            new_name='attempts',
        ),
        migrations.RunPython(
            combine_attempts,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name='test',
            name='trial_attempts',
        ),
        migrations.RemoveField(
            model_name='test',
            name='show_correct_answers',
        ),
        migrations.AddField(
            model_name='test',
            name='warning_threshold',
            field=models.PositiveSmallIntegerField(
                default=50,
                validators=[MinValueValidator(0), MaxValueValidator(100)],
                verbose_name='Порог (желтый, %)',
            ),
        ),
        migrations.AddField(
            model_name='test',
            name='success_threshold',
            field=models.PositiveSmallIntegerField(
                default=70,
                validators=[MinValueValidator(0), MaxValueValidator(100)],
                verbose_name='Порог (зеленый, %)',
            ),
        ),
        migrations.AlterField(
            model_name='test',
            name='passing_score',
            field=models.IntegerField(
                default=70,
                validators=[MinValueValidator(0), MaxValueValidator(100)],
                verbose_name='Проходной балл (%)',
            ),
        ),
        migrations.RunPython(
            convert_passing_score_to_percent,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
