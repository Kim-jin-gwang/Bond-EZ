from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parents[1]
if str(CURRENT_DIR) in sys.path:
    sys.path.remove(str(CURRENT_DIR))
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from apps.news.optimize_summarizer import build_program, load_examples
from apps.news.summarizer import configure_dspy, extract_summary, import_dspy, news_summary_metric


DEFAULT_DATASET = CURRENT_DIR / "summary_eval_examples.jsonl"
DEFAULT_PROGRAM = CURRENT_DIR / "news_summarizer_optimized.json"


def evaluate(program, examples):
    rows = []
    for example in examples:
        prediction = program(title=example.title, content=example.content)
        rows.append(
            {
                "news_id": getattr(example, "news_id", None),
                "score": news_summary_metric(example, prediction),
                "summary": extract_summary(prediction),
            }
        )
    average = sum(row["score"] for row in rows) / len(rows) if rows else 0.0
    return average, rows


def main():
    parser = argparse.ArgumentParser(description="Compare baseline and optimized DSPy news summarizers.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--program", default=str(DEFAULT_PROGRAM))
    args = parser.parse_args()

    dspy = import_dspy()
    configure_dspy(dspy)
    examples = load_examples(dspy, args.dataset)

    baseline = build_program(dspy)
    optimized = build_program(dspy)
    optimized.load(args.program)

    baseline_score, baseline_rows = evaluate(baseline, examples)
    optimized_score, optimized_rows = evaluate(optimized, examples)
    print(json.dumps({"baseline": baseline_score, "optimized": optimized_score}, ensure_ascii=False))
    for baseline_row, optimized_row in zip(baseline_rows, optimized_rows):
        print(
            json.dumps(
                {
                    "news_id": baseline_row["news_id"],
                    "baseline_score": baseline_row["score"],
                    "optimized_score": optimized_row["score"],
                    "baseline": baseline_row["summary"],
                    "optimized": optimized_row["summary"],
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
