from django.views.decorators.http import require_GET

from apps.common.responses import error, ok, paginated_response

from .models import GlossaryCategory
from .selectors import filtered_terms, get_term
from .serializers import serialize_category, serialize_term_detail, serialize_term_list_item


@require_GET
def category_list(request):
    categories = GlossaryCategory.objects.filter(deleted_at__isnull=True).order_by("category_name")
    return ok({"items": [serialize_category(category) for category in categories]})


@require_GET
def glossary_list(request):
    return paginated_response(filtered_terms(request.GET), request, serialize_term_list_item)


@require_GET
def glossary_detail(request, term_id):
    term = get_term(term_id)
    if term is None:
        return error("GLOSSARY_TERM_NOT_FOUND", "용어를 찾을 수 없습니다.", status=404)
    return ok(serialize_term_detail(term))

