-- Bond-EZ 데모 시드 (dummy_bonds_20_full.sql을 모델 스키마 컬럼명으로 변환)
-- 생성: bootstrap_demo 배포용. 재실행 안전(idempotent).
-- Full dummy data for BondEZ Django API tables.
-- Creates 20 bonds with issue/redemption, cashflow, option, and market data.
-- Safe to rerun: bonds and market data are upserted by isin_code / (bond_id, base_date).
-- docker compose exec -T db psql -U ssafyuser -d bonds_db < data-pjt/postgres/dummy_bonds_20_full.sql

BEGIN;

INSERT INTO industry (industry_name, created_at, updated_at)
SELECT v.industry_name, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (
    VALUES
        ('정부'),
        ('전기업'),
        ('금융업'),
        ('보험업'),
        ('여신금융업'),
        ('유통업'),
        ('자동차 부품 제조업'),
        ('정보통신업'),
        ('건설업'),
        ('의약품 제조업')
) AS v(industry_name)
WHERE NOT EXISTS (
    SELECT 1 FROM industry WHERE industry.industry_name = v.industry_name
);

INSERT INTO bond_type (bond_type, created_at, updated_at)
SELECT v.bond_type, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (
    VALUES
        ('국채'),
        ('특수채'),
        ('회사채'),
        ('금융채'),
        ('유동화SPC채'),
        ('조건부자본증권')
) AS v(bond_type)
WHERE NOT EXISTS (
    SELECT 1 FROM bond_type WHERE bond_type.bond_type = v.bond_type
);

INSERT INTO seniority (seniority_name, created_at, updated_at)
SELECT v.seniority_name, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (
    VALUES
        ('선순위'),
        ('후순위')
) AS v(seniority_name)
WHERE NOT EXISTS (
    SELECT 1 FROM seniority WHERE seniority.seniority_name = v.seniority_name
);

INSERT INTO credit_rating (rating_name, rating_order, created_at, updated_at)
SELECT v.rating_name, v.rating_order, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (
    VALUES
        ('국채', 0),
        ('AAA', 1),
        ('AA+', 2),
        ('AA', 3),
        ('AA-', 4),
        ('A+', 5),
        ('A', 6),
        ('A-', 7),
        ('BBB+', 8),
        ('BBB0', 9),
        ('BBB-', 10)
) AS v(rating_name, rating_order)
WHERE NOT EXISTS (
    SELECT 1 FROM credit_rating WHERE credit_rating.rating_name = v.rating_name
);

INSERT INTO guarantee_status (guarantee_status, created_at, updated_at)
SELECT v.guarantee_status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (
    VALUES
        ('무보증'),
        ('보증'),
        ('국가보증')
) AS v(guarantee_status)
WHERE NOT EXISTS (
    SELECT 1 FROM guarantee_status WHERE guarantee_status.guarantee_status = v.guarantee_status
);

INSERT INTO issuer (industry_id, issuer_name, created_at, updated_at)
SELECT industry.industry_id, v.issuer_name, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (
    VALUES
        ('정부', '대한민국'),
        ('전기업', '한국전력공사'),
        ('금융업', '한국수출입은행'),
        ('보험업', '푸본현대생명보험'),
        ('여신금융업', '현대캐피탈'),
        ('유통업', '이랜드월드'),
        ('자동차 부품 제조업', '아진산업'),
        ('정보통신업', '네오드림소프트'),
        ('건설업', '한빛건설'),
        ('의약품 제조업', '삼일제약'),
        ('금융업', '하나금융25호기업인수목적'),
        ('금융업', '와이아이제일차')
) AS v(industry_name, issuer_name)
JOIN industry ON industry.industry_name = v.industry_name
WHERE NOT EXISTS (
    SELECT 1 FROM issuer WHERE issuer.issuer_name = v.issuer_name
);

INSERT INTO bond_cashflow_rule (
    interest_payment_method,
    interest_payment_unit_months,
    interest_calculation_months,
    interest_pre_post_type,
    first_interest_payment_date,
    interest_payment_basis,
    interest_month_end_type,
    created_at,
    updated_at
)
SELECT *
FROM (
    VALUES
        ('이표채 고정금리', 1, 1, '후급', '2026-01-15'::date, '발행일', '일자기준', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('이표채 고정금리', 3, 3, '후급', '2026-03-15'::date, '발행일', '일자기준', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('이표채 고정금리', 6, 6, '후급', '2026-06-15'::date, '발행일', '일자기준', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('할인채', 12, 12, '선급', '2026-12-15'::date, '발행일', '일자기준', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('복리채 만기일시', 12, 12, '후급', '2026-12-31'::date, '발행일', '월말기준', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
) AS v(
    interest_payment_method,
    interest_payment_unit_months,
    interest_calculation_months,
    interest_pre_post_type,
    first_interest_payment_date,
    interest_payment_basis,
    interest_month_end_type,
    created_at,
    updated_at
)
WHERE NOT EXISTS (
    SELECT 1
    FROM bond_cashflow_rule
    WHERE bond_cashflow_rule.interest_payment_method = v.interest_payment_method
      AND bond_cashflow_rule.interest_payment_unit_months = v.interest_payment_unit_months
      AND bond_cashflow_rule.first_interest_payment_date = v.first_interest_payment_date
);

INSERT INTO bond_option_exercise (
    option_type,
    exercise_start_date_1,
    exercise_end_date_1,
    exercise_start_date_2,
    exercise_end_date_2,
    exercise_reason,
    created_at,
    updated_at
)
SELECT *
FROM (
    VALUES
        ('NONE', NULL::date, NULL::date, NULL::date, NULL::date, '옵션 없음', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('CALL', '2026-08-06'::date, '2026-08-20'::date, '2026-11-06'::date, '2026-11-20'::date, '발행회사 조기상환 선택권', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('CALL', '2026-09-15'::date, '2026-09-30'::date, '2027-03-15'::date, '2027-03-31'::date, '금리 재조정 전 콜옵션 행사 가능', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('CALL', '2027-06-15'::date, '2027-06-30'::date, '2028-06-15'::date, '2028-06-30'::date, '발행 후 2년 이후 조기상환 가능', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('PUT', '2026-12-15'::date, '2026-12-31'::date, '2027-06-15'::date, '2027-06-30'::date, '투자자 조기상환 청구권', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('CALL+PUT', '2027-01-20'::date, '2027-02-03'::date, '2028-01-20'::date, '2028-02-03'::date, '발행회사 콜 및 투자자 풋 가능', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
) AS v(
    option_type,
    exercise_start_date_1,
    exercise_end_date_1,
    exercise_start_date_2,
    exercise_end_date_2,
    exercise_reason,
    created_at,
    updated_at
)
WHERE NOT EXISTS (
    SELECT 1
    FROM bond_option_exercise
    WHERE bond_option_exercise.option_type = v.option_type
      AND bond_option_exercise.exercise_start_date_1 IS NOT DISTINCT FROM v.exercise_start_date_1
      AND bond_option_exercise.exercise_end_date_1 IS NOT DISTINCT FROM v.exercise_end_date_1
);

INSERT INTO bond (
    isin_code,
    bond_type_id,
    short_code,
    bond_name,
    short_name,
    issuer_id,
    issue_date,
    maturity_date,
    coupon_rate,
    issue_amount,
    underwriter,
    interest_type,
    cashflow_rule_id,
    maturity_redemption_rate,
    redemption_method,
    early_redemption_description,
    seniority_id,
    option_exercise_id,
    guarantee_status_id,
    rating_id,
    created_at,
    updated_at
)
SELECT
    v.isin_code,
    bond_type.bond_type_id,
    v.short_code,
    v.bond_name,
    v.short_name,
    issuer.issuer_id,
    v.issue_date,
    v.maturity_date,
    v.coupon_rate,
    v.issue_amount,
    v.underwriter,
    v.interest_type,
    cashflow.id,
    v.maturity_redemption_rate,
    v.redemption_method,
    v.early_redemption_description,
    seniority.seniority_id,
    option_exercise.id,
    guarantee_status.guarantee_status_id,
    credit_rating.rating_id,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM (
    VALUES
        ('KR9000000001', '특수채', 'D000001', '한국전력공사채권 더미1', '한전더미1', '한국전력공사', '2023-06-12'::date, '2027-06-12'::date, 4.0600, 140000000000, 'NH투자증권', '이표채', '이표채 고정금리', 6, '2026-06-15'::date, 100.0000, '만기상환', '만기 원금 100% 상환', '선순위', 'NONE', NULL::date, '무보증', 'AAA'),
        ('KR9000000002', '금융채', 'D000002', '한국수출입금융 2507마-할인-335', '수출입2507마', '한국수출입은행', '2025-07-15'::date, '2027-07-15'::date, 2.4100, 300000000000, '한국투자증권', '할인채', '할인채', 12, '2026-12-15'::date, 100.0000, '만기상환', '할인 발행 후 만기 일시 상환', '선순위', 'NONE', NULL::date, '국가보증', 'AAA'),
        ('KR9000000003', '회사채', 'D000003', '이랜드월드107', '이랜드107', '이랜드월드', '2026-02-06'::date, '2027-02-05'::date, 6.7000, 60000000000, '한국투자증권', '이표채', '이표채 고정금리', 1, '2026-01-15'::date, 100.0000, '만기상환', '발행 후 6개월 이후 발행회사 선택에 따라 조기상환 가능', '선순위', 'CALL', '2026-08-06'::date, '무보증', 'BBB0'),
        ('KR9000000004', '국채', 'D000004', '국고채권 01750-3006', '국고01750', '대한민국', '2020-06-10'::date, '2030-06-10'::date, 1.7500, 2000000000000, '국고채전문딜러', '이표채', '이표채 고정금리', 6, '2026-06-15'::date, 100.0000, '만기상환', '국고채 만기 원금 상환', '선순위', 'NONE', NULL::date, '국가보증', '국채'),
        ('KR9000000005', '회사채', 'D000005', '푸본현대생명보험18(후)', '푸본현대18', '푸본현대생명보험', '2021-09-14'::date, '2031-09-14'::date, 4.2000, 95000000000, '신한투자증권', '이표채', '이표채 고정금리', 3, '2026-03-15'::date, 100.0000, '만기상환', '발행 5년 후 금리 재조정 및 콜옵션 행사 가능', '후순위', 'CALL', '2026-09-15'::date, '무보증', 'A-'),
        ('KR9000000006', '회사채', 'D000006', '현대캐피탈 회사채', '현대캐피탈', '현대캐피탈', '2024-05-21'::date, '2029-05-21'::date, 3.7000, 120000000000, 'KB증권', '이표채', '이표채 고정금리', 3, '2026-03-15'::date, 100.0000, '만기상환', '여신전문금융회사 일반 회사채', '선순위', 'NONE', NULL::date, '무보증', 'AA'),
        ('KR9000000007', '회사채', 'D000007', '아진산업 21(사모/콜)', '아진산업21', '아진산업', '2025-06-16'::date, '2028-06-16'::date, 5.4000, 20000000000, '미래에셋증권', '이표채', '이표채 고정금리', 1, '2026-01-15'::date, 100.0000, '만기상환', '발행회사 콜옵션 행사 가능', '선순위', 'CALL', '2027-06-15'::date, '무보증', 'BBB+'),
        ('KR9000000008', '유동화SPC채', 'D000008', '네오드림소프트 1-3', '네오드림1-3', '네오드림소프트', '2024-06-15'::date, '2027-06-15'::date, 4.9500, 45000000000, '하나증권', '이표채', '이표채 고정금리', 3, '2026-03-15'::date, 100.0000, '만기상환', '유동화 SPC 선순위 채권', '선순위', 'NONE', NULL::date, '보증', 'A'),
        ('KR9000000009', '회사채', 'D000009', '삼일제약 18BW(사모/신/풋)', '삼일제약18BW', '삼일제약', '2023-06-15'::date, '2027-06-15'::date, 0.0000, 15000000000, '유진투자증권', '복리채', '복리채 만기일시', 12, '2026-12-31'::date, 100.0000, '만기상환', '투자자 풋옵션 행사 가능', '선순위', 'PUT', '2026-12-15'::date, '무보증', 'A-'),
        ('KR9000000010', '유동화SPC채', 'D000010', '하나금융25호기업인수목적 1CB', '하나금융25CB', '하나금융25호기업인수목적', '2025-06-14'::date, '2027-06-14'::date, 0.0000, 19883500000, '하나증권', '이표채', '이표채 고정금리', 3, '2026-03-15'::date, 100.0000, '만기상환', '전환권 및 조기상환 조건 확인 필요', '선순위', 'NONE', NULL::date, '무보증', 'BBB0'),
        ('KR9000000011', '회사채', 'D000011', '한빛건설 제12회', '한빛건설12', '한빛건설', '2024-10-01'::date, '2027-10-01'::date, 5.8500, 80000000000, '대신증권', '이표채', '이표채 고정금리', 6, '2026-06-15'::date, 100.0000, '만기상환', '건설업 업황 및 유동성 확인 필요', '선순위', 'NONE', NULL::date, '무보증', 'BBB+'),
        ('KR9000000012', '금융채', 'D000012', '현대캐피탈 2309-2', '현캐2309-2', '현대캐피탈', '2023-09-01'::date, '2028-09-01'::date, 4.1500, 220000000000, '삼성증권', '이표채', '이표채 고정금리', 3, '2026-03-15'::date, 100.0000, '만기상환', '여전채 신용스프레드 변동 확인 필요', '선순위', 'NONE', NULL::date, '무보증', 'AA-'),
        ('KR9000000013', '특수채', 'D000013', '한국전력공사채권1402', '한전1402', '한국전력공사', '2024-02-20'::date, '2029-02-20'::date, 3.9500, 250000000000, 'KB증권', '이표채', '이표채 고정금리', 6, '2026-06-15'::date, 100.0000, '만기상환', '공기업 재무구조 및 정책 리스크 확인', '선순위', 'NONE', NULL::date, '무보증', 'AAA'),
        ('KR9000000014', '조건부자본증권', 'D000014', '푸본현대생명 조건부자본 5', '푸본조건부5', '푸본현대생명보험', '2023-03-30'::date, '2033-03-30'::date, 5.6000, 70000000000, 'NH투자증권', '이표채', '이표채 고정금리', 3, '2026-03-15'::date, 100.0000, '만기상환', '후순위 조건부자본증권, 콜옵션 가능', '후순위', 'CALL', '2027-06-15'::date, '무보증', 'A'),
        ('KR9000000015', '회사채', 'D000015', '이랜드월드110', '이랜드110', '이랜드월드', '2025-01-15'::date, '2028-01-15'::date, 6.2500, 50000000000, '한국투자증권', '이표채', '이표채 고정금리', 1, '2026-01-15'::date, 100.0000, '만기상환', '발행회사 선택 조기상환 가능', '선순위', 'CALL+PUT', '2027-01-20'::date, '무보증', 'BBB0'),
        ('KR9000000016', '금융채', 'D000016', '한국수출입금융 2601가', '수출입2601가', '한국수출입은행', '2024-01-10'::date, '2029-01-10'::date, 3.5500, 400000000000, '메리츠증권', '이표채', '이표채 고정금리', 6, '2026-06-15'::date, 100.0000, '만기상환', '정책금융기관 발행 금융채', '선순위', 'NONE', NULL::date, '국가보증', 'AAA'),
        ('KR9000000017', '회사채', 'D000017', '아진산업 22(사모)', '아진산업22', '아진산업', '2024-11-20'::date, '2027-11-20'::date, 5.1000, 18000000000, 'IBK투자증권', '이표채', '이표채 고정금리', 3, '2026-03-15'::date, 100.0000, '만기상환', '자동차 부품 업황 확인 필요', '선순위', 'NONE', NULL::date, '무보증', 'BBB+'),
        ('KR9000000018', '회사채', 'D000018', '네오드림소프트 1-4', '네오드림1-4', '네오드림소프트', '2024-12-15'::date, '2027-06-15'::date, 5.3000, 40000000000, '신한투자증권', '이표채', '이표채 고정금리', 3, '2026-03-15'::date, 100.0000, '만기상환', '유동성 및 담보 구조 확인 필요', '선순위', 'CALL', '2027-06-15'::date, '보증', 'A-'),
        ('KR9000000019', '회사채', 'D000019', '삼일제약 20', '삼일제약20', '삼일제약', '2025-04-01'::date, '2028-04-01'::date, 4.8500, 30000000000, '대신증권', '이표채', '이표채 고정금리', 6, '2026-06-15'::date, 100.0000, '만기상환', '의약품 제조업 회사채', '선순위', 'NONE', NULL::date, '무보증', 'A'),
        ('KR9000000020', '국채', 'D000020', '국고채권 03250-3306', '국고03250', '대한민국', '2023-06-10'::date, '2033-06-10'::date, 3.2500, 2500000000000, '국고채전문딜러', '이표채', '이표채 고정금리', 6, '2026-06-15'::date, 100.0000, '만기상환', '국고채 만기 원금 상환', '선순위', 'NONE', NULL::date, '국가보증', '국채')
) AS v(
    isin_code,
    bond_type,
    short_code,
    bond_name,
    short_name,
    issuer_name,
    issue_date,
    maturity_date,
    coupon_rate,
    issue_amount,
    underwriter,
    interest_type,
    cashflow_method,
    cashflow_months,
    first_interest_payment_date,
    maturity_redemption_rate,
    redemption_method,
    early_redemption_description,
    seniority_name,
    option_type,
    option_date,
    guarantee_status_name,
    rating_name
)
JOIN bond_type ON bond_type.bond_type = v.bond_type
JOIN issuer ON issuer.issuer_name = v.issuer_name
JOIN seniority ON seniority.seniority_name = v.seniority_name
JOIN guarantee_status ON guarantee_status.guarantee_status = v.guarantee_status_name
JOIN credit_rating ON credit_rating.rating_name = v.rating_name
JOIN LATERAL (
    SELECT cashflow_rule_id AS id
    FROM bond_cashflow_rule
    WHERE interest_payment_method = v.cashflow_method
      AND interest_payment_unit_months = v.cashflow_months
      AND first_interest_payment_date = v.first_interest_payment_date
    ORDER BY 1
    LIMIT 1
) cashflow ON TRUE
JOIN LATERAL (
    SELECT option_exercise_id AS id
    FROM bond_option_exercise
    WHERE option_type = v.option_type
      AND exercise_start_date_1 IS NOT DISTINCT FROM v.option_date
    ORDER BY 1
    LIMIT 1
) option_exercise ON TRUE
ON CONFLICT (isin_code) DO UPDATE
SET bond_type_id = EXCLUDED.bond_type_id,
    short_code = EXCLUDED.short_code,
    bond_name = EXCLUDED.bond_name,
    short_name = EXCLUDED.short_name,
    issuer_id = EXCLUDED.issuer_id,
    issue_date = EXCLUDED.issue_date,
    maturity_date = EXCLUDED.maturity_date,
    coupon_rate = EXCLUDED.coupon_rate,
    issue_amount = EXCLUDED.issue_amount,
    underwriter = EXCLUDED.underwriter,
    interest_type = EXCLUDED.interest_type,
    cashflow_rule_id = EXCLUDED.cashflow_rule_id,
    maturity_redemption_rate = EXCLUDED.maturity_redemption_rate,
    redemption_method = EXCLUDED.redemption_method,
    early_redemption_description = EXCLUDED.early_redemption_description,
    seniority_id = EXCLUDED.seniority_id,
    option_exercise_id = EXCLUDED.option_exercise_id,
    guarantee_status_id = EXCLUDED.guarantee_status_id,
    rating_id = EXCLUDED.rating_id,
    updated_at = CURRENT_TIMESTAMP,
    deleted_at = NULL;

-- 시세: CURRENT_DATE 기준 최근 90일(주말 제외) 시계열을 결정적(비랜덤) 수식으로 생성.
-- 재실행하면 같은 날짜에는 같은 값이 다시 계산되어 idempotent하고,
-- 부팅 시마다 실행하면 "오늘"까지의 데이터가 항상 채워진다.
INSERT INTO bond_market_data (
    bond_id,
    base_date,
    price,
    ytm,
    duration,
    spread,
    trading_volume,
    substitute_price,
    bid_yield,
    ask_yield,
    price_change_rate,
    created_at,
    updated_at
)
SELECT
    b.bond_id,
    (CURRENT_DATE - d.n)::date,
    p.price_now,
    p.ytm_now,
    round((v.duration + d.n / 365.0)::numeric, 4),
    round(greatest(0, v.spread + 0.05 * sin((d.n + b.bond_id) / 7.0))::numeric, 4),
    round(v.trading_volume * (0.7 + 0.3 * abs(sin(d.n * 1.7 + b.bond_id))))::bigint,
    v.substitute_price,
    round((p.ytm_now + 0.06)::numeric, 3),
    round((p.ytm_now - 0.06)::numeric, 3),
    round(((p.price_now - p.price_prev) / p.price_prev * 100)::numeric, 4),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM (
    VALUES
        ('KR9000000001', 10018.00, 4.120, 0.4800, 0.1200, 1320000000, 9985),
        ('KR9000000002', 9972.00, 3.080, 0.9200, 0.0800, 2650000000, 9920),
        ('KR9000000003', 10000.00, 6.920, 0.9100, 3.1200, 690000000, 8050),
        ('KR9000000004', 10032.00, 3.310, 4.1000, 0.0000, 8610000000, 9990),
        ('KR9000000005', 9984.00, 5.680, 7.2000, 2.3600, 590000000, 8070),
        ('KR9000000006', 10011.00, 4.360, 2.8000, 0.8700, 1870000000, 9960),
        ('KR9000000007', 10004.00, 5.550, 0.7600, 1.8500, 420000000, 9700),
        ('KR9000000008', 9996.00, 5.110, 0.9800, 1.4200, 360000000, 9640),
        ('KR9000000009', 9860.00, 6.150, 0.8200, 2.0800, 210000000, 9300),
        ('KR9000000010', 9955.00, 5.740, 0.3900, 2.2200, 180000000, 9180),
        ('KR9000000011', 10021.00, 5.980, 1.5400, 2.4800, 310000000, 9410),
        ('KR9000000012', 10008.00, 4.470, 2.1200, 0.9600, 1480000000, 9890),
        ('KR9000000013', 10015.00, 3.960, 2.5600, 0.2100, 2240000000, 10010),
        ('KR9000000014', 9979.00, 6.240, 5.9000, 2.7500, 280000000, 8990),
        ('KR9000000015', 10035.00, 6.480, 1.4300, 2.9800, 330000000, 9100),
        ('KR9000000016', 10007.00, 3.740, 2.3500, 0.1600, 3260000000, 10020),
        ('KR9000000017', 9992.00, 5.420, 1.2400, 1.9600, 240000000, 9500),
        ('KR9000000018', 10002.00, 5.630, 1.1000, 2.0700, 275000000, 9480),
        ('KR9000000019', 10019.00, 4.980, 1.7200, 1.1500, 460000000, 9705),
        ('KR9000000020', 10045.00, 3.520, 6.8500, 0.0000, 12400000000, 10030)
) AS v(
    isin_code,
    price,
    ytm,
    duration,
    spread,
    trading_volume,
    substitute_price
)
JOIN bond b ON b.isin_code = v.isin_code
CROSS JOIN generate_series(0, 89) AS d(n)
CROSS JOIN LATERAL (
    SELECT
        round((v.price * (1 + 0.004 * sin((d.n + b.bond_id * 3) / 4.0)
                            + 0.002 * cos((d.n * 2 + b.bond_id * 7) / 3.0)))::numeric, 2) AS price_now,
        round((v.price * (1 + 0.004 * sin((d.n + 1 + b.bond_id * 3) / 4.0)
                            + 0.002 * cos(((d.n + 1) * 2 + b.bond_id * 7) / 3.0)))::numeric, 2) AS price_prev,
        round((v.ytm + 0.15 * sin((d.n + b.bond_id * 5) / 6.0))::numeric, 3) AS ytm_now
) AS p
WHERE extract(isodow FROM CURRENT_DATE - d.n) < 6
ON CONFLICT (bond_id, base_date) DO UPDATE
SET price = EXCLUDED.price,
    ytm = EXCLUDED.ytm,
    duration = EXCLUDED.duration,
    spread = EXCLUDED.spread,
    trading_volume = EXCLUDED.trading_volume,
    substitute_price = EXCLUDED.substitute_price,
    bid_yield = EXCLUDED.bid_yield,
    ask_yield = EXCLUDED.ask_yield,
    price_change_rate = EXCLUDED.price_change_rate,
    updated_at = CURRENT_TIMESTAMP,
    deleted_at = NULL;

INSERT INTO country (country_name, created_at, updated_at)
SELECT v.country_name, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (VALUES ('한국'), ('미국'), ('일본')) AS v(country_name)
WHERE NOT EXISTS (
    SELECT 1 FROM country c WHERE c.country_name = v.country_name
);

INSERT INTO base_rate (
    country_id,
    base_interest_rate,
    three_year_yield,
    ten_year_yield,
    yield_curve_spread,
    created_at,
    updated_at
)
SELECT
    country.id,
    v.base_interest_rate,
    v.three_year_yield,
    v.ten_year_yield,
    v.yield_curve_spread,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM (
    VALUES
        ('한국', 3.500, 3.180, 3.420, 0.240),
        ('미국', 4.500, 4.120, 4.310, 0.190),
        ('일본', 0.500, 0.420, 0.680, 0.260)
) AS v(country_name, base_interest_rate, three_year_yield, ten_year_yield, yield_curve_spread)
JOIN country ON country.country_name = v.country_name
WHERE NOT EXISTS (
    SELECT 1
    FROM base_rate br
    WHERE br.country_id = country.id
      AND br.deleted_at IS NULL
);

INSERT INTO bank (bank_name, created_at, updated_at)
SELECT v.bank_name, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (VALUES ('국민은행'), ('신한은행'), ('하나은행'), ('우리은행')) AS v(bank_name)
WHERE NOT EXISTS (
    SELECT 1 FROM bank b WHERE b.bank_name = v.bank_name
);

INSERT INTO deposit_rate (
    bank_id,
    product_name,
    base_rate,
    prime_rate,
    created_at,
    updated_at
)
SELECT
    bank.id,
    v.product_name,
    v.base_rate,
    v.prime_rate,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM (
    VALUES
        ('국민은행', 'KB Star 정기예금', 2.950, 3.820),
        ('신한은행', '신한 S드림 정기예금', 2.900, 3.650),
        ('하나은행', '하나의 정기예금', 2.850, 3.720),
        ('우리은행', 'WON 플러스 예금', 3.000, 3.780)
) AS v(bank_name, product_name, base_rate, prime_rate)
JOIN bank ON bank.bank_name = v.bank_name
WHERE NOT EXISTS (
    SELECT 1
    FROM deposit_rate dr
    WHERE dr.bank_id = bank.id
      AND dr.product_name = v.product_name
      AND dr.deleted_at IS NULL
);

COMMIT;


-- ─── 뉴스 / 용어사전 시드 ───────────────────────────────────────

INSERT INTO news_provider (provider_name, created_at, updated_at)
SELECT v.provider_name, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (VALUES ('연합뉴스'), ('한국경제'), ('매일경제'), ('서울경제')) AS v(provider_name)
WHERE NOT EXISTS (SELECT 1 FROM news_provider p WHERE p.provider_name = v.provider_name);

INSERT INTO news (source_id, title, url, summary, published_at, created_at, updated_at)
SELECT news_provider.provider_id, v.title, v.url, v.summary, v.published_at, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (
    VALUES
        ('연합뉴스', '국고채 금리, 장기물 중심으로 상승 마감', 'https://example.com/news/bond-yields-policy', '기준금리 동결 전망 속에 국고채 10년물 금리가 상승하며 장기물 중심으로 채권 가격 부담이 커졌다.', CURRENT_TIMESTAMP - interval '4 hours'),
        ('한국경제', '회사채 시장, 우량 등급 중심으로 수요 회복', 'https://example.com/news/corporate-bond-demand', 'AA급 이상 우량 회사채에 기관 수요가 몰리며 발행사들의 자금 조달 여건이 개선되고 있다.', CURRENT_TIMESTAMP - interval '9 hours'),
        ('매일경제', 'AA급 신용 스프레드 축소', 'https://example.com/news/credit-spread-aa', 'AA등급 회사채와 국고채 간 신용 스프레드가 소폭 축소되며 크레딧 시장 투자심리가 안정되고 있다.', CURRENT_TIMESTAMP - interval '1 day 2 hours'),
        ('서울경제', '개인투자자, 장외 채권 순매수 사상 최대', 'https://example.com/news/retail-bond-buying', '금리 고점 인식이 확산되며 개인투자자의 장외 채권 순매수 규모가 월간 기준 사상 최대를 기록했다.', CURRENT_TIMESTAMP - interval '1 day 8 hours'),
        ('연합뉴스', '여전채 발행 재개 조짐…현대캐피탈 수요예측 흥행', 'https://example.com/news/card-bond-demand', '현대캐피탈 회사채 수요예측에 목표액의 세 배가 넘는 자금이 몰리며 여전채 발행 시장이 회복 조짐을 보였다.', CURRENT_TIMESTAMP - interval '2 days 3 hours'),
        ('매일경제', '한전채 발행 물량 축소에 특수채 강세', 'https://example.com/news/kepco-bond-supply', '한국전력의 발행 물량 축소 전망에 특수채 금리가 하락하며 관련 채권 가격이 강세를 보였다.', CURRENT_TIMESTAMP - interval '2 days 9 hours'),
        ('한국경제', '보험사 후순위채 콜옵션 행사 릴레이', 'https://example.com/news/insurer-call-options', '주요 보험사들이 후순위채 콜옵션을 예정대로 행사하면서 조건부자본증권 시장의 신뢰가 유지되고 있다.', CURRENT_TIMESTAMP - interval '3 days 5 hours'),
        ('서울경제', '건설채 스프레드 확대…BBB급 옥석 가리기', 'https://example.com/news/construction-bond-spread', '건설 업황 우려로 BBB급 건설사 회사채의 신용 스프레드가 확대되며 종목별 차별화가 뚜렷해지고 있다.', CURRENT_TIMESTAMP - interval '4 days 1 hour')
) AS v(provider_name, title, url, summary, published_at)
JOIN news_provider ON news_provider.provider_name = v.provider_name
ON CONFLICT (url) DO UPDATE
SET source_id = EXCLUDED.source_id,
    title = EXCLUDED.title,
    summary = EXCLUDED.summary,
    published_at = EXCLUDED.published_at,
    updated_at = CURRENT_TIMESTAMP,
    deleted_at = NULL;

INSERT INTO glossary_category (category_name, created_at, updated_at)
SELECT v.category_name, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (VALUES ('기본 개념'), ('가격/수익률'), ('리스크'), ('발행/유통')) AS v(category_name)
WHERE NOT EXISTS (SELECT 1 FROM glossary_category c WHERE c.category_name = v.category_name);

INSERT INTO glossary (category_id, term_name, difficulty, description, example_text, created_at, updated_at)
SELECT glossary_category.category_id, v.term_name, v.difficulty, v.description, v.example_text, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (
    VALUES
        ('기본 개념', '채권', 'EASY', '정부, 공공기관, 기업 등이 자금을 빌리기 위해 발행하는 증서로, 정해진 기간 후 원금과 이자를 돌려받습니다.', '국고채, 회사채, 금융채'),
        ('기본 개념', '액면가', 'EASY', '채권에 표시된 금액으로, 만기에 상환받는 원금입니다.', '액면가 10,000원'),
        ('기본 개념', '표면금리', 'EASY', '채권 발행 시 약속된 이자율로, 액면가 기준으로 지급됩니다.', '표면금리 연 3.5%'),
        ('기본 개념', '만기', 'EASY', '채권의 원금이 상환되는 날짜까지의 기간입니다.', '3년 만기 국고채'),
        ('가격/수익률', 'YTM', 'MEDIUM', '만기수익률. 현재 가격에 매수해 만기까지 보유할 때 기대하는 연환산 수익률입니다.', '매수수익률 3.82%'),
        ('가격/수익률', '듀레이션', 'HARD', '금리 변화에 대한 채권 가격의 민감도를 나타내는 지표로, 값이 클수록 금리 변동 위험이 큽니다.', '듀레이션 4.2년'),
        ('가격/수익률', '할인채', 'MEDIUM', '이자를 지급하지 않는 대신 액면가보다 싸게 발행되어 만기에 액면가를 받는 채권입니다.', '통화안정증권 할인 발행'),
        ('리스크', '신용등급', 'MEDIUM', '발행자가 원리금을 갚을 능력을 신용평가사가 평가한 등급입니다. AAA가 가장 높습니다.', 'AAA, AA, A, BBB'),
        ('리스크', '신용스프레드', 'HARD', '회사채 금리와 국고채 금리의 차이로, 신용위험에 대한 보상을 나타냅니다.', 'AA- 3년물 스프레드 70bp'),
        ('리스크', '콜옵션', 'MEDIUM', '발행회사가 만기 전에 채권을 조기상환할 수 있는 권리입니다.', '발행 5년 후 콜옵션 행사 가능'),
        ('발행/유통', '수요예측', 'MEDIUM', '회사채 발행 전에 기관투자자의 매수 수요를 조사해 금리와 물량을 정하는 절차입니다.', '수요예측 경쟁률 3:1'),
        ('발행/유통', '장외거래', 'MEDIUM', '거래소를 거치지 않고 증권사 창구 등을 통해 채권을 사고파는 방식입니다.', '증권사 앱 장외 채권 매매')
) AS v(category_name, term_name, difficulty, description, example_text)
JOIN glossary_category ON glossary_category.category_name = v.category_name
WHERE NOT EXISTS (SELECT 1 FROM glossary g WHERE g.term_name = v.term_name);

