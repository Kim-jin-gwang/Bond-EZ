from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0002_newsarticle_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE news_article ADD COLUMN IF NOT EXISTS summary TEXT NOT NULL DEFAULT '';",
                    reverse_sql="ALTER TABLE news_article DROP COLUMN IF EXISTS summary;",
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="newsarticle",
                    name="summary",
                    field=models.TextField(blank=True),
                ),
            ],
        ),
    ]
