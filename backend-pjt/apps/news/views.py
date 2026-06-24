from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from apps.common.responses import error, ok, paginated_response, parse_json_body

from .models import NewsProvider
from .selectors import filtered_news, get_news
from .serializers import serialize_news_detail, serialize_news_list_item, serialize_provider
from .services import summarize_news_by_id
from .summarizer import NewsSummarizerError, summarize_news_content


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


@csrf_exempt
@require_http_methods(["POST"])
def news_summary_by_id(request, news_id):
    body = parse_json_body(request)
    if body is None:
        return error("INVALID_JSON", "요청 본문이 올바른 JSON 형식이 아닙니다.")

    try:
        result = summarize_news_by_id(
            news_id,
            fallback_title=body.get("title", ""),
            fallback_content=body.get("content", ""),
        )
    except NewsSummarizerError as exc:
        status = 400 if exc.default_code == "NEWS_SUMMARY_INPUT_ERROR" else 500
        return error(exc.default_code, exc.message, status=status)

    if result is None:
        return error("NEWS_NOT_FOUND", "뉴스를 찾을 수 없습니다.", status=404)

    return ok(
        {
            "news_id": result["news"].id,
            "summary": result["summary"],
            "cached": result["cached"],
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def news_summarize(request):
    body = parse_json_body(request)
    if body is None:
        return error("INVALID_JSON", "요청 본문이 올바른 JSON 형식이 아닙니다.")

    news_id = body.get("news_id")
    if news_id:
        try:
            result = summarize_news_by_id(
                news_id,
                fallback_title=body.get("title", ""),
                fallback_content=body.get("content", ""),
            )
        except NewsSummarizerError as exc:
            status = 400 if exc.default_code == "NEWS_SUMMARY_INPUT_ERROR" else 500
            return error(exc.default_code, exc.message, status=status)

        if result is None:
            return error("NEWS_NOT_FOUND", "뉴스를 찾을 수 없습니다.", status=404)

        return ok(
            {
                "news_id": result["news"].id,
                "summary": result["summary"],
                "cached": result["cached"],
            }
        )

    title = body.get("title", "")
    content = body.get("content", "")
    if not content:
        return error(
            "MISSING_REQUIRED_FIELD",
            "content는 필수입니다.",
            details={"fields": ["content"]},
        )

    try:
        summary = summarize_news_content(title=title, content=content)
    except NewsSummarizerError as exc:
        return error(exc.default_code, exc.message, status=500)

    return ok({"summary": summary})

