from django.conf import settings

try:
    from elasticsearch import Elasticsearch
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    Elasticsearch = None


def get_elasticsearch_client():
    if Elasticsearch is None:
        return None

    return Elasticsearch(
        settings.ELASTICSEARCH_HOSTS,
        request_timeout=settings.ELASTICSEARCH_REQUEST_TIMEOUT,
        retry_on_timeout=False,
    )
