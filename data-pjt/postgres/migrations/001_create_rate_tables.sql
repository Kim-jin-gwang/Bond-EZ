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

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ssafyuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ssafyuser;
