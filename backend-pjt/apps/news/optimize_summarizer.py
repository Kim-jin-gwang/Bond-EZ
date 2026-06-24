from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parents[1]
if str(CURRENT_DIR) in sys.path:
    sys.path.remove(str(CURRENT_DIR))
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from apps.news.summarizer import configure_dspy, import_dspy, news_summary_metric


DEFAULT_DATASET = CURRENT_DIR / "summary_examples.jsonl"
DEFAULT_OUTPUT = CURRENT_DIR / "news_summarizer_optimized.json"


def build_program(dspy):
    class SummarizeNews(dspy.Signature):
        """Summarize a Korean financial news article in one or two complete sentences.

        Preserve the main subject and action. Avoid malformed endings such as
        '시총다.', '전환다.', '하락다.', or other noun fragments plus '다.'.
        """

        title: str = dspy.InputField(desc="News article title")
        content: str = dspy.InputField(desc="Cleaned article body")
        summary: str = dspy.OutputField(desc="One or two complete Korean declarative sentences within 200 characters.")

    class NewsSummarizer(dspy.Module):
        def __init__(self):
            super().__init__()
            self.summarize = dspy.Predict(SummarizeNews)

        def forward(self, title, content):
            return self.summarize(title=title, content=content)

    return NewsSummarizer()


def load_examples(dspy, dataset_path):
    examples = []
    with Path(dataset_path).open(encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            row = json.loads(line)
            examples.append(
                dspy.Example(
                    news_id=row.get("news_id"),
                    title=row["title"],
                    content=row["content"],
                    summary=row.get("summary", ""),
                ).with_inputs("title", "content")
            )
    return examples


def optimize(dataset_path=DEFAULT_DATASET, output_path=DEFAULT_OUTPUT, optimizer_name="bootstrap"):
    dspy = import_dspy()
    configure_dspy(dspy)

    examples = load_examples(dspy, dataset_path)
    if len(examples) < 2:
        raise ValueError("Optimizer needs at least 2 examples. Add more rows to summary_examples.jsonl.")

    trainset = examples
    program = build_program(dspy)

    if optimizer_name == "mipro":
        optimizer = dspy.MIPROv2(metric=news_summary_metric, auto="light")
        optimized = optimizer.compile(program, trainset=trainset)
    else:
        optimizer = dspy.BootstrapFewShot(metric=news_summary_metric, max_bootstrapped_demos=4, max_labeled_demos=4)
        optimized = optimizer.compile(program, trainset=trainset)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    optimized.save(str(output_path))
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Optimize the DSPy news summarizer.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--optimizer", choices=["bootstrap", "mipro"], default="bootstrap")
    args = parser.parse_args()

    output = optimize(args.dataset, args.output, args.optimizer)
    print(f"Saved optimized summarizer to {output}")
    print(f"Set NEWS_SUMMARY_DSPY_PROGRAM_PATH={output}")


if __name__ == "__main__":
    import django
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    main()
