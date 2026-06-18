from django.db.models import Q

from .models import Glossary


def filtered_terms(params):
    queryset = (
        Glossary.objects.filter(deleted_at__isnull=True, category__deleted_at__isnull=True)
        .select_related("category")
        .order_by("term_name")
    )

    keyword = params.get("keyword")
    if keyword:
        queryset = queryset.filter(
            Q(term_name__icontains=keyword)
            | Q(description__icontains=keyword)
            | Q(example_text__icontains=keyword)
        )

    category_id = params.get("category_id")
    if category_id:
        queryset = queryset.filter(category_id=category_id)

    difficulty = params.get("difficulty")
    if difficulty:
        queryset = queryset.filter(difficulty=difficulty)

    return queryset


def get_term(term_id):
    return (
        Glossary.objects.filter(id=term_id, deleted_at__isnull=True, category__deleted_at__isnull=True)
        .select_related("category")
        .first()
    )

