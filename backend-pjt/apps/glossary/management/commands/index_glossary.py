from django.core.management.base import BaseCommand
from django.conf import settings
from apps.search.clients import get_elasticsearch_client
from apps.glossary.models import Glossary
from elasticsearch.helpers import bulk

class Command(BaseCommand):
    help = "Indexes all glossary terms from database to Elasticsearch."

    def add_arguments(self, parser):
        parser.add_argument(
            '--recreate',
            action='store_true',
            help='Recreate the glossary search index and re-index all documents',
        )

    def handle(self, *args, **options):
        from elasticsearch import Elasticsearch
        client = Elasticsearch(
            settings.ELASTICSEARCH_HOSTS,
            request_timeout=30.0
        )
        if not client:
            self.stderr.write("Elasticsearch client is not available.")
            return

        index_name = settings.ELASTICSEARCH_GLOSSARY_INDEX

        if options['recreate'] or not client.indices.exists(index=index_name):
            if client.indices.exists(index=index_name):
                self.stdout.write(f"Deleting existing index: {index_name}")
                client.indices.delete(index=index_name)

            self.stdout.write(f"Creating index: {index_name} with custom Korean analyzer mappings...")
            mapping = {
                "settings": {
                    "analysis": {
                        "analyzer": {
                            "korean_search": {
                                "type": "custom",
                                "tokenizer": "nori_tokenizer",
                                "filter": ["lowercase"]
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "term_id": { "type": "long" },
                        "term_name": {
                            "type": "text",
                            "analyzer": "korean_search",
                            "fields": {
                                "keyword": { "type": "keyword" }
                            }
                        },
                        "difficulty": { "type": "keyword" },
                        "description": {
                            "type": "text",
                            "analyzer": "korean_search"
                        },
                        "example_text": {
                            "type": "text",
                            "analyzer": "korean_search"
                        },
                        "category": {
                            "properties": {
                                "category_id": { "type": "long" },
                                "category_name": { "type": "keyword" }
                            }
                        }
                    }
                }
            }
            client.indices.create(index=index_name, body=mapping)

        # Index data
        self.stdout.write("Fetching glossary terms from database...")
        terms = Glossary.objects.filter(deleted_at__isnull=True, category__deleted_at__isnull=True).select_related("category")
        
        actions = []
        for term in terms:
            actions.append({
                "_index": index_name,
                "_id": str(term.id),
                "_source": {
                    "term_id": term.id,
                    "term_name": term.term_name,
                    "difficulty": term.difficulty,
                    "description": term.description,
                    "example_text": term.example_text,
                    "category": {
                        "category_id": term.category.id,
                        "category_name": term.category.category_name
                    }
                }
            })

        self.stdout.write(f"Indexing {len(actions)} terms into Elasticsearch...")
        success, failed = bulk(client, actions)
        self.stdout.write(self.style.SUCCESS(f"Successfully indexed {success} terms. (Failed: {len(failed) if isinstance(failed, list) else failed})"))
