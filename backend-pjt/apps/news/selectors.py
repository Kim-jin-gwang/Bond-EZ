from django.db.models import Q

from .models import News, NewsArticle


def filtered_news(params):
    if not News.objects.filter(deleted_at__isnull=True).exists():
        queryset = NewsArticle.objects.all().order_by("-write_date", "-id")

        keyword = params.get("keyword")
        if keyword:
            queryset = queryset.filter(Q(title__icontains=keyword) | Q(source__icontains=keyword))

        published_from = params.get("published_from")
        if published_from:
            queryset = queryset.filter(write_date__date__gte=published_from)

        published_to = params.get("published_to")
        if published_to:
            queryset = queryset.filter(write_date__date__lte=published_to)

        return queryset

    queryset = (
        News.objects.filter(deleted_at__isnull=True, source__deleted_at__isnull=True)
        .select_related("source")
        .order_by("-published_at", "-id")
    )

    keyword = params.get("keyword")
    if keyword:
        queryset = queryset.filter(
            Q(title__icontains=keyword)
            | Q(summary__icontains=keyword)
        )

    provider_id = params.get("provider_id")
    if provider_id:
        queryset = queryset.filter(source_id=provider_id)

    published_from = params.get("published_from")
    if published_from:
        queryset = queryset.filter(published_at__date__gte=published_from)

    published_to = params.get("published_to")
    if published_to:
        queryset = queryset.filter(published_at__date__lte=published_to)

    return queryset


def get_news(news_id):
    if not News.objects.filter(deleted_at__isnull=True).exists():
        return NewsArticle.objects.filter(id=news_id).first()

    return (
        News.objects.filter(id=news_id, deleted_at__isnull=True, source__deleted_at__isnull=True)
        .select_related("source")
        .first()
    )

