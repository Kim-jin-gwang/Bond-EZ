def serialize_provider(provider):
    return {
        "provider_id": provider.id,
        "provider_name": provider.provider_name,
    }


def serialize_news_list_item(news):
    if isinstance(news.source, str):
        return {
            "news_id": news.id,
            "source": {
                "provider_id": None,
                "provider_name": news.source,
            },
            "title": news.title,
            "url": news.url,
            "summary": "",
            "published_at": news.write_date.isoformat() if news.write_date else None,
        }

    return {
        "news_id": news.id,
        "source": serialize_provider(news.source),
        "title": news.title,
        "url": news.url,
        "summary": news.summary,
        "published_at": news.published_at.isoformat() if news.published_at else None,
    }


def serialize_news_detail(news):
    data = serialize_news_list_item(news)
    data["content"] = getattr(news, "content", "") or data.get("summary", "")
    return data

