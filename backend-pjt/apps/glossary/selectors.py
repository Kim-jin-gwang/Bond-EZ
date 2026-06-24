from django.db.models import Q
from django.core.cache import cache

from .models import Glossary


SUMMARY_TERMS_CACHE_KEY = "glossary:summary-term-index:v2"
SUMMARY_TERMS_CACHE_TIMEOUT = 300


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


def terms_in_text(text):
    """Return active glossary entries whose names occur in the given text."""
    normalized_text = (text or "").replace("**", "").casefold()
    if not normalized_text:
        return []

    term_index = cache.get(SUMMARY_TERMS_CACHE_KEY)
    if term_index is None:
        term_index = [
            {"term_id": term["id"], "term_name": term["term_name"]}
            for term in Glossary.objects.filter(
                deleted_at__isnull=True,
                category__deleted_at__isnull=True,
            ).order_by("id").values("id", "term_name")
            if term["term_name"] and len(term["term_name"].strip()) >= 2
        ]
        cache.set(SUMMARY_TERMS_CACHE_KEY, term_index, SUMMARY_TERMS_CACHE_TIMEOUT)

    matched_candidates = sorted(
        (term for term in term_index if term["term_name"].casefold() in normalized_text),
        key=lambda term: len(term["term_name"]),
        reverse=True,
    )
    matched_index = []
    matched_names = set()
    for term in matched_candidates:
        normalized_name = term["term_name"].casefold()
        if normalized_name in matched_names:
            continue
        matched_names.add(normalized_name)
        matched_index.append(term)

    if not matched_index:
        return []

    matched_rows = (
        Glossary.objects.filter(
            id__in=[term["term_id"] for term in matched_index],
            deleted_at__isnull=True,
            category__deleted_at__isnull=True,
        )
        .select_related("category")
        .values(
            "id",
            "term_name",
            "difficulty",
            "description",
            "example_text",
            "category_id",
            "category__category_name",
        )
    )
    terms_by_id = {
        row["id"]: {
            "term_id": row["id"],
            "term_name": row["term_name"],
            "difficulty": row["difficulty"],
            "description": row["description"],
            "example_text": row["example_text"],
            "category": {
                "category_id": row["category_id"],
                "category_name": row["category__category_name"],
            },
        }
        for row in matched_rows
    }
    return [terms_by_id[term["term_id"]] for term in matched_index if term["term_id"] in terms_by_id]

