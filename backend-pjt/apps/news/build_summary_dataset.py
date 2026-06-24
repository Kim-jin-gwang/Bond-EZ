from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parents[1]
if str(CURRENT_DIR) in sys.path:
    sys.path.remove(str(CURRENT_DIR))
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from apps.news.article_fetcher import fetch_article_content
from apps.news.models import News
from apps.news.summarizer import CONTENT_MAX_CHARS, clean_summary, is_valid_summary


DEFAULT_TRAIN_OUTPUT = CURRENT_DIR / "summary_examples.jsonl"
DEFAULT_EVAL_OUTPUT = CURRENT_DIR / "summary_eval_examples.jsonl"
TOPIC_PATTERNS = (
    ("market", r"코스피|코스닥|증시|주가|폭락|급락"),
    ("rates_bonds", r"금리|채권|국채|수익률|환율"),
    ("policy_tax", r"세금|양도세|금융위|금감원|정책|규제|세법"),
    ("funds", r"ETF|펀드|레버리지|리츠"),
    ("companies", r"삼성|하이닉스|기업|상장|실적"),
    ("global_assets", r"미국|해외|스페이스X|비트코인|가상자산"),
)


def select_candidates(limit):
    rows = list(
        News.objects.filter(deleted_at__isnull=True, source__deleted_at__isnull=True)
        .select_related("source")
        .order_by("-published_at", "-id")
    )
    selected = []
    selected_ids = set()
    per_topic = max(2, limit // len(TOPIC_PATTERNS))

    for topic, pattern in TOPIC_PATTERNS:
        topic_rows = [row for row in rows if re.search(pattern, row.title or "", re.IGNORECASE)]
        topic_rows.sort(
            key=lambda row: (sum(item[1].source_id == row.source_id for item in selected), -row.id)
        )
        for row in topic_rows:
            if row.id in selected_ids:
                continue
            selected.append((topic, row))
            selected_ids.add(row.id)
            if sum(selected_topic == topic for selected_topic, _ in selected) >= per_topic:
                break

    for row in rows:
        if len(selected) >= limit:
            break
        if row.id in selected_ids:
            continue
        selected.append(("other", row))
        selected_ids.add(row.id)

    return selected[:limit]


def fetch_examples(candidate_limit, target_count):
    examples = []
    for topic, article in select_candidates(candidate_limit):
        try:
            content = fetch_article_content(article.url)
        except Exception as exc:
            print(f"skip news_id={article.id}: {exc}", file=sys.stderr)
            continue
        if len(content) < 200:
            continue
        examples.append(
            {
                "news_id": article.id,
                "topic": topic,
                "provider": article.source.provider_name,
                "title": article.title,
                "content": content[:CONTENT_MAX_CHARS],
            }
        )
        if len(examples) >= target_count:
            break
    return examples


def fetch_examples_by_ids(news_ids):
    articles = {
        article.id: article
        for article in News.objects.filter(
            id__in=news_ids,
            deleted_at__isnull=True,
            source__deleted_at__isnull=True,
        ).select_related("source")
    }
    examples = []
    for news_id in news_ids:
        article = articles.get(news_id)
        if article is None:
            raise RuntimeError(f"News not found for annotation: news_id={news_id}")
        content = fetch_article_content(article.url)
        if len(content) < 200:
            raise RuntimeError(f"Article content is too short: news_id={news_id}")
        topic = next(
            (name for name, pattern in TOPIC_PATTERNS if re.search(pattern, article.title or "", re.IGNORECASE)),
            "other",
        )
        examples.append(
            {
                "news_id": article.id,
                "topic": topic,
                "provider": article.source.provider_name,
                "title": article.title,
                "content": content[:CONTENT_MAX_CHARS],
            }
        )
    return examples


def generate_summaries(examples, model, batch_size):
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required.")

    results = []
    for offset in range(0, len(examples), batch_size):
        batch = examples[offset : offset + batch_size]
        prompt = build_teacher_prompt(batch)
        summaries = call_gemini(model, api_key, prompt)
        by_id = {int(item["news_id"]): item["summary"] for item in summaries}

        for example in batch:
            summary = clean_summary(by_id.get(example["news_id"], ""))
            if not is_valid_summary(summary):
                print(f"invalid summary news_id={example['news_id']}: {summary}", file=sys.stderr)
                continue
            results.append({**example, "summary": summary})
        print(f"generated {len(results)}/{len(examples)}")
    return results


def build_teacher_prompt(batch):
    articles = [
        {
            "news_id": item["news_id"],
            "title": item["title"],
            "content": item["content"],
        }
        for item in batch
    ]
    return (
        "당신은 한국 금융 뉴스 데이터셋을 만드는 편집자입니다. 각 기사마다 사실에 충실한 골드 요약을 작성하세요.\n"
        "규칙:\n"
        "- 핵심 주체, 사건, 원인 또는 영향을 포함합니다.\n"
        "- 200자 이내의 완전한 한국어 서술문 1~2개로 작성합니다.\n"
        "- 앵커 도입, 기자 소개, 인터뷰 원문, 사진 설명, 독자에게 묻는 표현은 제외합니다.\n"
        "- 제목과 본문에 없는 사실을 추가하지 않습니다.\n"
        "- JSON 배열만 반환하고 각 원소는 news_id와 summary만 포함합니다.\n\n"
        f"기사 목록:\n{json.dumps(articles, ensure_ascii=False)}"
    )


def call_gemini(model, api_key, prompt):
    if api_key and not api_key.strip().startswith("AIzaSy"):
        url = f"https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    else:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
        },
    }
    response = None
    for attempt in range(4):
        response = requests.post(
            url,
            headers={"x-goog-api-key": api_key},
            json=payload,
            timeout=120,
        )
        if response.status_code not in (429, 500, 502, 503, 504):
            break
        if attempt < 3:
            time.sleep(2**attempt)

    if response is None:
        raise RuntimeError("Gemini API did not return a response.")
    response.raise_for_status()
    response_payload = response.json()
    text = response_payload["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


def write_jsonl(path, examples):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for example in examples:
            file.write(json.dumps(example, ensure_ascii=False) + "\n")


def split_examples(examples, eval_count):
    if eval_count <= 0:
        return examples, []
    eval_count = min(eval_count, len(examples))
    step = len(examples) / eval_count
    eval_indices = {min(len(examples) - 1, round((index + 1) * step) - 1) for index in range(eval_count)}
    train_examples = [example for index, example in enumerate(examples) if index not in eval_indices]
    eval_examples = [example for index, example in enumerate(examples) if index in eval_indices]
    return train_examples, eval_examples


def main():
    parser = argparse.ArgumentParser(description="Build reviewed DSPy summary dataset drafts from real news.")
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--eval-count", type=int, default=6)
    parser.add_argument("--candidate-limit", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--teacher-model", default="gemini-3.5-flash")
    parser.add_argument("--train-output", default=str(DEFAULT_TRAIN_OUTPUT))
    parser.add_argument("--eval-output", default=str(DEFAULT_EVAL_OUTPUT))
    parser.add_argument("--export-only", action="store_true")
    parser.add_argument("--annotation-file")
    args = parser.parse_args()

    annotations = None
    if args.annotation_file:
        annotations = json.loads(Path(args.annotation_file).read_text(encoding="utf-8"))
        examples = fetch_examples_by_ids([int(news_id) for news_id in annotations])
    else:
        examples = fetch_examples(args.candidate_limit, args.count)
    if args.export_only:
        write_jsonl(args.train_output, examples)
        print(f"candidates={len(examples)}")
        return

    if args.annotation_file:
        generated = []
        for example in examples:
            summary = clean_summary(annotations.get(str(example["news_id"]), ""))
            if not is_valid_summary(summary):
                raise RuntimeError(f"Invalid or missing annotation for news_id={example['news_id']}: {summary}")
            generated.append({**example, "summary": summary})
    else:
        generated = generate_summaries(examples, args.teacher_model, args.batch_size)

    if len(generated) < args.count:
        raise RuntimeError(f"Only {len(generated)} of {args.count} examples passed validation.")

    train_examples, eval_examples = split_examples(generated, args.eval_count)
    write_jsonl(args.train_output, train_examples)
    write_jsonl(args.eval_output, eval_examples)
    print(f"train={len(train_examples)} eval={len(eval_examples)}")


if __name__ == "__main__":
    main()
