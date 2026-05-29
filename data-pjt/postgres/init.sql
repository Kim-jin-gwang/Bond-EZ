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


-- 5. news_article 테이블 생성
CREATE TABLE IF NOT EXISTS news_article (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    source VARCHAR(100) NOT NULL,
    url VARCHAR(500) UNIQUE NOT NULL,
    write_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 현재 존재하는 객체에 대한 권한 부여
-- 위에서 생성한 테이블과 관련 시퀀스에도 적용됨
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ssafyuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ssafyuser;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO ssafyuser;
