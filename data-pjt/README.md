# SSAFY 맞춤형 서비스 데이터 파이프라인 환경 설정 관통 PJT 가이드 예시

## 최종 목표

```text
[Extract]                   [Transform]              [Load / Serve]
Kafka Topic  →  Flink  →  데이터 처리/변환    →  PostgreSQL(DB 저장)
(JSON or RSS) (스트리밍)  (카테고리 분류)     →  Elasticsearch(검색)
                  │        (키워드 추출)      
                  │        (벡터 임베딩)
                  │
                  ↓            
                HDFS  →  Spark  →  리포트 생성
              (레이크)   (배치)       (PDF)
                                →  집계/분석 결과 HDFS 저장
                                    (분석 결과 저장소 / DW 대체 역할)
```

본 프로젝트는 Kafka, Flink, PostgreSQL, Elasticsearch, HDFS, Spark 등을 연결하여 데이터 수집부터 저장, 검색, 배치 분석까지 이어지는 데이터 파이프라인 구조를 구성하는 것을 목표로 합니다.

PostgreSQL은 컨텐츠 데이터를 저장하는 DB 역할을 하며, `pgvector` 확장을 사용하여 벡터 임베딩 데이터도 함께 저장할 수 있도록 구성합니다.

---

## 1. PostgreSQL 설정 방식 선택 기준

PostgreSQL은 로컬 Linux 환경에 직접 설치할 수도 있고, Docker Compose를 사용하여 컨테이너로 실행할 수도 있습니다.

이번 프로젝트처럼 Kafka, Flink, PostgreSQL, Elasticsearch 등 여러 서비스를 함께 실행하고 연결해야 하는 경우에는 Docker Compose 방식을 권장합니다.

| 방식 | 적합한 경우 | 특징 |
|---|---|---|
| 로컬 PostgreSQL 설치 | PostgreSQL만 단독으로 실습할 때 | OS에 직접 설치하므로 서비스 관리가 필요함 |
| Docker Compose 방식 | Kafka, Flink, PostgreSQL 등 여러 컨테이너를 함께 사용할 때 | 하나의 Docker 네트워크에서 컨테이너 이름으로 통신 가능 |

Docker Compose를 사용하면 여러 서비스를 같은 네트워크에 연결할 수 있습니다.

예를 들어 같은 Docker 네트워크 안에서는 다음과 같이 컨테이너 이름을 주소처럼 사용할 수 있습니다.

```text
Kafka          → kafka:9092
PostgreSQL     → postgres:5432
Elasticsearch  → elasticsearch:9200
```

단, 이 방식은 기본적으로 하나의 Docker 호스트 안에서 동작하는 구조입니다.

여러 서버에 나누어 배포하는 운영 환경에서는 서버 IP, 도메인, Kubernetes Service 등의 방식으로 네트워크를 구성해야 합니다.

---

## 2. 로컬 PostgreSQL 설치 및 설정

이 방식은 PostgreSQL을 Linux 환경에 직접 설치하는 방법입니다.

PostgreSQL만 단독으로 실습하거나, Docker를 사용하지 않는 환경에서 사용할 수 있습니다.

### 2.1. 로컬 PostgreSQL 설치 Linux - Ubuntu

1. PostgreSQL 저장소를 추가합니다.

```bash
echo "deb http://apt.postgresql.org/pub/repos/apt jammy-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list

wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

sudo apt-get update
```

2. PostgreSQL 16과 pgvector 패키지를 설치합니다.

```bash
sudo apt install -y postgresql-16 postgresql-contrib-16 postgresql-16-pgvector
```

3. 서비스 상태를 확인합니다.

```bash
sudo service postgresql status
```

### 2.2. 로컬 PostgreSQL 데이터베이스 설정

1. PostgreSQL 관리자 계정으로 접속합니다.

```bash
sudo -i -u postgres
psql
```

2. 데이터베이스를 생성합니다.

```sql
CREATE DATABASE news;
```

3. 사용자를 생성하고 데이터베이스 권한을 부여합니다.

```sql
CREATE USER ssafyuser WITH PASSWORD 'ssafy';
GRANT ALL PRIVILEGES ON DATABASE news TO ssafyuser;
```

4. 생성한 데이터베이스로 접속합니다.

```sql
\c news
```

5. pgvector 확장을 활성화합니다.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

6. 뉴스 기사 저장 테이블을 생성합니다.

```sql
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
```

7. 기존 객체와 앞으로 생성될 객체에 대한 권한을 부여합니다.

```sql
-- public 스키마 접근 및 생성 권한
GRANT USAGE ON SCHEMA public TO ssafyuser;
GRANT CREATE ON SCHEMA public TO ssafyuser;

-- 기존 테이블 및 시퀀스 권한
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ssafyuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ssafyuser;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO ssafyuser;

-- 앞으로 생성될 객체의 기본 권한
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO ssafyuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO ssafyuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO ssafyuser;
```

8. 종료
```bash
sudo service postgresql stop
```

---

## 3. Docker Compose 기반 PostgreSQL 설정

이 방식은 PostgreSQL을 로컬 OS에 직접 설치하지 않고, Docker Compose를 사용하여 실행하는 방법입니다.

PostgreSQL에는 벡터 임베딩 데이터를 저장하기 위해 `pgvector` 확장이 필요합니다.

따라서 일반 `postgres` 이미지가 아니라 `pgvector`가 포함된 이미지를 사용합니다.

### 3.1. 디렉터리 구조 예시

프로젝트 디렉터리는 다음과 같이 구성합니다.

```text
de_pjt/
├── docker-compose.yml
├── postgres/
│   └── init.sql
├── requirements.txt
└── ...
```

`postgres/init.sql` 파일은 PostgreSQL 컨테이너가 처음 실행될 때 자동으로 실행되는 초기화 SQL 파일입니다.

---

### 3.2. Docker 네트워크 생성

현재 Docker Compose 설정에서는 `de_net`이라는 외부 네트워크를 사용합니다.

Kafka, Flink, PostgreSQL 등 여러 컨테이너가 같은 네트워크에서 통신할 수 있도록 최초 1회 네트워크를 생성합니다.

```bash
docker network create de_net
```

이미 생성된 네트워크가 있는지 확인하려면 다음 명령어를 사용합니다.

```bash
docker network ls
```

이미 `de_net`이 존재한다면 다시 생성하지 않아도 됩니다.

---

### 3.3. PostgreSQL 서비스 추가

`docker-compose.yml` 파일에 PostgreSQL 서비스를 추가합니다.

```yaml
services:
  postgres:
    container_name: postgres
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: news
      POSTGRES_USER: ssafyuser
      POSTGRES_PASSWORD: ssafy
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - de_net

volumes:
  postgres_data:

networks:
  de_net:
    external: true
```

기존 Kafka, Zookeeper 설정이 이미 있다면 `services:` 아래에 `postgres` 서비스만 추가하고, 하단에 `volumes` 설정을 추가하면 됩니다.

예를 들어 Kafka, Zookeeper와 함께 사용하는 경우 전체 구조는 다음과 같습니다.

```yaml
services:
  zookeeper:
    container_name: zookeeper
    image: confluentinc/cp-zookeeper:7.5.0
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    networks:
      - de_net

  kafka:
    container_name: kafka
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
      - "29092:29092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181

      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,PLAINTEXT_HOST://0.0.0.0:29092
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:29092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    depends_on:
      - zookeeper
    networks:
      - de_net

  postgres:
    container_name: postgres
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: news
      POSTGRES_USER: ssafyuser
      POSTGRES_PASSWORD: ssafy
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - de_net

volumes:
  postgres_data:

networks:
  de_net:
    external: true
```

### 3.4. PostgreSQL 설정 설명

```yaml
image: pgvector/pgvector:pg16
```

`pgvector` 확장이 포함된 PostgreSQL 16 이미지를 사용합니다.

이 이미지를 사용하면 `VECTOR(1536)`과 같은 벡터 타입을 사용할 수 있습니다.

```yaml
POSTGRES_DB: news
POSTGRES_USER: ssafyuser
POSTGRES_PASSWORD: ssafy
```

컨테이너가 처음 실행될 때 다음 항목을 자동으로 생성합니다.

```text
데이터베이스: news
사용자: ssafyuser
비밀번호: ssafy
```

즉, 기존에 수동으로 실행했던 아래 SQL은 Docker Compose 환경변수로 대체됩니다.

```sql
CREATE DATABASE news;
CREATE USER ssafyuser WITH PASSWORD 'ssafy';
```

```yaml
./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
```

`postgres/init.sql` 파일을 PostgreSQL 컨테이너의 초기화 SQL 경로에 연결합니다.

이 파일은 PostgreSQL 데이터 볼륨이 처음 생성될 때 자동 실행됩니다.

따라서 `pgvector` 확장 설치, 테이블 생성, 권한 설정을 이 파일에서 처리할 수 있습니다.

---

## 4. PostgreSQL 초기화 SQL 작성

먼저 `postgres` 디렉터리와 `init.sql` 파일을 생성합니다.

```bash
mkdir -p postgres
touch postgres/init.sql
```

이후 `postgres/init.sql` 파일에 다음 내용을 작성합니다.

```sql
-- init.sql
-- PostgreSQL + pgvector 초기 설정
--
-- 목적:
--   1. pgvector 확장 활성화
--   2. ssafyuser가 public 스키마에서 실습에 필요한 작업을 수행할 수 있도록 권한 설정
--   3. news_article 테이블 생성
--
-- 주의:
--   이 파일은 PostgreSQL 데이터 볼륨이 처음 생성될 때 1회만 실행됨


-- 1. pgvector 확장 활성화
-- embedding VECTOR 타입을 사용하기 위해 필요
CREATE EXTENSION IF NOT EXISTS vector;


-- 2. public 스키마 권한 부여
-- ssafyuser가 public 스키마 안에서 객체를 조회하고 생성할 수 있도록 설정
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


-- 4. 앞으로 postgres 사용자가 생성하는 객체에 대한 기본 권한 설정
-- 나중에 postgres 계정으로 테이블을 만들더라도 ssafyuser가 접근할 수 있도록 설정
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
GRANT ALL PRIVILEGES ON TABLES TO ssafyuser;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
GRANT ALL PRIVILEGES ON SEQUENCES TO ssafyuser;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
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
```

### 4.1. 권한 설정 의미

위 설정을 적용하면 `ssafyuser`는 `news` 데이터베이스의 `public` 스키마에서 실습에 필요한 작업을 수행할 수 있습니다.

가능한 작업 예시는 다음과 같습니다.

```sql
CREATE TABLE ...
INSERT INTO ...
SELECT ...
UPDATE ...
DELETE ...
CREATE INDEX ...
DROP TABLE ...
```

즉, 실습 중 새로운 테이블을 생성하거나 삭제하고, 데이터를 삽입하거나 조회하는 작업을 진행할 수 있습니다.

다만 `ssafyuser`는 PostgreSQL 전체 관리자 계정은 아닙니다.

따라서 다음과 같은 서버 관리자 작업은 제한될 수 있습니다.

```sql
CREATE DATABASE ...
CREATE USER ...
ALTER SYSTEM ...
```

해당 프로젝트에서는 일반적으로 `news` 데이터베이스 내부에서 테이블 생성, 데이터 적재, 조회, 수정, 삭제 권한이면 충분합니다.

---

## 5. PostgreSQL 실행 및 접속 확인

### 5.1. Docker Compose 실행

```bash
docker compose up -d
```

실행 중인 컨테이너를 확인합니다.

```bash
docker ps
```

다음 컨테이너가 실행 중이면 정상입니다.

```text
zookeeper
kafka
postgres
```

---

### 5.2. PostgreSQL 접속

PostgreSQL 컨테이너에 접속합니다.

```bash
docker exec -it postgres psql -U ssafyuser -d news
```

현재 접속한 데이터베이스를 확인합니다.

```sql
SELECT current_database();
```

현재 사용자를 확인합니다.

```sql
SELECT current_user;
```

---

### 5.3. pgvector 확장 확인

```sql
\dx
```

또는 다음 SQL로 확인할 수 있습니다.

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

`vector` 확장이 조회되면 정상입니다.

### 5.4. 테이블 확인

```sql
\dt
```

`news_article` 테이블이 보이면 정상입니다.

### 5.5. 테이블 생성 권한 테스트

`ssafyuser`가 앞으로도 테이블을 생성할 수 있는지 확인합니다.

```sql
CREATE TABLE test_table (
    id SERIAL PRIMARY KEY,
    name TEXT
);
```

데이터를 삽입합니다.

```sql
INSERT INTO test_table (name)
VALUES ('test');
```

데이터를 조회합니다.

```sql
SELECT * FROM test_table;
```

테스트가 끝나면 테이블을 삭제합니다.

```sql
DROP TABLE test_table;
```

위 작업이 모두 정상 실행되면 PostgreSQL 실습 권한 설정이 완료된 것입니다.

---

## 6. 접속 정보 정리

### 6.1. 호스트 PC에서 접속할 때

Python, DBeaver, pgAdmin 등 로컬 PC에서 PostgreSQL에 접속할 때는 다음 정보를 사용합니다.

```text
Host: localhost
Port: 5432
Database: news
User: ssafyuser
Password: ssafy
```

Python 코드에서 사용할 경우 예시는 다음과 같습니다.

```text
postgresql://ssafyuser:ssafy@localhost:5432/news
```

---

### 6.2. Docker 컨테이너 내부에서 접속할 때

Flink, Spark, Airflow, Django 등이 같은 `de_net` 네트워크에 연결되어 있다면 `localhost`가 아니라 컨테이너 이름을 사용합니다.

```text
Host: postgres
Port: 5432
Database: news
User: ssafyuser
Password: ssafy
```

컨테이너 내부에서 사용할 접속 URL 예시는 다음과 같습니다.

```text
postgresql://ssafyuser:ssafy@postgres:5432/news
```

Kafka도 같은 방식으로 구분합니다.

호스트 PC에서 Kafka에 접속할 때

```text
localhost:29092
```

Docker 컨테이너 내부에서 Kafka에 접속할 때

```text
kafka:9092
```

---

## 7. init.sql 수정 시 주의사항

`postgres/init.sql` 파일은 PostgreSQL 데이터 볼륨이 처음 생성될 때만 자동 실행됩니다.

따라서 이미 한 번 컨테이너를 실행한 뒤 `init.sql`을 수정해도 자동으로 다시 실행되지 않습니다.

초기 실습 단계에서 DB를 완전히 초기화하고 다시 실행하려면 다음 명령어를 사용합니다.

```bash
docker compose down -v
docker compose up -d
```

단, `docker compose down -v`를 실행하면 PostgreSQL 데이터 볼륨도 삭제됩니다.

즉, 기존에 저장된 데이터도 함께 삭제됩니다.

이미 중요한 데이터가 저장된 상태라면 먼저 백업하거나, 컨테이너에 직접 접속하여 변경 SQL을 수동으로 실행해야 합니다.

---

## 8. 필요한 라이브러리 설치 예시

Python 가상환경을 생성합니다.

```bash
python3.10 -m venv ~/venvs/data-pjt
source ~/venvs/data-pjt/bin/activate
```

필요한 라이브러리를 설치합니다.

```bash
pip install -r requirements.txt
```

### 8.1. 금리/예금금리 적재 스크립트 실행

`producer/interest_rate_loader.py`는 ECOS 기준금리/국고채 금리, FRED 미국 기준금리/미국채 금리, 금융감독원 12개월 예금상품 금리를 PostgreSQL에 적재합니다.

`.env`에 다음 값을 설정합니다.

```text
ECOS_API_KEY=한국은행_ECOS_API_KEY
FSS_API_KEY=금융감독원_금융상품통합비교공시_API_KEY
POSTGRES_DB=bonds_db
POSTGRES_USER=ssafyuser
POSTGRES_PASSWORD=ssafy
DB_HOST=localhost
DB_PORT=5432
```

호스트 PC에서 실행할 때는 다음 명령을 사용합니다.

```bash
python producer/interest_rate_loader.py --only all
```

기준금리/국채금리를 10년치 기간 데이터로 다시 적재하려면 다음 명령을 사용합니다.

```bash
python producer/interest_rate_loader.py --only base-rate --days-back 3650
```

위 명령은 한국 데이터는 ECOS, 미국 데이터는 FRED에서 가져옵니다. 미국 금리는 `DFF`(연방기금금리), `DGS3`(미국채 3년물), `DGS10`(미국채 10년물)을 사용하며, `BaseRate`에는 국가별/기준일별로 적재됩니다.

예금상품 금리만 적재하려면 다음 명령을 사용합니다.

```bash
python producer/interest_rate_loader.py --only deposit-rate
```

금리와 예금상품 금리를 모두 적재하려면 다음 명령을 사용합니다.

```bash
python producer/interest_rate_loader.py --only all --days-back 3650
```

이미 생성된 DB에 기간 데이터를 넣기 전에는 `BaseRate` 테이블에 기준일 컬럼을 추가해야 합니다.

```bash
docker exec -i postgres psql -U ssafyuser -d bonds_db < data-pjt/postgres/migrations/002_base_rate_history.sql
```

컨테이너 내부에서 실행할 때는 `DB_HOST=db`를 사용합니다.

### 8.2. Airflow 매일 자동 업데이트

`interest_rate_daily_update_dag`는 매일 오전 7시(Asia/Seoul)에 최근 14일 금리 데이터와 예금상품 금리를 다시 적재합니다. 최근 14일을 조회하는 이유는 미국 FRED/Fed 데이터가 영업일 기준으로 늦게 공개될 수 있어 누락된 날짜를 upsert로 보완하기 위해서입니다.

Airflow 실행 전 `.env`에 `ECOS_API_KEY`, `FSS_API_KEY`가 설정되어 있어야 합니다. 이미 생성된 DB라면 `BaseRate` 기간 적재용 migration도 먼저 적용합니다.

```bash
docker exec -i postgres psql -U ssafyuser -d bonds_db < data-pjt/postgres/migrations/002_base_rate_history.sql
```

Airflow를 실행합니다.

```bash
docker compose up -d airflow-init airflow-webserver airflow-scheduler
```

Airflow UI는 기본 설정 기준 `http://localhost:8081`에서 확인할 수 있습니다. DAG 목록에서 `interest_rate_daily_update_dag`를 활성화하거나 수동 실행하면 됩니다.

예를 들어 PostgreSQL, Kafka, RSS, HTML 파싱 등을 사용할 경우 `requirements.txt`에는 다음과 같은 라이브러리가 포함될 수 있습니다.

```text
kafka-python
feedparser
requests
beautifulsoup4
psycopg2-binary
python-dotenv
```

---

## 9. 참고: 수동 설정과 Docker 설정의 차이

수동으로 실행하던 아래 SQL은 Docker 방식에서는 직접 실행하지 않아도 됩니다.

```sql
CREATE DATABASE news;
CREATE USER ssafyuser WITH PASSWORD 'ssafy';
GRANT ALL PRIVILEGES ON DATABASE news TO ssafyuser;
```

이 작업은 Docker Compose의 아래 환경변수가 대신 처리합니다.

```yaml
POSTGRES_DB: news
POSTGRES_USER: ssafyuser
POSTGRES_PASSWORD: ssafy
```

Docker 방식에서는 데이터베이스와 사용자는 환경변수로 생성하고, 확장 설치와 테이블 생성, 세부 권한 설정은 `postgres/init.sql`에서 처리합니다.

---

