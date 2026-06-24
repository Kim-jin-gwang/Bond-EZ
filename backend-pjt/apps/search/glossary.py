from math import ceil
from django.conf import settings
from apps.search.clients import get_elasticsearch_client

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

class SearchUnavailable(Exception):
    pass

def search_glossary(params):
    page = positive_int(params.get("page"), 1)
    size = min(positive_int(params.get("size"), DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE)
    client = get_elasticsearch_client()

    if client is None:
        raise SearchUnavailable("Elasticsearch client is not installed.")

    body = build_glossary_search_body(params, page, size)
    response = client.search(index=settings.ELASTICSEARCH_GLOSSARY_INDEX, **body)
    total = response["hits"]["total"]
    total_value = total.get("value", 0) if isinstance(total, dict) else total

    return {
        "data": [normalize_glossary_hit(hit["_source"]) for hit in response["hits"]["hits"]],
        "page": {
            "number": page,
            "size": size,
            "total_elements": total_value,
            "total_pages": ceil(total_value / size) if total_value else 0,
        },
    }

def build_glossary_search_body(params, page, size):
    must = []
    filters = []
    keyword = (params.get("keyword") or params.get("q") or "").strip()

    if keyword:
        must.append(
            {
                "bool": {
                    "should": [
                        {
                            "term": {
                                "term_name.keyword": {
                                    "value": keyword,
                                    "boost": 20
                                }
                            }
                        },
                        {
                            "multi_match": {
                                "query": keyword,
                                "fields": [
                                    "term_name^5",
                                    "description^2",
                                    "example_text^1"
                                ],
                                "type": "best_fields"
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            }
        )

    # Apply category filter
    category_id = params.get("category_id")
    if category_id:
        filters.append({"term": {"category.category_id": category_id}})

    # Apply difficulty filter
    difficulty = params.get("difficulty")
    if difficulty:
        filters.append({"term": {"difficulty": difficulty}})

    query = {"bool": {"filter": filters}}
    if must:
        query["bool"]["must"] = must
    else:
        query["bool"]["must"] = [{"match_all": {}}]

    return {
        "from_": (page - 1) * size,
        "size": size,
        "query": query,
        "sort": [{"_score": "desc"}, {"term_name.keyword": "asc"}],
        "track_total_hits": True,
    }

def normalize_glossary_hit(source):
    return {
        "term_id": source.get("term_id"),
        "term_name": source.get("term_name"),
        "difficulty": source.get("difficulty"),
        "description": source.get("description"),
        "example_text": source.get("example_text"),
        "category": {
            "category_id": source.get("category", {}).get("category_id"),
            "category_name": source.get("category", {}).get("category_name"),
        }
    }

def positive_int(value, default):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default
