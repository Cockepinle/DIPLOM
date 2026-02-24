from django.db import migrations, models


def add_points_column(apps, schema_editor):
    table = 'tests_question'
    column = 'points'
    with schema_editor.connection.cursor() as cursor:
        existing = {
            col.name
            for col in schema_editor.connection.introspection.get_table_description(cursor, table)
        }
    if column in existing:
        return

    vendor = schema_editor.connection.vendor
    if vendor == 'postgresql':
        sql = f'ALTER TABLE "{table}" ADD COLUMN "{column}" integer NOT NULL DEFAULT 1'
    elif vendor == 'sqlite':
        sql = f'ALTER TABLE "{table}" ADD COLUMN "{column}" integer NOT NULL DEFAULT 1'
    else:
        sql = f'ALTER TABLE `{table}` ADD COLUMN `{column}` integer NOT NULL DEFAULT 1'
    schema_editor.execute(sql)


class Migration(migrations.Migration):
    dependencies = [
        ('tests', '0006_test_passing_score_questions'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    add_points_column,
                    reverse_code=migrations.RunPython.noop,
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name='question',
                    name='points',
                    field=models.IntegerField(default=1, verbose_name='Баллы'),
                ),
            ],
        ),
    ]
