import logging
import os
import json
import re
import time

from .history import get_session_history

logger = logging.getLogger(__name__)

# 최적화: 원격 DB RTT 지연 최소화를 위한 인메모리 캐시 선언
_GLOSSARY_CACHE = {}
_INDICATORS_CACHE = {"data": None, "timestamp": 0}
_NEWS_CACHE = {"data": None, "timestamp": 0}

GLOSSARY_CACHE_TTL = 1800  # 30분
INDICATORS_CACHE_TTL = 600  # 10분
NEWS_CACHE_TTL = 300  # 5분



SYSTEM_POLICY = (
    "너는 채권 전문 Q&A 챗봇이다. 채권의 개념, 수익률, 듀레이션, 신용등급, "
    "만기, 위험 요소를 쉬운 한국어로 설명한다. 투자 권유처럼 단정하지 말고 "
    "정보 제공 관점으로 답한다.\n\n"
    "답변은 반드시 아래의 JSON 형식으로 작성해야 한다:\n"
    "{\n"
    "  \"answer\": \"여기에 질문에 대한 상세한 답변을 작성하십시오. Markdown 문법을 사용할 수 있습니다. 절대로 이 JSON 구조 바깥에 다른 설명이나 텍스트를 붙여서는 안 됩니다.\",\n"
    "  \"navigation_recommendations\": [\n"
    "    {\n"
    "      \"label\": \"이동 버튼 라벨 (예: '채권 상세정보 보기', '시장지표 페이지로 이동')\",\n"
    "      \"type\": \"navigate\",\n"
    "      \"page\": \"이동할 페이지 이름 ('detail', 'market', 'compare', 'indicators', 'dictionary', 'guide', 'news' 중 하나)\",\n"
    "      \"payload\": { ... 필요한 경우 파라미터 전달 ... }\n"
    "    }\n"
    "  ],\n"
    "  \"recommended_questions\": [\n"
    "    \"사용자가 다음에 할 만한 첫 번째 예상 질문\",\n"
    "    \"사용자가 다음에 할 만한 두 번째 예상 질문\"\n"
    "  ]\n"
    "}\n\n"
    "규칙:\n"
    "1. 사용자가 특정 페이지의 기능이나 용어를 탐색하고 싶어할 때만 navigation_recommendations에 이동 링크를 제공하시오. 필요하지 않다면 빈 배열([])이어야 한다.\n"
    "2. recommended_questions는 항상 2~3개의 구체적이고 채권 지식 탐색에 도움이 되는 다음 예상 질문들을 포함해야 한다.\n"
    "3. 출력 결과는 다른 부연 설명 없이 오직 위의 JSON 형식 문자열 하나만 반환해야 한다."
)

TOPIC_GUIDELINES = {
    "Concept": "사용자가 채권 개념을 질문했습니다. 채권 초보자도 이해할 수 있도록 예시를 들어 쉽고 친절하게 용어를 설명해 주세요.",
    "Indicators": "사용자가 거시경제나 시장지표에 대해 질문했습니다. 금리와 채권 가격의 상관관계, 스프레드 동향 등을 바탕으로 거시적 관점에서 답변해 주세요.",
    "Compare": "사용자가 채권 간 비교를 요청했습니다. 이율, 만기, 신용등급 등 리스크와 수익률 측면의 trade-off를 비교하여 합리적인 판단을 돕도록 설명해 주세요.",
    "Credit": "사용자가 신용평가나 위험도에 대해 질문했습니다. 신용등급의 의미와 기업 부도 위험성 등을 객관적인 평가지표 관점에서 차분하게 설명해 주세요.",
    "Disclosure": "사용자가 공시나 채권 옵션(콜/풋옵션 등)에 대해 질문했습니다. 발행 개요와 옵션의 조건을 세부적으로 설명해 주세요.",
    "Search": "사용자가 종목 추천이나 검색을 원합니다. 특정 종목을 매수 권유하지 말고, 어떤 기준으로 필터링하여 검색하면 좋은지 가이드를 제공해 주세요.",
    "General": "채권 전문 상담사로서 사용자의 질문에 친절하고 상세하게 답변해 주세요."
}


def answer_chat(session_id, question, current_page=None, page_params=None):
    history = get_session_history(session_id)

    result = _generate_answer(history, question, current_page, page_params)
    
    history.add_user_message(question)
    history.add_ai_message(result["answer"])

    return result


def _classify_topic(question):
    normalized = question.lower()
    if any(k in normalized for k in ["개념", "사전", "뜻", "의미", "듀레이션", "만기수익률", "ytm", "표면금리", "신용스프레드"]):
        return "Concept"
    if any(k in normalized for k in ["지표", "시장", "금리", "국채", "기준금리", "거시"]):
        return "Indicators"
    if any(k in normalized for k in ["비교", "차이", "어떤게", "더 이득"]):
        return "Compare"
    if any(k in normalized for k in ["신용", "등급", "평가", "부도", "위험"]):
        return "Credit"
    if any(k in normalized for k in ["공시", "콜옵션", "풋옵션", "call", "put", "dart", "발행"]):
        return "Disclosure"
    if any(k in normalized for k in ["추천", "종목", "검색", "찾아"]):
        return "Search"
    return "General"


def _parse_llm_json(response_content):
    fallback_result = {
        "answer": response_content,
        "navigation_recommendations": [],
        "recommended_questions": []
    }
    
    if not response_content:
        return fallback_result

    content = response_content.strip()
    
    # 1. Try to find a JSON block wrapped in ```json ... ```
    match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                return {
                    "answer": str(data.get("answer") or "").strip(),
                    "navigation_recommendations": data.get("navigation_recommendations") or [],
                    "recommended_questions": data.get("recommended_questions") or []
                }
        except Exception:
            pass

    # 2. Try to find any {...} JSON block in the text
    match = re.search(r"(\{.*\})", content, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                return {
                    "answer": str(data.get("answer") or "").strip(),
                    "navigation_recommendations": data.get("navigation_recommendations") or [],
                    "recommended_questions": data.get("recommended_questions") or []
                }
        except Exception:
            pass

    # 3. If parsing completely fails, clean up the response to remove any JSON-like blocks so the user doesn't see them
    clean_answer = re.sub(r"```json.*?```", "", response_content, flags=re.DOTALL)
    clean_answer = re.sub(r"\{.*?\}", "", clean_answer, flags=re.DOTALL).strip()
    if not clean_answer:
        clean_answer = response_content
        
    return {
        "answer": clean_answer,
        "navigation_recommendations": [],
        "recommended_questions": [
            "듀레이션과 만기의 차이점은 무엇인가요?",
            "듀레이션이 길면 어떤 장단점이 있나요?",
            "수정 듀레이션은 무엇인가요?"
        ]
    }


def _get_glossary_context(question):
    global _GLOSSARY_CACHE
    now = time.time()
    
    # 30분 캐시 체크 및 갱신
    cache_entry = _GLOSSARY_CACHE.get("all_terms")
    if cache_entry and (now - cache_entry["timestamp"] < GLOSSARY_CACHE_TTL):
        all_terms = cache_entry["data"]
    else:
        try:
            from apps.glossary.models import Glossary
            all_terms = list(Glossary.objects.filter(deleted_at__isnull=True).values("term_name", "description", "example_text"))
            _GLOSSARY_CACHE["all_terms"] = {"data": all_terms, "timestamp": now}
        except Exception:
            return ""

    # 메모리 내 키워드 매칭 (DB 지연 없음)
    matching_terms = []
    for term in all_terms:
        term_name = term["term_name"]
        if term_name.lower() in question.lower() or any(kw in question for kw in term_name.split()):
            matching_terms.append(term)
        
    if matching_terms:
        context = "\n\n[서비스 내 등록된 용어 사전 정보]"
        for term in matching_terms[:3]:
            context += f"\n- 용어명: {term['term_name']}\n  설명: {term['description']}"
            if term['example_text']:
                context += f"\n  예시: {term['example_text']}"
        return context
    return ""


def _get_indicators_context():
    global _INDICATORS_CACHE
    now = time.time()
    
    # 10분 캐시 체크
    if _INDICATORS_CACHE["data"] and (now - _INDICATORS_CACHE["timestamp"] < INDICATORS_CACHE_TTL):
        return _INDICATORS_CACHE["data"]
        
    try:
        from apps.indicators.models import BaseRate
        rates = BaseRate.objects.select_related("country").order_by("-created_at")[:3]
        if rates.exists():
            context = "\n\n[서비스 내 등록된 최신 국가별 시장금리 지표]"
            for rate in rates:
                context += (
                    f"\n- 국가: {rate.country.country_name}"
                    f"\n  기준금리: {rate.base_interest_rate}%"
                    f"\n  3년물 국채금리: {rate.three_year_yield}%"
                    f"\n  10년물 국채금리: {rate.ten_year_yield}%"
                    f"\n  스프레드(10년 - 3년): {rate.yield_curve_spread}%"
                )
            _INDICATORS_CACHE["data"] = context
            _INDICATORS_CACHE["timestamp"] = now
            return context
    except Exception:
        pass
    return ""


def _get_news_context():
    global _NEWS_CACHE
    now = time.time()
    
    # 5분 캐시 체크
    if _NEWS_CACHE["data"] and (now - _NEWS_CACHE["timestamp"] < NEWS_CACHE_TTL):
        return _NEWS_CACHE["data"]
        
    try:
        from apps.news.models import News
        articles = News.objects.filter(deleted_at__isnull=True).order_by("-published_at")[:3]
        if articles.exists():
            context = "\n\n[서비스 내 등록된 최신 채권 뉴스]"
            for art in articles:
                context += (
                    f"\n- 뉴스 제목: {art.title}"
                    f"\n  요약: {art.summary}"
                    f"\n  게시일: {art.published_at}"
                )
            _NEWS_CACHE["data"] = context
            _NEWS_CACHE["timestamp"] = now
            return context
    except Exception:
        pass
    return ""


def _generate_answer(history, question, current_page=None, page_params=None):
    topic = _classify_topic(question)
    
    llm_answer = _try_gemini_answer(history, question, current_page, page_params, topic) or \
                 _try_openai_answer(history, question, current_page, page_params, topic)
                 
    if llm_answer:
        return _parse_llm_json(llm_answer)

    # Fallback to local rules
    fallback_text = _fallback_answer(question)
    return {
        "answer": fallback_text,
        "navigation_recommendations": [],
        "recommended_questions": [
            "듀레이션이 무엇인가요?",
            "만기수익률(YTM)은 무엇인가요?",
            "신용등급은 어떻게 결정되나요?"
        ]
    }


def _build_langchain_messages(history, question, current_page=None, page_params=None, topic="General"):
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    # Core Policy and Specialization Guidelines
    system_content = SYSTEM_POLICY + "\n\n[주제별 가이드라인]\n" + TOPIC_GUIDELINES.get(topic, TOPIC_GUIDELINES["General"])

    # Base Database RAG Context Retrieval
    db_context = ""
    
    # 1. Glossary database lookup if related to Concept / dictionary
    if topic == "Concept" or current_page == "dictionary":
        db_context += _get_glossary_context(question)
        
    # 2. Indicators database lookup if related to Indicators / indicators page
    if topic == "Indicators" or current_page == "indicators":
        db_context += _get_indicators_context()
        
    # 3. News database lookup if news page
    if current_page == "news":
        db_context += _get_news_context()

    # 4. Specific Bond details if user is on the bond detail page
    if current_page == 'detail' and page_params and 'bondId' in page_params:
        bond_id = page_params['bondId']
        try:
            from apps.bonds.selectors import get_bond
            bond = get_bond(bond_id)
            if bond:
                db_context += (
                    f"\n\n[상세 조회 중인 채권 실제 정보 (DB 조회결과)]"
                    f"\n- 채권 ID: {bond.id}"
                    f"\n- 채권명: {bond.bond_name}"
                    f"\n- 발행사: {bond.issuer.issuer_name}"
                    f"\n- 표면이율: {bond.coupon_rate}%"
                    f"\n- 만기일: {bond.maturity_date}"
                    f"\n- 신용등급: {bond.rating.rating_name}"
                    f"\n- 이자지급유형: {bond.interest_type}"
                    f"\n- 옵션 여부: {bond.option_type}"
                )
        except Exception as e:
            # Inject exception detail for internal debugging (invisible to user)
            pass

    if db_context:
        system_content += "\n\n[실시간 DB 정보 컨텍스트]\n" + db_context

    # Page Context Injection
    if current_page:
        system_content += f"\n\n[현재 화면 맥락]\n사용자는 현재 '{current_page}' 페이지를 확인 중입니다."
        if page_params:
            system_content += f"\n페이지 파라미터: {page_params}"

    messages = [SystemMessage(content=system_content)]
    
    # Add conversation history (최적화: 이력 범위를 최근 4개로 제한하여 컨텍스트 사이즈 축소)
    for message in history.messages[-4:]:
        if message.type in ("human", "user"):
            messages.append(HumanMessage(content=message.content))
        elif message.type in ("ai", "assistant"):
            messages.append(AIMessage(content=message.content))
            
    messages.append(HumanMessage(content=question))
    return messages


def _try_gemini_answer(history, question, current_page=None, page_params=None, topic="General"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        return None

    model = os.environ.get("GEMINI_CHAT_MODEL", "gemini-3.6-flash")
    try:
        # 과거에는 키 접두사에 따라 SSAFY 내부 프록시로 우회했으나, 외부에서
        # 접근 불가한 주소라 요청이 무한 대기하는 문제가 있어 제거했다.
        # 잘못된 키는 timeout/에러로 빠르게 실패하고 규칙 기반 폴백이 동작한다.
        kwargs = {
            "model": model,
            "temperature": 0.2,
            "google_api_key": api_key,
            "max_retries": 0,
            "timeout": 30,
            "response_mime_type": "application/json",
        }
        llm = ChatGoogleGenerativeAI(**kwargs)
        response = llm.invoke(_build_langchain_messages(history, question, current_page, page_params, topic))
        return _content_to_text(response.content)
    except Exception as exc:
        logger.warning("Gemini answer failed: %s: %s", type(exc).__name__, exc)
        return None


def _try_gemini_stream(history, question, current_page=None, page_params=None, topic="General"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        return None

    model = os.environ.get("GEMINI_CHAT_MODEL", "gemini-3.6-flash")
    try:
        # 과거에는 키 접두사에 따라 SSAFY 내부 프록시로 우회했으나, 외부에서
        # 접근 불가한 주소라 요청이 무한 대기하는 문제가 있어 제거했다.
        # 잘못된 키는 timeout/에러로 빠르게 실패하고 규칙 기반 폴백이 동작한다.
        kwargs = {
            "model": model,
            "temperature": 0.2,
            "google_api_key": api_key,
            "max_retries": 0,
            "timeout": 30,
            "response_mime_type": "application/json",
        }
        llm = ChatGoogleGenerativeAI(**kwargs)
        return llm.stream(_build_langchain_messages(history, question, current_page, page_params, topic))
    except Exception as exc:
        logger.warning("Gemini stream setup failed: %s: %s", type(exc).__name__, exc)
        return None


def _try_openai_answer(history, question, current_page=None, page_params=None, topic="General"):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        return None

    llm = ChatOpenAI(
        model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        temperature=0.2,
        api_key=api_key,
        max_retries=0,
        response_format={"type": "json_object"}
    )
    response = llm.invoke(_build_langchain_messages(history, question, current_page, page_params, topic))
    return response.content


def _try_openai_stream(history, question, current_page=None, page_params=None, topic="General"):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        return None

    llm = ChatOpenAI(
        model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        temperature=0.2,
        api_key=api_key,
        max_retries=0,
        response_format={"type": "json_object"}
    )
    return llm.stream(_build_langchain_messages(history, question, current_page, page_params, topic))


def _content_to_text(content):
    """LLM 응답 content를 순수 텍스트로 정규화한다.
    (신형 Gemini 모델은 문자열 대신 [{'type': 'text', 'text': ...}] 블록 리스트를 반환)
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(str(part.get("text", "")))
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(content or "")


def _next_with_deadline(iterator, seconds=12):
    """이터레이터의 다음 값을 데드라인 안에 가져온다. 초과/실패 시 None."""
    import concurrent.futures

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(lambda: next(iterator, None))
    try:
        return future.result(timeout=seconds)
    except Exception as exc:
        logger.warning("Gemini first token failed/deadline: %s: %s", type(exc).__name__, exc)
        return None
    finally:
        executor.shutdown(wait=False)


def answer_chat_stream(session_id, question, current_page=None, page_params=None):
    history = get_session_history(session_id)
    topic = _classify_topic(question)

    stream = _try_gemini_stream(history, question, current_page, page_params, topic) or \
             _try_openai_stream(history, question, current_page, page_params, topic)

    accumulated = []
    stream_failed = False
    if stream:
        # llm.stream()은 지연 평가라 실제 API 오류/지연이 반복(iteration) 시점에 발생한다.
        # 라이브러리 timeout이 전송 계층에 따라 무시될 수 있으므로,
        # 첫 토큰을 스레드 데드라인(12초)으로 기다리고 넘기면 즉시 폴백한다.
        first_chunk = _next_with_deadline(stream, seconds=12)
        if first_chunk is None:
            stream_failed = True
        else:
            try:
                first_text = _content_to_text(first_chunk.content)
                accumulated.append(first_text)
                yield first_text
                for chunk in stream:
                    content = _content_to_text(chunk.content)
                    accumulated.append(content)
                    yield content
            except Exception:
                pass  # 이미 일부를 보냈다면 그대로 종료

        if accumulated:
            # 스트리밍 완료 후 대화 이력 누적 저장
            full_response = "".join(accumulated)
            parsed = _parse_llm_json(full_response)
            history.add_user_message(question)
            history.add_ai_message(parsed["answer"])
    if not stream or stream_failed:
        # 로컬 폴백 생성기
        fallback_text = _fallback_answer(question)
        fallback_json = json.dumps({
            "answer": fallback_text,
            "navigation_recommendations": [],
            "recommended_questions": [
                "듀레이션이 무엇인가요?",
                "만기수익률(YTM)은 무엇인가요?",
                "신용등급은 어떻게 결정되나요?"
            ]
        }, ensure_ascii=False)
        yield fallback_json
        
        history.add_user_message(question)
        history.add_ai_message(fallback_text)


def _fallback_answer(question):
    normalized = question.strip()
    lower_question = normalized.lower()

    if "듀레이션" in normalized:
        return (
            "듀레이션은 금리 변화에 채권 가격이 얼마나 민감하게 움직이는지 보여주는 지표입니다. "
            "일반적으로 듀레이션이 길수록 금리가 오를 때 가격 하락 폭이 커질 수 있습니다. "
            "다만 실제 위험은 만기, 쿠폰, 신용등급, 시장금리 상황을 함께 봐야 합니다."
        )

    if "ytm" in lower_question or "만기수익률" in normalized:
        return (
            "YTM, 즉 만기수익률은 채권을 현재 가격에 사서 만기까지 보유한다고 가정했을 때의 "
            "연 환산 기대수익률입니다. 쿠폰 이자, 현재 매입 가격, 만기 상환금이 함께 반영됩니다."
        )

    if "신용" in normalized or "등급" in normalized:
        return (
            "신용등급은 발행자가 원리금을 갚을 능력을 평가한 지표입니다. "
            "등급이 낮을수록 일반적으로 더 높은 수익률을 요구받지만, 부도나 가격 변동 위험도 커질 수 있습니다."
        )

    if "금리" in normalized:
        return (
            "채권 가격은 보통 시장금리와 반대로 움직입니다. 시장금리가 오르면 기존 채권의 매력도가 낮아져 "
            "가격이 하락할 수 있고, 시장금리가 내리면 기존 채권 가격은 상승할 수 있습니다."
        )

    return (
        "죄송합니다. 요청하신 질문에 대한 답변을 찾지 못했습니다. "
        "채권의 개념, 수익률, 듀레이션, 신용등급 등에 대해 다시 질문해 주시면 성실히 설명해 드리겠습니다."
    )
