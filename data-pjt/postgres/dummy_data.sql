-- Dummy data for the Django API tables.
-- Run after Django migrations:
--   docker exec -i postgres psql -U ssafyuser -d bonds_db < data-pjt/postgres/django_dummy_data.sql

BEGIN;

INSERT INTO industry (industry_name, created_at, updated_at)
VALUES
    ('유통업', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('정부', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('보험업', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('여신금융업', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

INSERT INTO bond_type (bond_type, created_at, updated_at)
VALUES
    ('회사채', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('국채', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('금융채', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

INSERT INTO seniority (seniority_name, created_at, updated_at)
VALUES
    ('선순위', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('후순위', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

INSERT INTO credit_rating (rating_name, rating_order, created_at, updated_at)
VALUES
    ('국채', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('AAA', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('AA', 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('A-', 6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('BBB0', 9, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

INSERT INTO guarantee_status (guarantee_status, created_at, updated_at)
VALUES
    ('무보증', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('국가보증', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

INSERT INTO issuer (industry_id, issuer_name, created_at, updated_at)
SELECT industry.id, v.issuer_name, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (
    VALUES
        ('유통업', '이랜드월드'),
        ('정부', '대한민국'),
        ('보험업', '푸본현대생명보험'),
        ('여신금융업', '현대캐피탈')
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
        ('이표채 고정금리', 1, 1, '후급', '2026-03-06'::date, '발행일', '일자기준', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('이표채 고정금리', 6, 6, '후급', '2020-12-10'::date, '발행일', '일자기준', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('고정금리부 이표채', 3, 3, '후급', '2021-12-14'::date, '발행일', '일자기준', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('이표채 고정금리', 3, 3, '후급', '2024-08-21'::date, '발행일', '일자기준', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
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
    call_reason,
    created_at,
    updated_at
)
SELECT *
FROM (
    VALUES
        ('NONE', NULL::date, NULL::date, NULL::date, NULL::date, '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('CALL', '2026-08-06'::date, NULL::date, NULL::date, NULL::date, '발행회사 선택', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('CALL', '2026-09-15'::date, NULL::date, NULL::date, NULL::date, '발행회사 선택', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
) AS v(
    option_type,
    exercise_start_date_1,
    exercise_end_date_1,
    exercise_start_date_2,
    exercise_end_date_2,
    call_reason,
    created_at,
    updated_at
)
WHERE NOT EXISTS (
    SELECT 1
    FROM bond_option_exercise
    WHERE bond_option_exercise.option_type = v.option_type
      AND bond_option_exercise.exercise_start_date_1 IS NOT DISTINCT FROM v.exercise_start_date_1
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
    bond_type.id,
    v.short_code,
    v.bond_name,
    v.short_name,
    issuer.id,
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
    seniority.id,
    option_exercise.id,
    guarantee_status.id,
    credit_rating.id,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM (
    VALUES
        ('KR6035651G21', '회사채', 'B035651G2', '이랜드월드107', '이랜드월드107', '이랜드월드', '2026-02-06'::date, '2027-02-05'::date, 6.7000, 60000000000, '한국투자증권', '이표채', '이표채 고정금리', 1, '2026-03-06'::date, 100.0000, '만기상환', '발행 후 6개월 이후 발행회사 선택에 따라 조기상환 가능', '선순위', 'CALL', '2026-08-06'::date, '무보증', 'BBB0'),
        ('KR103501G760', '국채', '03501G76', '국고채권 01750-3006', '국고01750-3006', '대한민국', '2020-06-10'::date, '2030-06-10'::date, 1.7500, 2000000000000, '국고채 전문딜러', '이표채', '이표채 고정금리', 6, '2020-12-10'::date, 100.0000, '만기상환', '', '선순위', 'NONE', NULL::date, '국가보증', '국채'),
        ('KR6086951B91', '금융채', 'B086951B9', '푸본현대생명보험18(후)', '푸본현대생명보험18', '푸본현대생명보험', '2021-09-14'::date, '2031-09-14'::date, 4.2000, 95000000000, '신한투자증권', '이표채', '고정금리부 이표채', 3, '2021-12-14'::date, 100.0000, '만기상환', '발행 5년 후 금리 재조정 및 콜옵션 행사 가능', '후순위', 'CALL', '2026-09-15'::date, '무보증', 'A-'),
        ('KR6123456A78', '회사채', 'B123456A', '현대캐피탈 회사채', '현대캐피탈 회사채', '현대캐피탈', '2024-05-21'::date, '2029-05-21'::date, 3.7000, 120000000000, 'KB증권', '이표채', '이표채 고정금리', 3, '2024-08-21'::date, 100.0000, '만기상환', '', '선순위', 'NONE', NULL::date, '무보증', 'AA')
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
    SELECT id
    FROM bond_cashflow_rule
    WHERE interest_payment_method = v.cashflow_method
      AND interest_payment_unit_months = v.cashflow_months
      AND first_interest_payment_date = v.first_interest_payment_date
    ORDER BY id
    LIMIT 1
) cashflow ON TRUE
JOIN LATERAL (
    SELECT id
    FROM bond_option_exercise
    WHERE option_type = v.option_type
      AND exercise_start_date_1 IS NOT DISTINCT FROM v.option_date
    ORDER BY id
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
    bond.id,
    v.base_date,
    v.price,
    v.ytm,
    v.duration,
    v.spread,
    v.trading_volume,
    v.substitute_price,
    v.bid_yield,
    v.ask_yield,
    v.price_change_rate,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM (
    VALUES
        ('KR6035651G21', '2026-06-18'::date, 10000.00, 6.920, 0.9100, 0.0000, 690000000, 8050, 6.920, 6.560, 0.0000),
        ('KR103501G760', '2026-06-18'::date, 10032.00, 3.310, 4.1000, 0.0000, 8610000000, 9990, 3.310, 3.260, -0.0600),
        ('KR6086951B91', '2026-06-18'::date, 9984.00, 5.680, 7.2000, 0.0000, 590000000, 8070, 5.680, 5.470, 0.3100),
        ('KR6123456A78', '2026-06-18'::date, 10011.00, 4.360, 2.8000, 0.0000, 1870000000, 9960, 4.360, 4.210, -0.2200)
) AS v(
    isin_code,
    base_date,
    price,
    ytm,
    duration,
    spread,
    trading_volume,
    substitute_price,
    bid_yield,
    ask_yield,
    price_change_rate
)
JOIN bond ON bond.isin_code = v.isin_code
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

INSERT INTO news_provider (provider_name, created_at, updated_at)
VALUES
    ('연합뉴스', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('한국경제', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('매일경제', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

INSERT INTO news (source_id, title, url, summary, content, published_at, created_at, updated_at)
SELECT
    news_provider.id,
    v.title,
    v.url,
    v.summary,
    v.summary,
    v.published_at,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM (
    VALUES
        ('연합뉴스', '국고채 금리, 장기물 중심으로 상승 마감', 'https://example.com/news/bond-yields-policy', '장기물 금리가 상승하며 채권 가격 부담이 커졌습니다.', '2026-06-17 09:30:00'::timestamp),
        ('한국경제', '회사채 시장, 우량 등급 중심으로 수요 회복', 'https://example.com/news/corporate-bond-demand', '우량 회사채 수요가 회복되며 조달 여건이 개선되고 있습니다.', '2026-06-17 11:10:00'::timestamp),
        ('매일경제', 'AA급 신용 스프레드 축소', 'https://example.com/news/credit-spread-aa', 'AA 등급 발행사의 스프레드가 소폭 축소됐습니다.', '2026-06-18 08:50:00'::timestamp)
) AS v(provider_name, title, url, summary, published_at)
JOIN news_provider ON news_provider.provider_name = v.provider_name
ON CONFLICT (url) DO UPDATE
SET source_id = EXCLUDED.source_id,
    title = EXCLUDED.title,
    summary = EXCLUDED.summary,
    content = EXCLUDED.content,
    published_at = EXCLUDED.published_at,
    updated_at = CURRENT_TIMESTAMP,
    deleted_at = NULL;

INSERT INTO glossary_category (category_name, created_at, updated_at)
VALUES
    ('기본 개념', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('가격/수익률', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('리스크', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

INSERT INTO glossary (category_id, term_name, difficulty, description, example_text, created_at, updated_at)
SELECT
    glossary_category.id,
    v.term_name,
    v.difficulty,
    v.description,
    v.example_text,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM (
    VALUES
        ('기본 개념', '채권', 'EASY', '정부, 공공기관, 기업 등이 자금을 빌리기 위해 발행하는 증서입니다.', '국고채, 회사채, 금융채'),
        ('가격/수익률', 'YTM', 'MEDIUM', '현재 가격에 매수해 만기까지 보유한다고 가정했을 때 기대하는 연환산 수익률입니다.', '매수수익률 3.82%'),
        ('리스크', '신용등급', 'MEDIUM', '발행자가 원리금을 갚을 능력을 평가한 등급입니다.', 'AAA, AA, A, BBB')
) AS v(category_name, term_name, difficulty, description, example_text)
JOIN glossary_category ON glossary_category.category_name = v.category_name
WHERE NOT EXISTS (
    SELECT 1 FROM glossary WHERE glossary.term_name = v.term_name
);

INSERT INTO country (country_name, created_at, updated_at)
VALUES
    ('한국', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('미국', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('일본', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

INSERT INTO base_rate (
    country_id,
    base_interest_rate,
    three_year_yield,
    ten_year_yield,
    yield_curve_spread,
    created_at,
    updated_at
)
SELECT country.id, v.base_interest_rate, v.three_year_yield, v.ten_year_yield, v.yield_curve_spread, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (
    VALUES
        ('한국', 3.500, 3.180, 3.420, 0.240),
        ('미국', 4.500, 4.050, 4.310, 0.260),
        ('일본', 0.500, 0.620, 1.080, 0.460)
) AS v(country_name, base_interest_rate, three_year_yield, ten_year_yield, yield_curve_spread)
JOIN country ON country.country_name = v.country_name;

INSERT INTO bank (bank_name, created_at, updated_at)
VALUES
    ('국민은행', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('신한은행', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('하나은행', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

INSERT INTO deposit_rate (bank_id, product_name, base_rate, prime_rate, created_at, updated_at)
SELECT bank.id, v.product_name, v.base_rate, v.prime_rate, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (
    VALUES
        ('국민은행', 'KB 정기예금', 3.100, 3.300),
        ('신한은행', '신한 정기예금', 3.050, 3.250),
        ('하나은행', '하나 정기예금', 3.000, 3.200)
) AS v(bank_name, product_name, base_rate, prime_rate)
JOIN bank ON bank.bank_name = v.bank_name;

COMMIT;
