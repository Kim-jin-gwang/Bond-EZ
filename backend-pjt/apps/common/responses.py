import json
from hashlib import md5
from math import ceil

from django.core.cache import cache
from django.core.paginator import EmptyPage, Paginator
from django.http import HttpResponse, JsonResponse


def parse_json_body(request):
    if not request.body:
        return {}

    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def ok(data, status=200):
    if status == 204:
        return HttpResponse(status=204)
    return JsonResponse(data, status=status, json_dumps_params={"ensure_ascii": False})


def error(error_code, message, status=400, details=None):
    payload = {
        "error_code": error_code,
        "message": message,
        "details": details or {},
    }
    return JsonResponse(payload, status=status, json_dumps_params={"ensure_ascii": False})


def paginated_response(queryset, request, serializer, default_size=20, max_size=100, count_cache_timeout=300):
    try:
        page_number = int(request.GET.get("page", 1))
        size = min(int(request.GET.get("size", default_size)), max_size)
    except ValueError:
        return error(
            "INVALID_QUERY_PARAMETER",
            "page와 size는 숫자 형식이어야 합니다.",
            details={"fields": ["page", "size"]},
        )

    if page_number < 1 or size < 1:
        return error(
            "INVALID_QUERY_PARAMETER",
            "page와 size는 1 이상이어야 합니다.",
            details={"fields": ["page", "size"]},
        )

    count = cached_queryset_count(queryset, request, timeout=count_cache_timeout)
    paginator = Paginator(queryset, size)
    paginator.count = count

    try:
        page = paginator.page(page_number)
    except EmptyPage:
        page = []

    total_pages = ceil(count / size) if count else 0
    return ok(
        {
            "data": [serializer(item) for item in page],
            "page": {
                "number": page_number,
                "size": size,
                "total_elements": count,
                "total_pages": total_pages,
            },
        }
    )


def cached_queryset_count(queryset, request, timeout=300):
    cache_key = count_cache_key(queryset, request)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    count = queryset.count()
    cache.set(cache_key, count, timeout=timeout)
    return count


def count_cache_key(queryset, request):
    params = request.GET.copy()
    params.pop("page", None)
    params.pop("size", None)
    normalized_params = sorted((key, params.getlist(key)) for key in params)
    payload = json.dumps(
        {
            "path": request.path,
            "model": queryset.model._meta.label_lower,
            "params": normalized_params,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return f"pagination-count:{md5(payload.encode('utf-8')).hexdigest()}"
