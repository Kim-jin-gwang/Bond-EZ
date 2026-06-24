import os

from .history import get_session_history


SYSTEM_POLICY = (
    "너는 채권 전문 Q&A 챗봇이다. 채권의 개념, 수익률, 듀레이션, 신용등급, "
    "만기, 위험 요소를 쉬운 한국어로 설명한다. 투자 권유처럼 단정하지 말고 "
    "정보 제공 관점으로 답한다."
)


def answer_chat(session_id, question):
    history = get_session_history(session_id)

    answer, sources = _generate_answer(history, question)
    history.add_user_message(question)
    history.add_ai_message(answer)

    return {
        "answer": answer,
        "sources": sources,
    }


def _generate_answer(history, question):
    llm_answer = _try_gemini_answer(history, question) or _try_openai_answer(history, question)
    if llm_answer:
        return llm_answer, []

    return _fallback_answer(question), []


def _build_langchain_messages(history, question):
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    messages = [SystemMessage(content=SYSTEM_POLICY)]
    for message in history.messages[-8:]:
        if message.type in ("human", "user"):
            messages.append(HumanMessage(content=message.content))
        elif message.type in ("ai", "assistant"):
            messages.append(AIMessage(content=message.content))
    messages.append(HumanMessage(content=question))
    return messages


def _try_gemini_answer(history, question):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        return None

    configured_model = os.environ.get("GEMINI_CHAT_MODEL")
    model_candidates = [
        configured_model,
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]

    for model in dict.fromkeys(candidate for candidate in model_candidates if candidate):
        try:
            llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=0.2,
                google_api_key=api_key,
                max_retries=0,
            )
            response = llm.invoke(_build_langchain_messages(history, question))
            return response.content
        except Exception:
            continue

    return None


def _try_openai_answer(history, question):
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
    )
    response = llm.invoke(_build_langchain_messages(history, question))
    return response.content


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
        "현재는 LangChain MessageHistory가 붙은 개발용 챗봇 상태입니다. "
        "GOOGLE_API_KEY와 Gemini/LangChain 의존성을 설정하면 같은 세션의 이전 대화 맥락을 참고해 답변할 수 있습니다. "
        "RAG 문서 검색은 다음 단계에서 채권 문서 chunk와 pgvector 검색을 연결하면 됩니다."
    )
