from datetime import date


def is_master_bond(bond):
    return hasattr(bond, "company_name") and hasattr(bond, "call_put_option")


def get_josa(word, josa_type="이/가"):
    """
    단어의 마지막 글자 받침 여부에 따라 알맞은 조사(이/가, 은/는)를 반환합니다.
    """
    if not word:
        return ""
    last_char = str(word)[-1]
    # 한글 유니코드 범위 확인
    if 0xAC00 <= ord(last_char) <= 0xD7A3:
        # 받침이 있으면 (char_code - 0xAC00) % 28 이 0보다 큼
        if (ord(last_char) - 0xAC00) % 28 > 0:
            return "이" if josa_type == "이/가" else "은"
        else:
            return "가" if josa_type == "이/가" else "는"
    # 영문/숫자 등 기본 폴백
    return "가" if josa_type == "이/가" else "는"


def generate_rule_based_summary(bond):
    """
    채권의 주요 속성(금리 수준, 신용등급, 선후순위, 보증 상태, 옵션 정보)을 분석하여
    3문장으로 구성된 한글 핵심 요약 배열을 생성하여 반환합니다.
    """
    if is_master_bond(bond):
        issuer_name = bond.company_name or "발행회사"
        bond_type = bond.bond_type or "채권"
        coupon_rate = float(bond.coupon_rate) if bond.coupon_rate is not None else None
        seniority_name = bond.seniority or "선순위"
        guarantee_status = bond.guarantee_status or "무보증"
        rating_name = bond.credit_rating or "등급없음"
        maturity_date = bond.maturity_date
        option_type = bond.call_put_option or "NONE"
        exercise_date = None
    else:
        issuer_name = bond.issuer.issuer_name if bond.issuer else "발행회사"
        bond_type = bond.bond_type.bond_type if bond.bond_type else "채권"
        coupon_rate = float(bond.coupon_rate) if bond.coupon_rate is not None else None
        seniority_name = bond.seniority.seniority_name if bond.seniority else "선순위"
        guarantee_status = bond.guarantee_status.guarantee_status if bond.guarantee_status else "무보증"
        rating_name = bond.rating.rating_name if bond.rating else "등급없음"
        maturity_date = bond.maturity_date
        
        option_type = "NONE"
        exercise_date = None
        if bond.option_exercise:
            option_type = bond.option_exercise.option_type
            exercise_date = bond.option_exercise.exercise_start_date_1

    summary = []

    # 1. 첫 번째 문장: 발행사, 종류, 표면이율
    if coupon_rate is not None:
        rate_str = f"표면이율은 연 **{coupon_rate:.2f}%**입니다."
    else:
        rate_str = "표면이율 정보가 제공되지 않았습니다."

    josa = get_josa(issuer_name, "이/가")
    summary.append(f"{issuer_name}{josa} 발행한 {bond_type}로, {rate_str}")

    # 2. 두 번째 문장: 변제순위(선/후순위) 및 신용등급에 따른 리스크 판단
    # 선/후순위 텍스트 결정
    if "선순위" in seniority_name:
        seniority_desc = "선순위 채권으로 후순위 채권보다 상환 순위가 앞섭니다"
    elif "후순위" in seniority_name:
        seniority_desc = "후순위 채권으로 일반 선순위 채권보다 상환 순위가 뒤에 있습니다"
    else:
        seniority_desc = f"상환 순위는 {seniority_name}입니다"

    # 신용등급 그룹 분기
    rating_group = rating_name.rstrip("+-0123456789") or rating_name
    if rating_name in ("", "등급없음", "미평가", "NR"):
        rating_desc = "신용등급 정보가 없어 등급에 따른 신용위험을 판단하기 어렵습니다."
    elif rating_name == "국채" or "국채" in rating_name or rating_group in ("AAA", "AA"):
        rating_desc = f"신용등급은 {rating_name}로 우량 등급 범위에 해당합니다. 다만 신용등급이 원금 상환을 보장하지는 않습니다."
    elif rating_group == "A":
        rating_desc = f"신용등급은 {rating_name}로 투자적격 등급 범위에 해당하며, 발행사의 신용 상태를 함께 확인해야 합니다."
    elif rating_group == "BBB":
        rating_desc = f"신용등급은 {rating_name}로 투자적격 등급 범위이지만, 경기와 재무 상태 변화에 따른 신용위험을 확인해야 합니다."
    else:
        rating_desc = f"신용등급은 {rating_name}로 투기등급 범위에 해당해 원금 손실 위험을 주의 깊게 확인해야 합니다."

    # 보증 여부 텍스트 결정
    if guarantee_status and "보증" in guarantee_status and "무보증" not in guarantee_status:
        guarantee_desc = f"{guarantee_status} 조건이며"
    else:
        guarantee_desc = "무보증 조건이며"

    summary.append(f"{guarantee_desc}, {seniority_desc}. {rating_desc}")

    # 3. 세 번째 문장: 만기 및 조기상환 옵션 정보
    maturity_value = None
    if isinstance(maturity_date, date):
        maturity_str = maturity_date.strftime("%Y-%m-%d")
        maturity_value = maturity_date
    else:
        maturity_str = str(maturity_date or "")
        try:
            maturity_value = date.fromisoformat(maturity_str[:10])
        except ValueError:
            pass

    option_type = (option_type or "").upper()
    has_call = "CALL" in option_type
    has_put = "PUT" in option_type
    exercise_str = f"(행사 시작일: {exercise_date})" if exercise_date else ""

    if maturity_value and maturity_value < date.today():
        summary.append(
            f"만기일은 {maturity_str}로 이미 지났습니다. 실제 상환 완료 여부와 현재 거래 가능 상태를 확인해야 합니다."
        )
    elif has_call and has_put:
        summary.append(
            f"만기일은 {maturity_str}이며, 발행사의 콜옵션과 투자자의 풋옵션이 모두 포함되어 있습니다{exercise_str}."
        )
    elif has_call:
        summary.append(
            f"만기일은 {maturity_str}이며, 발행사가 만기 전에 상환할 수 있는 콜옵션(CALL)이 포함되어 있습니다{exercise_str}."
        )
    elif has_put:
        summary.append(
            f"만기일은 {maturity_str}이며, 투자자가 만기 전에 상환을 요구할 수 있는 풋옵션(PUT)이 포함되어 있습니다{exercise_str}."
        )
    else:
        summary.append(
            f"만기일은 {maturity_str}이며, 등록된 중도 조기상환 옵션은 없습니다. 만기 전 매도 시 시장가격에 따라 손익이 달라질 수 있습니다."
        )

    return summary
