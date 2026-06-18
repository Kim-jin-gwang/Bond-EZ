# Generated manually for the glossary API.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="GlossaryCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category_name", models.CharField(max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "glossary_category", "indexes": [models.Index(fields=["category_name"], name="glossary_ca_categor_e54c05_idx")]},
        ),
        migrations.CreateModel(
            name="Glossary",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("term_name", models.CharField(max_length=255)),
                ("difficulty", models.CharField(choices=[("EASY", "쉬움"), ("MEDIUM", "보통"), ("HARD", "어려움")], default="EASY", max_length=20)),
                ("description", models.TextField()),
                ("example_text", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="terms", to="glossary.glossarycategory")),
            ],
            options={
                "db_table": "glossary",
                "indexes": [
                    models.Index(fields=["term_name"], name="glossary_term_na_3cc1bb_idx"),
                    models.Index(fields=["category"], name="glossary_categor_570ec9_idx"),
                    models.Index(fields=["difficulty"], name="glossary_difficu_3f3794_idx"),
                ],
            },
        ),
    ]
