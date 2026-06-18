import json
from math import ceil

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


def paginated_response(queryset, request, serializer, default_size=20, max_size=100):
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

    paginator = Paginator(queryset, size)
    try:
        page = paginator.page(page_number)
    except EmptyPage:
        page = []

    total_pages = ceil(paginator.count / size) if paginator.count else 0
    return ok(
        {
            "data": [serializer(item) for item in page],
            "page": {
                "number": page_number,
                "size": size,
                "total_elements": paginator.count,
                "total_pages": total_pages,
            },
        }
    )
