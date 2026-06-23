import re
from functools import lru_cache

from django.conf import settings


SUMMARY_MAX_CHARS = 120
CONTENT_MAX_CHARS = 4000
KOREAN_DECLARATIVE_ENDINGS = (
    "다.",
    "니다.",
    "했다.",
    "였다.",
    "한다.",
    "전망이다.",
    "분석이다.",
)


class NewsSummarizerError(Exception):
    default_code = "NEWS_SUMMARY_FAILED"
    default_message = "뉴스 요약을 생성하지 못했습니다."

    def __init__(self, message=None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message


class NewsSummaryConfigError(NewsSummarizerError):
    default_code = "NEWS_SUMMARY_CONFIG_ERROR"
    default_message = "뉴스 요약 모델 설정이 없습니다."


class NewsSummaryInputError(NewsSummarizerError):
    default_code = "NEWS_SUMMARY_INPUT_ERROR"
    default_message = "요약할 뉴스 본문이 없습니다."


def summarize_news_content(title, content):
    cleaned_title = normalize_text(title)
    cleaned_content = normalize_text(content)
    if not cleaned_content:
        raise NewsSummaryInputError()

    prediction = get_summarizer()(title=cleaned_title, content=cleaned_content[:CONTENT_MAX_CHARS])
    summary = clean_summary(extract_summary(prediction))
    if not summary:
        summary = clean_summary(generate_direct_summary(cleaned_title, cleaned_content[:CONTENT_MAX_CHARS]))
    if summary and not is_valid_summary(summary):
        summary = coerce_valid_summary(summary)
    if is_malformed_summary(summary):
        summary = build_extractive_summary(cleaned_title, cleaned_content)
    if not summary:
        raise NewsSummarizerError("요약 결과 형식이 올바르지 않습니다.")
    return summary


@lru_cache(maxsize=1)
def get_summarizer():
    dspy = import_dspy()
    configure_dspy(dspy)

    class SummarizeNews(dspy.Signature):
        """Summarize a Korean financial news article in one concise sentence.

        Preserve concrete facts such as institutions, rates, markets, bonds,
        dates, amounts, and policy direction. Ignore ads, reporter bios,
        copyright notices, and related links.
        """

        title: str = dspy.InputField(desc="News article title")
        content: str = dspy.InputField(desc="Cleaned article body")
        summary: str = dspy.OutputField(
            desc=f"One Korean declarative sentence within {SUMMARY_MAX_CHARS} characters, ending with ~다."
        )

    class NewsSummarizer(dspy.Module):
        def __init__(self):
            super().__init__()
            self.summarize = dspy.Predict(SummarizeNews)

        def forward(self, title, content):
            return self.summarize(title=title, content=content)

    program = NewsSummarizer()
    program_path = getattr(settings, "NEWS_SUMMARY_DSPY_PROGRAM_PATH", "")
    if program_path:
        program.load(program_path)
    return program


def configure_dspy(dspy):
    dspy.configure(lm=build_lm(dspy))


def build_lm(dspy):
    model = getattr(settings, "NEWS_SUMMARY_LM_MODEL", "")
    api_key = get_lm_api_key(model)
    if not model or not api_key:
        raise NewsSummaryConfigError(
            "NEWS_SUMMARY_LM_MODEL과 해당 API 키(OPENAI_API_KEY 또는 GEMINI_API_KEY)를 설정해 주세요."
        )

    return dspy.LM(
        model,
        api_key=api_key,
        temperature=getattr(settings, "NEWS_SUMMARY_LM_TEMPERATURE", 0.2),
        max_tokens=getattr(settings, "NEWS_SUMMARY_LM_MAX_TOKENS", 512),
    )


def get_lm_api_key(model):
    if model.startswith("gemini/"):
        return getattr(settings, "GEMINI_API_KEY", "")
    if model.startswith("openai/"):
        return getattr(settings, "OPENAI_API_KEY", "")
    return getattr(settings, "NEWS_SUMMARY_LM_API_KEY", "")


def import_dspy():
    try:
        import dspy
    except ImportError as exc:
        raise NewsSummaryConfigError("dspy 패키지가 설치되어 있지 않습니다.") from exc
    return dspy


def normalize_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def extract_summary(prediction):
    summary = getattr(prediction, "summary", None)
    if summary:
        return summary
    if hasattr(prediction, "summary"):
        return ""

    if isinstance(prediction, dict):
        return prediction.get("summary", "")

    try:
        prediction_dict = prediction.toDict()
    except AttributeError:
        prediction_dict = {}

    if prediction_dict.get("summary"):
        return prediction_dict["summary"]

    fallback = str(prediction or "")
    if re.search(r"Prediction\s*\(", fallback):
        return ""
    return fallback


def generate_direct_summary(title, content):
    dspy = import_dspy()
    lm = build_lm(dspy)
    prompt = (
        "다음 금융 뉴스 본문을 한국어 한 문장으로 요약하세요.\n"
        f"- {SUMMARY_MAX_CHARS}자 이내\n"
        "- 광고, 기자명, 저작권 문구는 제외\n"
        "- 반드시 '~다.'로 끝내기\n\n"
        f"제목: {title}\n"
        f"본문: {content}\n\n"
        "요약:"
    )
    response = lm(prompt)
    if isinstance(response, (list, tuple)):
        return response[0] if response else ""
    return response


def clean_summary(summary):
    summary = normalize_text(summary)
    summary = re.sub(r"^요약[:：]\s*", "", summary).strip()
    summary = summary.replace('"', "").replace("'", "").strip()

    sentence_match = re.match(r"^(.+?(?:다|니다|했다|였다|한다|전망이다|분석이다)\.)", summary)
    if sentence_match:
        summary = sentence_match.group(1).strip()

    if summary and summary.endswith("다") and not summary.endswith("다."):
        summary = f"{summary}."
    elif summary and not summary.endswith(KOREAN_DECLARATIVE_ENDINGS):
        summary = f"{summary.rstrip('.。')}다."

    if len(summary) > SUMMARY_MAX_CHARS:
        summary = trim_summary(summary)

    return summary


def trim_summary(summary):
    truncated = summary[:SUMMARY_MAX_CHARS].rstrip(" ,，.。")
    last_space = truncated.rfind(" ")
    if last_space >= 40:
        truncated = truncated[:last_space].rstrip(" ,，.。")
    if truncated.endswith("다"):
        return f"{truncated}."
    return truncated[: SUMMARY_MAX_CHARS - 2].rstrip(" ,，.。") + "다."


def coerce_valid_summary(summary):
    summary = normalize_text(summary).replace("\n", " ")
    if len(summary) > SUMMARY_MAX_CHARS:
        summary = trim_summary(summary)
    if summary and not summary.endswith(KOREAN_DECLARATIVE_ENDINGS):
        summary = f"{summary.rstrip('.。')}다."
    if len(summary) > SUMMARY_MAX_CHARS:
        summary = trim_summary(summary)
    return summary


def is_malformed_summary(summary):
    if not summary:
        return True
    if re.search(r"(은|는|이|가|을|를|와|과|의|에|에서|로|으로)다\.$", summary):
        return True
    if re.search(r"[0-9.%+-]+다\.$", summary):
        return True
    if len(summary) < 20:
        return True
    return False


def build_extractive_summary(title, content):
    text = normalize_text(content)
    for sentence in split_sentences(text):
        sentence = clean_summary(sentence)
        if sentence and not is_malformed_summary(sentence):
            return sentence if len(sentence) <= SUMMARY_MAX_CHARS else trim_summary(sentence)

    fallback = clean_summary(title)
    if fallback and not is_malformed_summary(fallback):
        return fallback if len(fallback) <= SUMMARY_MAX_CHARS else trim_summary(fallback)
    return ""


def split_sentences(text):
    matches = re.finditer(r".+?(?:다\.|니다\.|했다\.|였다\.|한다\.|전망이다\.|분석이다\.|[!?。])", text)
    sentences = [match.group(0).strip() for match in matches]
    if sentences:
        return sentences
    return [text]


def is_valid_summary(summary):
    return (
        bool(summary)
        and len(summary) <= SUMMARY_MAX_CHARS
        and "\n" not in summary
        and summary.endswith(KOREAN_DECLARATIVE_ENDINGS)
    )
