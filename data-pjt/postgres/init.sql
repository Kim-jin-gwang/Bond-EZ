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
    title VARCHAR(200) NOT NULL,
    writer VARCHAR(255) NOT NULL,
    write_date TIMESTAMP NOT NULL,
    category VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    url VARCHAR(200) UNIQUE NOT NULL,
    keywords JSON DEFAULT '[]'::json,
    embedding VECTOR(1536) NULL
);


-- 6. 현재 존재하는 객체에 대한 권한 부여
-- 위에서 생성한 news_article 테이블과 관련 시퀀스에도 적용됨
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ssafyuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ssafyuser;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO ssafyuser;
