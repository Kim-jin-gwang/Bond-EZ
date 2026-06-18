from django.db.models import Q

from .models import News


def filtered_news(params):
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
            | Q(content__icontains=keyword)
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
    return (
        News.objects.filter(id=news_id, deleted_at__isnull=True, source__deleted_at__isnull=True)
        .select_related("source")
        .first()
    )

