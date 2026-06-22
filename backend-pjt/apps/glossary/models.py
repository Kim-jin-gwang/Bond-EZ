from django.db import models


class GlossaryCategory(models.Model):
    id = models.BigIntegerField(primary_key=True, db_column="category_id")
    category_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "glossary_category"
        indexes = [models.Index(fields=["category_name"])]

    def __str__(self):
        return self.category_name


class Glossary(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "EASY", "쉬움"
        MEDIUM = "MEDIUM", "보통"
        HARD = "HARD", "어려움"

    id = models.BigIntegerField(primary_key=True, db_column="term_id")
    category = models.ForeignKey(GlossaryCategory, on_delete=models.PROTECT, related_name="terms")
    term_name = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.EASY)
    description = models.TextField()
    example_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "glossary"
        indexes = [
            models.Index(fields=["term_name"]),
            models.Index(fields=["category"]),
            models.Index(fields=["difficulty"]),
        ]

    def __str__(self):
        return self.term_name
