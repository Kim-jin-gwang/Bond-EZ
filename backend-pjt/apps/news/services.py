from django.db import transaction

from .article_fetcher import fetch_article_content
from .models import News, NewsArticle
from .summarizer import NewsSummaryInputError, is_valid_summary, summarize_news_content


def summarize_news_by_id(news_id, fallback_title="", fallback_content=""):
    model, queryset = get_summary_target_queryset(news_id)
    if queryset is None:
        return None

    article = queryset.first()
    if article is None:
        return None

    cached_summary = normalize_cached_summary(article.summary)
    if cached_summary:
        return {
            "news": article,
            "summary": cached_summary,
            "cached": True,
        }

    with transaction.atomic():
        article = get_locked_summary_target(model, news_id)
        if article is None:
            return None

        cached_summary = normalize_cached_summary(article.summary)
        if cached_summary:
            return {
                "news": article,
                "summary": cached_summary,
                "cached": True,
            }

        content = normalize_content(fallback_content)
        if not content:
            content = fetch_article_content(article.url)
        if not content:
            raise NewsSummaryInputError("요약할 뉴스 본문이 DB에 없습니다.")

        title = article.title or fallback_title
        summary = summarize_news_content(title=title, content=content)
        article.summary = summary
        article.save(update_fields=get_summary_update_fields(article))

        return {
            "news": article,
            "summary": summary,
            "cached": False,
        }


def get_summary_target_queryset(news_id):
    news_queryset = News.objects.filter(
        id=news_id,
        deleted_at__isnull=True,
        source__deleted_at__isnull=True,
    ).select_related("source")
    if news_queryset.exists():
        return News, news_queryset

    article_queryset = NewsArticle.objects.filter(id=news_id)
    if article_queryset.exists():
        return NewsArticle, article_queryset

    return None, None


def get_locked_summary_target(model, news_id):
    queryset = model.objects.select_for_update().filter(id=news_id)
    if model is News:
        queryset = queryset.filter(
            deleted_at__isnull=True,
            source__deleted_at__isnull=True,
        ).select_related("source")
    return queryset.first()


def get_summary_update_fields(article):
    fields = ["summary"]
    if isinstance(article, News):
        fields.append("updated_at")
    return fields


def normalize_summary(summary):
    return str(summary or "").strip()


def normalize_cached_summary(summary):
    summary = normalize_summary(summary)
    return summary if is_valid_summary(summary) else ""


def normalize_content(content):
    return str(content or "").strip()
