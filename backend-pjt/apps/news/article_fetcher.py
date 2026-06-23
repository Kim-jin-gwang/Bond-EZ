from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from .summarizer import NewsSummaryInputError


REQUEST_TIMEOUT_SECONDS = 8
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
ARTICLE_SELECTORS = (
    "#newsct_article",
    "#dic_area",
    "#news_read",
    "#article-view-content-div",
    "#articleBodyContents",
    "#articleBody",
    ".articleCont",
    "article",
)


def fetch_article_content(url):
    normalized_url = normalize_article_url(url)
    if not normalized_url:
        raise NewsSummaryInputError("뉴스 URL이 없습니다.")

    try:
        response = requests.get(
            normalized_url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise NewsSummaryInputError("뉴스 URL에서 본문을 가져오지 못했습니다.") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    remove_noise(soup)

    for selector in ARTICLE_SELECTORS:
        element = soup.select_one(selector)
        content = normalize_content(element.get_text(" ", strip=True) if element else "")
        if content:
            return content

    content = normalize_content(soup.get_text(" ", strip=True))
    if content:
        return content

    raise NewsSummaryInputError("뉴스 URL에서 요약할 본문을 찾지 못했습니다.")


def normalize_article_url(url):
    parsed_url = urlparse(str(url or "").strip())
    if not parsed_url.scheme or not parsed_url.netloc:
        return ""

    if "finance.naver.com" in parsed_url.netloc and "news_read.naver" in parsed_url.path:
        params = parse_qs(parsed_url.query)
        office_id = params.get("office_id", [None])[0]
        article_id = params.get("article_id", [None])[0]
        if office_id and article_id:
            return f"https://n.news.naver.com/mnews/article/{office_id}/{article_id}"

    return parsed_url.geturl()


def remove_noise(soup):
    for tag in soup(["script", "style", "noscript", "iframe", "aside", "nav", "footer"]):
        tag.decompose()


def normalize_content(content):
    return " ".join(str(content or "").split())
