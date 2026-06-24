# Generated manually for the news API.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="NewsProvider",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider_name", models.CharField(max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "news_provider", "indexes": [models.Index(fields=["provider_name"], name="news_provid_provider_592f19_idx")]},
        ),
        migrations.CreateModel(
            name="News",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("url", models.URLField(max_length=500, unique=True)),
                ("summary", models.TextField(blank=True)),
                ("content", models.TextField(blank=True)),
                ("published_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="news", to="news.newsprovider")),
            ],
            options={
                "db_table": "news",
                "indexes": [
                    models.Index(fields=["published_at"], name="news_publish_a1f8fb_idx"),
                    models.Index(fields=["source"], name="news_source__f3d10a_idx"),
                    models.Index(fields=["title"], name="news_title_593401_idx"),
                ],
            },
        ),
    ]
