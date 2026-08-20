-- Bond-EZ 라이브 데모용 스키마 (idempotent)
--
-- 배경: 데이터 파이프라인(data-pjt/postgres/init.sql)의 ERD 스키마와
-- Django 마이그레이션(0001)이 만드는 스키마는 PK 컬럼명이 다르다
-- (bond_id vs id). Django 모델은 db_column으로 ERD 스키마를 가리키므로,
-- 데모 DB는 이 파일로 모델 정의에 정확히 일치하는 테이블을 만들고
-- bonds/glossary/news 마이그레이션은 --fake 처리한다. (bootstrap_demo 커맨드 참조)
--
-- init.sql과의 차이: 데모에 불필요한 요소 제거(스테이징/트리거/권한/pgvector),
-- 모델이 CharField로 읽는 컬럼은 enum 대신 VARCHAR 사용.

CREATE TABLE IF NOT EXISTS industry (
    industry_id BIGSERIAL PRIMARY KEY,
    industry_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS issuer (
    issuer_id BIGSERIAL PRIMARY KEY,
    industry_id BIGINT NOT NULL REFERENCES industry(industry_id) ON DELETE CASCADE,
    issuer_name VARCHAR(100) NOT NULL,
    crno VARCHAR(50) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS bond_type (
    bond_type_id BIGSERIAL PRIMARY KEY,
    bond_type VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS seniority (
    seniority_id BIGSERIAL PRIMARY KEY,
    seniority_name VARCHAR(20) NOT NULL UNIQUE,
    priority_order BIGINT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS credit_rating (
    rating_id BIGSERIAL PRIMARY KEY,
    rating_name VARCHAR(30) NOT NULL UNIQUE,
    rating_order BIGINT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS guarantee_status (
    guarantee_status_id BIGSERIAL PRIMARY KEY,
    guarantee_status VARCHAR(10) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS bond_cashflow_rule (
    cashflow_rule_id BIGSERIAL PRIMARY KEY,
    interest_payment_method VARCHAR(255) NULL,
    interest_payment_unit_months INTEGER NULL,
    interest_calculation_months INTEGER NULL,
    interest_pre_post_type VARCHAR(255) NULL,
    first_interest_payment_date DATE NULL,
    interest_payment_basis VARCHAR(255) NULL,
    interest_month_end_type VARCHAR(255) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS bond_option_exercise (
    option_exercise_id BIGSERIAL PRIMARY KEY,
    option_type VARCHAR(20) NOT NULL DEFAULT 'NONE',
    exercise_start_date_1 DATE NULL,
    exercise_end_date_1 DATE NULL,
    exercise_start_date_2 DATE NULL,
    exercise_end_date_2 DATE NULL,
    exercise_reason TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS bond (
    bond_id BIGSERIAL PRIMARY KEY,
    isin_code VARCHAR(255) NOT NULL UNIQUE,
    bond_type_id BIGINT NOT NULL REFERENCES bond_type(bond_type_id),
    short_code VARCHAR(255) NULL UNIQUE,
    bond_name VARCHAR(255) NOT NULL,
    short_name VARCHAR(255) NULL,
    issuer_id BIGINT NOT NULL REFERENCES issuer(issuer_id),
    issue_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    coupon_rate DECIMAL(10, 4) NOT NULL,
    issue_amount BIGINT NULL,
    underwriter VARCHAR(255) NULL,
    interest_type VARCHAR(100) NULL,
    option_type VARCHAR(20) NULL,
    payment_cycle_months INTEGER NULL,
    cashflow_rule_id BIGINT NULL REFERENCES bond_cashflow_rule(cashflow_rule_id) ON DELETE SET NULL,
    maturity_redemption_rate DECIMAL(8, 4) NULL,
    redemption_method VARCHAR(255) NULL,
    early_redemption_description TEXT NULL,
    seniority_id BIGINT NOT NULL REFERENCES seniority(seniority_id),
    option_exercise_id BIGINT NULL REFERENCES bond_option_exercise(option_exercise_id),
    guarantee_status_id BIGINT NOT NULL REFERENCES guarantee_status(guarantee_status_id),
    rating_id BIGINT NOT NULL REFERENCES credit_rating(rating_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_bond_bond_name ON bond(bond_name);
CREATE INDEX IF NOT EXISTS idx_bond_maturity_date ON bond(maturity_date);

CREATE TABLE IF NOT EXISTS bond_market_data (
    market_data_id BIGSERIAL PRIMARY KEY,
    bond_id BIGINT NOT NULL REFERENCES bond(bond_id) ON DELETE CASCADE,
    base_date DATE NOT NULL,
    price DECIMAL(15, 2) NULL,
    ytm DECIMAL(6, 3) NULL,
    duration DECIMAL(8, 4) NULL,
    spread DECIMAL(8, 4) NULL,
    trading_volume BIGINT NULL,
    substitute_price VARCHAR(255) NULL,
    bid_yield VARCHAR(255) NULL,
    ask_yield VARCHAR(255) NULL,
    price_change_rate VARCHAR(255) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL,
    CONSTRAINT uniq_bond_market_data_date UNIQUE(bond_id, base_date)
);

CREATE OR REPLACE VIEW latest_bond_market_data AS
SELECT DISTINCT ON (bond_id)
    market_data_id,
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
    price_change_rate
FROM bond_market_data
WHERE deleted_at IS NULL
ORDER BY bond_id, base_date DESC, market_data_id DESC;

CREATE TABLE IF NOT EXISTS news_provider (
    provider_id BIGSERIAL PRIMARY KEY,
    provider_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS news (
    news_id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES news_provider(provider_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    url VARCHAR(255) NOT NULL UNIQUE,
    summary TEXT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

-- news_article: Flink 스테이징 테이블 (데모에서는 비어있지만 폴백 코드가 참조)
CREATE TABLE IF NOT EXISTS news_article (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    source VARCHAR(100) NOT NULL,
    url VARCHAR(500) UNIQUE NOT NULL,
    summary TEXT NULL,
    write_date TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS glossary_category (
    category_id BIGSERIAL PRIMARY KEY,
    category_name VARCHAR(50) NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS glossary (
    term_id BIGSERIAL PRIMARY KEY,
    category_id BIGINT NOT NULL REFERENCES glossary_category(category_id) ON DELETE CASCADE,
    term_name VARCHAR(255) NOT NULL,
    difficulty VARCHAR(20) NOT NULL DEFAULT 'EASY',
    description TEXT NOT NULL,
    example_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL
);

-- bonds_master: bond 테이블이 비어있을 때의 폴백 평면 테이블 (데모에서는 비워둠)
CREATE TABLE IF NOT EXISTS bonds_master (
    isin_code VARCHAR(255) PRIMARY KEY,
    short_code VARCHAR(255) NULL,
    bond_name VARCHAR(255) NULL,
    short_name VARCHAR(255) NULL,
    company_name VARCHAR(255) NULL,
    company_id VARCHAR(255) NULL,
    industry VARCHAR(255) NULL,
    bond_type VARCHAR(255) NULL,
    issue_date DATE NULL,
    maturity_date DATE NULL,
    coupon_rate DECIMAL(10, 4) NULL,
    issue_amount BIGINT NULL,
    underwriter VARCHAR(255) NULL,
    interest_type VARCHAR(255) NULL,
    payment_cycle VARCHAR(255) NULL,
    seniority VARCHAR(255) NULL,
    guarantee_status VARCHAR(255) NULL,
    credit_rating VARCHAR(255) NULL,
    call_put_option VARCHAR(255) NULL
);
