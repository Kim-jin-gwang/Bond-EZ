import re
from functools import lru_cache

from django.conf import settings


SUMMARY_MAX_CHARS = 200
CONTENT_MAX_CHARS = 12000
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

    try:
        summary = clean_summary(
            generate_llm_summary(cleaned_title, cleaned_content[:CONTENT_MAX_CHARS])
        )
    except NewsSummarizerError:
        raise
    except Exception as exc:
        raise NewsSummarizerError("뉴스 요약 모델 호출에 실패했습니다.") from exc

    if not is_valid_summary(summary):
        summary = coerce_valid_summary(summary)
    if not is_valid_summary(summary):
        summary = build_extractive_summary(cleaned_title, cleaned_content)
    if not is_valid_summary(summary):
        raise NewsSummarizerError("요약 결과 형식이 올바르지 않습니다.")
    return summary


# NOTE: 기존에는 dspy로 요약 프로그램을 구성했으나, dspy가 매우 무거워
# (litellm/optuna/pandas 연쇄 의존) 무료 호스팅 메모리에 부적합하여
# 이미 챗봇에 사용 중인 langchain-google-genai 직접 호출로 교체했다.
# 요약 검증/교정/추출 폴백 로직은 그대로 유지된다.
@lru_cache(maxsize=1)
def get_summary_llm():
    api_key = clean_secret(getattr(settings, "GEMINI_API_KEY", ""))
    if not api_key:
        raise NewsSummaryConfigError("GEMINI_API_KEY를 설정해 주세요.")
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:
        raise NewsSummaryConfigError("langchain-google-genai 패키지가 설치되어 있지 않습니다.") from exc

    model = getattr(settings, "NEWS_SUMMARY_LM_MODEL", "gemini-2.5-flash")
    model = model.split("/")[-1]  # 과거 'gemini/...' litellm 표기 호환
    if not api_key.startswith("AIzaSy"):
        raise NewsSummaryConfigError("정식 Google AI Studio 키(AIzaSy...)가 필요합니다.")
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=getattr(settings, "NEWS_SUMMARY_LM_TEMPERATURE", 0.2),
        max_output_tokens=getattr(settings, "NEWS_SUMMARY_LM_MAX_TOKENS", 2048),
        timeout=30,
        max_retries=1,
    )


def generate_llm_summary(title, content):
    llm = get_summary_llm()
    prompt = (
        "다음 금융 뉴스 본문을 한국어 1~2문장으로 요약하세요.\n"
        f"- {SUMMARY_MAX_CHARS}자 이내\n"
        "- 기관명, 금리, 시장, 날짜, 금액, 정책 방향 같은 구체적 사실을 보존\n"
        "- 광고, 기자명, 저작권 문구, 관련 링크는 제외\n"
        "- 반드시 '~다.'로 끝나는 완결된 평서문으로 작성\n\n"
        f"제목: {title}\n"
        f"본문: {content}\n\n"
        "요약:"
    )
    response = llm.invoke(prompt)
    summary = getattr(response, "content", "") or ""
    if isinstance(summary, list):  # 멀티파트 응답 방어
        summary = " ".join(str(part) for part in summary)
    return summary


def clean_secret(value):
    return str(value or "").strip().strip('"').strip("'")


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


def clean_summary(summary):
    summary = normalize_text(summary)
    summary = re.sub(r"^요약[:：]\s*", "", summary).strip()
    summary = summary.replace('"', "").replace("'", "").strip()

    sentence_endings = list(re.finditer(r"(?:다|니다|했다|였다|한다|전망이다|분석이다)\.", summary))
    if sentence_endings:
        summary = summary[: sentence_endings[min(1, len(sentence_endings) - 1)].end()].strip()

    if summary and summary.endswith("다") and not summary.endswith("다."):
        summary = f"{summary}."

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
    if is_malformed_summary(summary):
        return ""
    if summary and summary.endswith("다") and not summary.endswith("다."):
        summary = f"{summary}."
    if len(summary) > SUMMARY_MAX_CHARS:
        summary = trim_summary(summary)
    return summary if is_valid_summary(summary) else ""


def is_malformed_summary(summary):
    if not summary:
        return True
    if has_broken_ending(summary):
        return True
    if len(summary) < 20:
        return True
    return False


def has_broken_ending(summary):
    summary = normalize_text(summary)
    if re.search(r"<\s*(앵커|기자)\s*>", summary):
        return True
    if re.search(r"^\s*\[[^\]]{1,80}:", summary):
        return True
    if "?" in summary:
        return True
    sentence_count = len(re.findall(r"(?:다|니다|했다|였다|한다|전망이다|분석이다)\.", summary))
    if sentence_count not in (1, 2):
        return True
    if re.search(r"(은|는|가|을|를|와|과|의|에|에서|로|으로)다\.$", summary):
        return True
    if re.search(r"(시총|전환|하락|상승|약세|강세|코스피|코스닥|환율|금리|총|환|락|승|세)다\.$", summary):
        return True
    if re.search(r"[0-9.%+-]+다\.$", summary):
        return True
    return False


def build_extractive_summary(title, content):
    text = normalize_text(content)
    candidates = []
    title_tokens = extract_korean_keywords(title)
    finance_terms = ("세금", "양도세", "과세", "금리", "채권", "주식", "시장", "투자자", "정책", "정부")
    for index, sentence in enumerate(split_sentences(text)):
        sentence = clean_summary(sentence)
        if "[" in sentence or "]" in sentence:
            continue
        if not sentence or is_malformed_summary(sentence):
            continue
        sentence_tokens = extract_korean_keywords(sentence)
        score = len(title_tokens.intersection(sentence_tokens)) * 3
        score += sum(term in sentence for term in finance_terms)
        score += max(0, 3 - index) * 0.1
        candidates.append((score, -index, sentence))

    if candidates:
        sentence = max(candidates)[2]
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
        and not has_broken_ending(summary)
    )


def summary_quality_score(summary, title="", content=""):
    summary = clean_summary(summary)
    if not is_valid_summary(summary):
        return 0.0

    score = 0.5
    if 30 <= len(summary) <= SUMMARY_MAX_CHARS:
        score += 0.2

    title_tokens = extract_korean_keywords(title)
    summary_tokens = extract_korean_keywords(summary)
    if title_tokens and title_tokens.intersection(summary_tokens):
        score += 0.2

    if any(term in summary for term in ("금리", "채권", "코스피", "코스닥", "환율", "증시", "주가", "시장")):
        score += 0.1

    return min(score, 1.0)


def extract_korean_keywords(text):
    tokens = re.findall(r"[가-힣A-Za-z0-9]{2,}", normalize_text(text))
    stopwords = {"기자", "뉴스", "본문", "관련", "이번", "이날", "지난", "대한", "통해"}
    return {token for token in tokens if token not in stopwords}


def news_summary_metric(example, prediction, trace=None):
    summary = extract_summary(prediction)
    title = getattr(example, "title", "")
    content = getattr(example, "content", "")
    gold_summary = getattr(example, "summary", "")

    score = summary_quality_score(summary, title=title, content=content)
    if gold_summary:
        gold_tokens = extract_korean_keywords(gold_summary)
        summary_tokens = extract_korean_keywords(summary)
        if gold_tokens and summary_tokens:
            overlap_count = len(gold_tokens.intersection(summary_tokens))
            precision = overlap_count / len(summary_tokens)
            recall = overlap_count / len(gold_tokens)
            content_f1 = 2 * precision * recall / max(precision + recall, 1e-9)
            score = score * 0.35 + content_f1 * 0.65
        else:
            score = 0.0

    return min(score, 1.0)
