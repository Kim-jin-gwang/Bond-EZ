from django.db import models


class NewsProvider(models.Model):
    provider_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "news_provider"
        indexes = [models.Index(fields=["provider_name"])]

    def __str__(self):
        return self.provider_name


class News(models.Model):
    source = models.ForeignKey(NewsProvider, on_delete=models.PROTECT, related_name="news")
    title = models.CharField(max_length=255)
    url = models.URLField(max_length=500, unique=True)
    summary = models.TextField(blank=True)
    content = models.TextField(blank=True)
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "news"
        indexes = [
            models.Index(fields=["published_at"]),
            models.Index(fields=["source"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return self.title


class NewsArticle(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    source = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(max_length=500, blank=True, null=True)
    write_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "news_article"
        indexes = [
            models.Index(fields=["write_date"]),
            models.Index(fields=["title"]),
        ]
