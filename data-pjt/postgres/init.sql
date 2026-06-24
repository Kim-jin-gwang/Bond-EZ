-- 0. bonds_db 및 airflow 데이터베이스 생성
CREATE DATABASE bonds_db;
CREATE DATABASE airflow;

-- ssafyuser에게 권한 부여를 위한 추가 설정
ALTER DATABASE bonds_db OWNER TO ssafyuser;
ALTER DATABASE airflow OWNER TO ssafyuser;

-- 1. pgvector 확장 활성화
-- embedding VECTOR(1536) 타입을 사용하기 위해 필요
CREATE EXTENSION IF NOT EXISTS vector;


-- 2. public 스키마 권한 부여
-- ssafyuser가 public 스키마 안의 객체를 조회하고 생성할 수 있도록 설정
GRANT USAGE ON SCHEMA public TO ssafyuser;
GRANT CREATE ON SCHEMA public TO ssafyuser;


-- 3. 앞으로 ssafyuser가 생성하는 객체에 대한 기본 권한 설정
-- ssafyuser가 새로 만드는 테이블, 시퀀스, 함수에 대해 자기 자신이 계속 사용할 수 있도록 명시
ALTER DEFAULT PRIVILEGES FOR ROLE ssafyuser IN SCHEMA public
GRANT ALL PRIVILEGES ON TABLES TO ssafyuser;

ALTER DEFAULT PRIVILEGES FOR ROLE ssafyuser IN SCHEMA public
GRANT ALL PRIVILEGES ON SEQUENCES TO ssafyuser;

ALTER DEFAULT PRIVILEGES FOR ROLE ssafyuser IN SCHEMA public
GRANT ALL PRIVILEGES ON FUNCTIONS TO ssafyuser;


-- 5. news_article 테이블 생성 (Flink 수집용 스테이징 테이블 역할)
CREATE TABLE IF NOT EXISTS news_article (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    source VARCHAR(100) NOT NULL,
    url VARCHAR(500) UNIQUE NOT NULL,
    write_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5-1. ERD에 명시된 news_provider 테이블 생성
CREATE TABLE IF NOT EXISTS news_provider (
    provider_id BIGSERIAL PRIMARY KEY,
    provider_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 5-2. ERD에 명시된 news 테이블 생성
CREATE TABLE IF NOT EXISTS news (
    news_id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES news_provider(provider_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    url VARCHAR(255) NOT NULL UNIQUE,
    summary TEXT NULL,
    published_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 5-3. ERD에 명시된 glossary_category 테이블 생성
CREATE TABLE IF NOT EXISTS glossary_category (
    category_id BIGSERIAL PRIMARY KEY,
    category_name VARCHAR(50) NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 5-4. ERD에 명시된 difficulty ENUM 타입 생성
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'difficulty_enum') THEN
        CREATE TYPE difficulty_enum AS ENUM ('입문', '기초', '중요', '심화');
    END IF;
END$$;

-- 5-5. ERD에 명시된 glossary 테이블 생성
CREATE TABLE IF NOT EXISTS glossary (
    term_id BIGSERIAL PRIMARY KEY,
    category_id BIGINT NOT NULL REFERENCES glossary_category(category_id) ON DELETE CASCADE,
    term_name VARCHAR(255) NOT NULL,
    difficulty difficulty_enum NOT NULL,
    description TEXT NOT NULL,
    example_text TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 5-6. ERD에 명시된 Country, BaseRate, Bank, DepositRate 테이블 생성
CREATE TABLE IF NOT EXISTS "Country" (
    country_id BIGSERIAL PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS "BaseRate" (
    base_rate_id BIGSERIAL PRIMARY KEY,
    country_id BIGINT NOT NULL REFERENCES "Country"(country_id) ON DELETE CASCADE,
    base_date DATE NOT NULL DEFAULT CURRENT_DATE,
    base_interest_rate DECIMAL(8, 4) NULL,
    three_year_yield DECIMAL(8, 4) NULL,
    ten_year_yield DECIMAL(8, 4) NULL,
    yield_curve_spread DECIMAL(8, 4) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    CONSTRAINT base_rate_country_date_unique UNIQUE(country_id, base_date)
);

CREATE TABLE IF NOT EXISTS "Bank" (
    bank_id BIGSERIAL PRIMARY KEY,
    bank_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS "DepositRate" (
    deposit_rate_id BIGSERIAL PRIMARY KEY,
    bank_id BIGINT NOT NULL REFERENCES "Bank"(bank_id) ON DELETE CASCADE,
    product_name VARCHAR(50) NOT NULL,
    base_rate DECIMAL(8, 4) NULL,
    prime_rate DECIMAL(8, 4) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    CONSTRAINT deposit_rate_bank_product_unique UNIQUE(bank_id, product_name)
);

-- 5-6. news_article (수집 데이터)에서 NewsProvider 및 News로 자동 변환/동기화하는 트리거 생성
CREATE OR REPLACE FUNCTION sync_news_article_to_erd()
RETURNS TRIGGER AS $$
DECLARE
    v_provider_id BIGINT;
BEGIN
    -- news_provider에 언론사 정보 삽입/가져오기 (최대 50자 제한)
    INSERT INTO news_provider (provider_name, created_at, updated_at)
    VALUES (LEFT(NEW.source, 50), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT (provider_name) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
    RETURNING provider_id INTO v_provider_id;

    -- news 테이블에 기사 정보 삽입/업데이트 (최대 255자 제한)
    INSERT INTO news (source_id, title, url, summary, published_at, created_at, updated_at)
    VALUES (
        v_provider_id,
        LEFT(NEW.title, 255),
        LEFT(NEW.url, 255),
        NULL,
        NEW.write_date,
        NEW.created_at,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (url) DO UPDATE SET
        source_id = EXCLUDED.source_id,
        title = EXCLUDED.title,
        published_at = EXCLUDED.published_at,
        updated_at = EXCLUDED.updated_at;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 바인딩 (INSERT 또는 UPDATE 발생 시 변환 로직 실행)
DROP TRIGGER IF EXISTS trigger_sync_news_article ON news_article;
CREATE TRIGGER trigger_sync_news_article
AFTER INSERT OR UPDATE ON news_article
FOR EACH ROW
EXECUTE FUNCTION sync_news_article_to_erd();

-- 7. ENUM 및 신규 12개 테이블 생성 (image_example2.png ERD 매핑)

-- 7-1. 옵션 타입 ENUM 생성
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'option_type_enum') THEN
        CREATE TYPE option_type_enum AS ENUM ('옵션해당사항없음', 'CALL', 'PUT', 'CALL+PUT');
    END IF;
END$$;

-- 7-2. 이자 타입 ENUM 생성
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'interest_type_enum') THEN
        CREATE TYPE interest_type_enum AS ENUM ('이표채', '복리채', '단리채', '할인채');
    END IF;
END$$;

-- 7-3. industry (산업) 테이블 생성
CREATE TABLE IF NOT EXISTS industry (
    industry_id BIGSERIAL PRIMARY KEY,
    industry_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 7-4. issuer (발행기관) 테이블 생성
CREATE TABLE IF NOT EXISTS issuer (
    issuer_id BIGSERIAL PRIMARY KEY,
    industry_id BIGINT NOT NULL REFERENCES industry(industry_id) ON DELETE CASCADE,
    issuer_name VARCHAR(100) NOT NULL,
    crno VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 7-5. bond_type (채권 종류) 테이블 생성
CREATE TABLE IF NOT EXISTS bond_type (
    bond_type_id BIGSERIAL PRIMARY KEY,
    bond_type VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 7-6. seniority (우선순위) 테이블 생성
CREATE TABLE IF NOT EXISTS seniority (
    seniority_id BIGSERIAL PRIMARY KEY,
    seniority_name VARCHAR(20) NOT NULL UNIQUE,
    priority_order BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 7-7. credit_rating (신용 등급) 테이블 생성
CREATE TABLE IF NOT EXISTS credit_rating (
    rating_id BIGSERIAL PRIMARY KEY,
    rating_name VARCHAR(30) NOT NULL UNIQUE,
    rating_order BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 7-8. guarantee_status (보증 여부) 테이블 생성
CREATE TABLE IF NOT EXISTS guarantee_status (
    guarantee_status_id BIGSERIAL PRIMARY KEY,
    guarantee_status VARCHAR(10) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 7-9. bond_option_exercise (옵션 행사 가능일 상세) 테이블 생성
CREATE TABLE IF NOT EXISTS bond_option_exercise (
    option_exercise_id BIGSERIAL PRIMARY KEY,
    option_type option_type_enum NOT NULL,
    exercise_start_date_1 DATE NULL,
    exercise_end_date_1 DATE NULL,
    exercise_start_date_2 DATE NULL,
    exercise_end_date_2 DATE NULL,
    exercise_reason TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 7-10. bond_cashflow_rule (이자 지급 상세 조건) 테이블 생성
CREATE TABLE IF NOT EXISTS bond_cashflow_rule (
    cashflow_rule_id BIGSERIAL PRIMARY KEY,
    interest_payment_method VARCHAR(255) NULL,
    interest_payment_unit_months VARCHAR(255) NULL,
    interest_calculation_months VARCHAR(255) NULL,
    interest_pre_post_type VARCHAR(255) NULL,
    first_interest_payment_date DATE NULL,
    interest_payment_basis VARCHAR(255) NULL,
    interest_month_end_type VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 7-11. bond (채권 마스터) 테이블 생성
CREATE TABLE IF NOT EXISTS bond (
    bond_id BIGSERIAL PRIMARY KEY,
    isin_code VARCHAR(255) NOT NULL UNIQUE,
    bond_type_id BIGINT NOT NULL REFERENCES bond_type(bond_type_id),
    short_code VARCHAR(255) NULL,
    bond_name VARCHAR(255) NOT NULL,
    short_name VARCHAR(255) NULL,
    issuer_id BIGINT NOT NULL REFERENCES issuer(issuer_id),
    issue_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    coupon_rate DECIMAL(10, 4) NOT NULL,
    issue_amount BIGINT NOT NULL,
    underwriter VARCHAR(255) NOT NULL,
    option_type option_type_enum NOT NULL,
    cashflow_rule_id BIGINT NULL REFERENCES bond_cashflow_rule(cashflow_rule_id) ON DELETE SET NULL,
    interest_type interest_type_enum NOT NULL,
    payment_cycle_months INT NOT NULL,
    maturity_redemption_rate DECIMAL(15, 2) NULL,
    redemption_method VARCHAR(255) NULL,
    early_redemption_description TEXT NULL,
    seniority_id BIGINT NOT NULL REFERENCES seniority(seniority_id),
    option_exercise_id BIGINT NOT NULL REFERENCES bond_option_exercise(option_exercise_id),
    guarantee_status_id BIGINT NOT NULL REFERENCES guarantee_status(guarantee_status_id),
    rating_id BIGINT NOT NULL REFERENCES credit_rating(rating_id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 7-12. users (사용자) 테이블 생성
CREATE TABLE IF NOT EXISTS users (
    user_id BIGSERIAL PRIMARY KEY,
    user_name VARCHAR(255) NULL,
    user_email VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 7-13. user_bond (사용자 채권 구매 정보) 테이블 생성
CREATE TABLE IF NOT EXISTS user_bond (
    user_bond_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    bond_id BIGINT NOT NULL REFERENCES bond(bond_id) ON DELETE CASCADE,
    purchase_price DECIMAL(15, 2) NOT NULL,
    purchase_date TIMESTAMP NULL,
    quantity BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 7-14. bond_market_data (채권 시장정보) 테이블 생성
CREATE TABLE IF NOT EXISTS bond_market_data (
    market_data_id BIGSERIAL PRIMARY KEY,
    bond_id BIGINT NOT NULL REFERENCES bond(bond_id) ON DELETE CASCADE,
    base_date DATE NOT NULL,
    price DECIMAL(15, 2) NULL,
    ytm DECIMAL(8, 3) NULL,
    duration DECIMAL(8, 4) NULL,
    spread DECIMAL(8, 7) NULL,
    trading_volume BIGINT NULL,
    substitute_price VARCHAR(255) NULL,
    bid_yield VARCHAR(255) NULL,
    ask_yield VARCHAR(255) NULL,
    price_change_rate VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    CONSTRAINT bond_market_data_unique UNIQUE(bond_id, base_date)
);

-- 8. 기초 기준정보(Seed Data) 적재

-- 8-1. bond_type 시드 데이터
INSERT INTO bond_type (bond_type) VALUES
('특수채'), ('금융채'), ('MBS'), ('지방채'), ('일반회사채'), ('지방공사채'), ('유동화SPC채'), ('유사집합투자기구채')
ON CONFLICT (bond_type) DO NOTHING;

-- 8-2. seniority 시드 데이터
INSERT INTO seniority (seniority_name, priority_order) VALUES
('선순위', 1),
('후순위', 2)
ON CONFLICT (seniority_name) DO NOTHING;

-- 8-3. guarantee_status 시드 데이터
INSERT INTO guarantee_status (guarantee_status) VALUES
('무보증'),
('보증')
ON CONFLICT (guarantee_status) DO NOTHING;

-- 8-4. credit_rating 시드 데이터
INSERT INTO credit_rating (rating_name, rating_order) VALUES
('AAA', 1), ('AA+', 2), ('AA0', 3), ('AA-', 4), ('A+', 5), ('A0', 6), ('A-', 7),
('BBB+', 8), ('BBB0', 9), ('BBB-', 10), ('BB+', 11), ('BB0', 12), ('BB-', 13),
('B+', 14), ('B0', 15), ('B-', 16), ('CCC', 17), ('CC', 18), ('C', 19), ('D', 20)
ON CONFLICT (rating_name) DO NOTHING;

-- 9. Staging 테이블에서 12개 정규화 테이블로 변환하는 PL/pgSQL 함수 생성
CREATE OR REPLACE FUNCTION normalize_bonds_staging()
RETURNS void AS $$
DECLARE
    r RECORD;
    v_industry_id BIGINT;
    v_issuer_id BIGINT;
    v_bond_type_id BIGINT;
    v_seniority_id BIGINT;
    v_guarantee_status_id BIGINT;
    v_rating_id BIGINT;
    v_option_exercise_id BIGINT;
    v_cashflow_rule_id BIGINT;
    v_option_type option_type_enum;
    v_interest_type interest_type_enum;
BEGIN
    -- 0. 기본 '기타' 산업군 생성
    INSERT INTO industry (industry_name) VALUES ('기타') ON CONFLICT (industry_name) DO NOTHING;

    -- 1. industry 적재
    INSERT INTO industry (industry_name)
    SELECT DISTINCT industry FROM temp_bonds_master_staging 
    WHERE industry IS NOT NULL AND industry != ''
    ON CONFLICT (industry_name) DO NOTHING;

    -- 2. issuer 적재 (산업군 미매핑 시 '기타'로 매핑)
    INSERT INTO issuer (industry_id, issuer_name, crno)
    SELECT DISTINCT ON (s.company_id)
        COALESCE(i.industry_id, (SELECT industry_id FROM industry WHERE industry_name = '기타')), 
        s.company_name, 
        s.company_id
    FROM temp_bonds_master_staging s
    LEFT JOIN industry i ON s.industry = i.industry_name
    WHERE s.company_name IS NOT NULL AND s.company_id IS NOT NULL AND s.company_id != ''
    ORDER BY s.company_id, s.company_name DESC
    ON CONFLICT (crno) DO UPDATE SET issuer_name = EXCLUDED.issuer_name, industry_id = EXCLUDED.industry_id;

    -- 3. 개별 채권 로프 돌며 정규화 및 적재
    FOR r IN SELECT * FROM temp_bonds_master_staging LOOP
        -- 산업 ID 조회
        SELECT industry_id INTO v_industry_id FROM industry WHERE industry_name = r.industry;
        IF v_industry_id IS NULL THEN
            SELECT industry_id INTO v_industry_id FROM industry WHERE industry_name = '기타';
        END IF;

        -- 발행기관 ID 조회
        SELECT issuer_id INTO v_issuer_id FROM issuer WHERE crno = r.company_id;
        
        -- 발행기관이 없을 경우 폴백 처리 (기타 산업군으로 신규 생성)
        IF v_issuer_id IS NULL THEN
            INSERT INTO issuer (industry_id, issuer_name, crno)
            VALUES (
                v_industry_id,
                COALESCE(r.company_name, '미분류 발행기관'),
                COALESCE(NULLIF(r.company_id, ''), 'UNKNOWN_' || r.isin_code)
            )
            ON CONFLICT (crno) DO UPDATE SET issuer_name = EXCLUDED.issuer_name
            RETURNING issuer_id INTO v_issuer_id;
        END IF;
        
        -- 채권 분류 ID 조회 (기본값 설정)
        SELECT bond_type_id INTO v_bond_type_id FROM bond_type WHERE bond_type = r.bond_type;
        IF v_bond_type_id IS NULL THEN
            SELECT bond_type_id INTO v_bond_type_id FROM bond_type WHERE bond_type = '일반회사채';
        END IF;

        -- 우선순위 ID 조회
        SELECT seniority_id INTO v_seniority_id FROM seniority WHERE seniority_name = r.seniority;
        IF v_seniority_id IS NULL THEN
            SELECT seniority_id INTO v_seniority_id FROM seniority WHERE seniority_name = '선순위';
        END IF;

        -- 보증 여부 ID 조회
        SELECT guarantee_status_id INTO v_guarantee_status_id FROM guarantee_status WHERE guarantee_status = r.guarantee_status;
        IF v_guarantee_status_id IS NULL THEN
            SELECT guarantee_status_id INTO v_guarantee_status_id FROM guarantee_status WHERE guarantee_status = '무보증';
        END IF;

        -- 신용등급 ID 조회
        SELECT rating_id INTO v_rating_id FROM credit_rating WHERE rating_name = r.credit_rating;
        IF v_rating_id IS NULL THEN
            SELECT rating_id INTO v_rating_id FROM credit_rating WHERE rating_name = 'BBB-';
        END IF;

        -- 옵션 타입 매핑
        v_option_type := '옵션해당사항없음';
        IF r.call_put_option = 'CALL' THEN v_option_type := 'CALL';
        ELSIF r.call_put_option = 'PUT' THEN v_option_type := 'PUT';
        ELSIF r.call_put_option = 'CALL+PUT' THEN v_option_type := 'CALL+PUT';
        END IF;

        -- 이자 타입 매핑
        v_interest_type := '이표채';
        IF r.interest_type = '복리채' THEN v_interest_type := '복리채';
        ELSIF r.interest_type = '단리채' THEN v_interest_type := '단리채';
        ELSIF r.interest_type = '할인채' THEN v_interest_type := '할인채';
        END IF;

        -- 기존 Bond가 있는지 확인
        SELECT option_exercise_id, cashflow_rule_id INTO v_option_exercise_id, v_cashflow_rule_id 
        FROM bond WHERE isin_code = r.isin_code;

        -- 없으면 OptionExercise 및 CashflowRule 플레이스홀더 레코드 생성
        IF v_option_exercise_id IS NULL THEN
            INSERT INTO bond_option_exercise (option_type) VALUES (v_option_type) RETURNING option_exercise_id INTO v_option_exercise_id;
        ELSE
            UPDATE bond_option_exercise SET option_type = v_option_type WHERE option_exercise_id = v_option_exercise_id;
        END IF;

        IF v_cashflow_rule_id IS NULL THEN
            INSERT INTO bond_cashflow_rule (interest_payment_method) VALUES (r.interest_type) RETURNING cashflow_rule_id INTO v_cashflow_rule_id;
        END IF;

        -- bond 테이블 적재 (UPSERT)
        INSERT INTO bond (
            isin_code, bond_type_id, bond_name, issuer_id, issue_date, maturity_date, 
            coupon_rate, issue_amount, underwriter, option_type, cashflow_rule_id, 
            interest_type, payment_cycle_months, seniority_id, option_exercise_id, 
            guarantee_status_id, rating_id
        ) VALUES (
            r.isin_code, v_bond_type_id, r.bond_name, v_issuer_id, r.issue_date, r.maturity_date,
            r.coupon_rate, r.issue_amount, r.underwriter, v_option_type, v_cashflow_rule_id,
            v_interest_type, COALESCE(NULLIF(regexp_replace(r.payment_cycle, '[^0-9]', '', 'g'), '')::INT, 3), 
            v_seniority_id, v_option_exercise_id, v_guarantee_status_id, v_rating_id
        )
        ON CONFLICT (isin_code) DO UPDATE SET
            bond_type_id = EXCLUDED.bond_type_id,
            bond_name = EXCLUDED.bond_name,
            issuer_id = EXCLUDED.issuer_id,
            issue_date = EXCLUDED.issue_date,
            maturity_date = EXCLUDED.maturity_date,
            coupon_rate = EXCLUDED.coupon_rate,
            issue_amount = EXCLUDED.issue_amount,
            underwriter = EXCLUDED.underwriter,
            option_type = EXCLUDED.option_type,
            interest_type = EXCLUDED.interest_type,
            payment_cycle_months = EXCLUDED.payment_cycle_months,
            seniority_id = EXCLUDED.seniority_id,
            guarantee_status_id = EXCLUDED.guarantee_status_id,
            rating_id = EXCLUDED.rating_id,
            updated_at = CURRENT_TIMESTAMP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 10. 현재 존재하는 객체에 대한 권한 부여
-- 위에서 생성한 테이블과 관련 시퀀스에도 적용됨
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ssafyuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ssafyuser;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO ssafyuser;
