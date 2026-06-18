from django.views.decorators.http import require_GET

from apps.common.responses import error, ok, paginated_response

from .models import NewsProvider
from .selectors import filtered_news, get_news
from .serializers import serialize_news_detail, serialize_news_list_item, serialize_provider


@require_GET
def news_list(request):
    return paginated_response(filtered_news(request.GET), request, serialize_news_list_item)


@require_GET
def news_detail(request, news_id):
    news = get_news(news_id)
    if news is None:
        return error("NEWS_NOT_FOUND", "뉴스를 찾을 수 없습니다.", status=404)
    return ok(serialize_news_detail(news))


@require_GET
def provider_list(request):
    providers = NewsProvider.objects.filter(deleted_at__isnull=True).order_by("provider_name")
    return ok({"items": [serialize_provider(provider) for provider in providers]})

