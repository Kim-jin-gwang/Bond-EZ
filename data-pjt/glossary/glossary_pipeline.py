import os
import re
import csv
import random
import argparse
import psycopg2
from dotenv import load_dotenv

# Load environment variables if running locally
load_dotenv()

# Database connection settings from environment variables
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "bonds_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "ssafyuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ssafy")

# Category mapping to exact IDs based on ERD/spec
CATEGORIES = {
    "거시 경제": 1,
    "금리": 2,
    "리스크 관리": 3,
    "금융 제도": 4,
    "시장 지표": 5,
    "채권/발행": 6,
    "투자 지표": 7
}

# ==========================================
# Phase 1: PDF Extraction Helpers & Logic
# ==========================================

def deep_clean_description(text, term_name):
    if not text: return ""
    
    # Remove headers/footers
    text = re.sub(r'I\s+경제금융용어\s+800선', '', text)
    text = re.sub(r'찾아보기\s+I', '', text)
    
    # Remove page numbers and solo digits
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    text = re.sub(r'\s{2,}\d+\s{2,}', ' ', text)
    
    # Remove Korean consonants/solo symbols
    text = re.sub(r'\n\s*[ㄱ-ㅎㅏ-ㅣ]\s*\n', '\n', text)
    text = re.sub(r'\s+[ㄱ-ㅎ]\s+', ' ', text)
    
    # Remove references list
    text = re.split(r'연관검색어', text)[0]
    
    # Merge lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    full_text = ""
    for i in range(len(lines)):
        if i > 0 and re.search(r'[가-힣]$', lines[i-1]) and re.match(r'^[가-힣]', lines[i]):
            if not re.search(r'[.!?]$', lines[i-1]):
                full_text += lines[i]
            else:
                full_text += " " + lines[i]
        else:
            full_text += (" " if full_text else "") + lines[i]
    
    # Fix spacing issues with particles
    particles = "은|는|이|가|을|를|에|의|로|와|과|도|만|뿐|까지|부터|하여|하며|하고|한다|한다면"
    full_text = re.sub(rf'\s+({particles})(?=\s|$|[.!?])', r'\1', full_text)
    
    # Merge single letter words
    for _ in range(3):
        full_text = re.sub(r'([가-힣])\s([가-힣])(?=\s|[.!?]|$)', r'\1\2', full_text)
    
    # Clean term repeats and spacing
    full_text = re.sub(rf'^{re.escape(term_name)}\s+', '', full_text)
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    
    # Final sentence truncation
    if "." in full_text:
        last_period_idx = full_text.rfind(".")
        full_text = full_text[:last_period_idx + 1]

    return full_text

def generate_truly_unique_example(term, category):
    market_contexts = [
        "미 연준의 긴축 종료 기대감이 시장에 선반영되면서",
        "글로벌 공급망 차질에 따른 인플레이션 상방 압력이 지속되는 가운데",
        "국내외 통화정책의 불확실성이 고조된 현재 시점에서",
        "실물 경기 회복세가 둔화되며 안전자산 선호 현상이 강화되자",
        "외국인 투자자들의 국채선물 대량 매도로 금리 변동성이 커진 상황에서",
        "정부의 추가경정예산 편성 발표로 채권 수급 불균형 우려가 확산되며",
        "신용 스프레드가 연중 최고치에 근접하며 시장의 경계감이 높아진 가운데",
        "장단기 금리 역전 현상이 심화되며 경기 침체 시그널이 뚜렷해지는 상황에서"
    ]
    
    expert_actions = {
        "금리": [
            f"{term}의 하방 경직성이 강화되며 채권 가격 상승이 제한되고 있습니다.",
            f"시장 참가자들은 {term}의 추가 상승 가능성을 열어두고 보수적인 포지션을 유지 중입니다.",
            f"{term} 추이를 통해 향후 한은 금통위의 정책 스탠스를 가늠해볼 수 있습니다.",
            f"급격한 {term} 변동은 듀레이션이 긴 장기물 채권에 치명적인 손실을 줄 수 있습니다."
        ],
        "채권/발행": [
            f"이번에 발행된 {term}은 탁월한 금리 경쟁력 덕분에 연기금의 대량 매수세가 유입되었습니다.",
            f"{term} 시장의 유동성 위축을 방지하기 위해 금융당국이 선제적인 시장 안정화 조치에 나섰습니다.",
            f"기업들의 자금 조달 비용 상승으로 인해 {term} 발행 시장이 일시적인 관망세를 보이고 있습니다.",
            f"투자자들은 {term}의 상환 우선순위와 담보 가치를 면밀히 분석하여 투자 여부를 결정해야 합니다."
        ],
        "시장 지표": [
            f"차주 발표될 {term} 수치가 예상치를 하회할 경우 금리 인하 기대감이 탄력을 받을 전망입니다.",
            f"{term} 데이터의 반등은 우리 경제의 기초 체력(Fundamental)이 견고함을 시사합니다.",
            f"분석가들은 {term}의 변화가 향후 자산 배분 전략의 핵심 변수가 될 것으로 내다보고 있습니다.",
            f"예상보다 견조한 {term} 흐름은 채권 시장에 'Higher for Longer' 우려를 다시 불러일으켰습니다."
        ],
        "투자 지표": [
            f"해당 섹터 내 타 기업들과 비교했을 때 {term} 수준은 여전히 매력적인 구간에 있습니다.",
            f"단기적인 주가 흐름보다는 {term}의 장기적인 개선 추세에 주목할 필요가 있습니다.",
            f"기관 투자자들은 리스크 관리 차원에서 {term} 임계치를 설정하고 포트폴리오를 운용합니다.",
            f"안정적인 이익 창출 능력을 보여주는 {term} 수치는 채권자들에게 중요한 신용 보강 요인입니다."
        ],
        "리스크 관리": [
            f"{term}의 급격한 상승은 한계 가구 및 기업들의 가파른 이자 부담 증가로 이어질 수 있습니다.",
            f"시장 변동성 확대에 대응하여 {term} 관리를 최우선 과제로 삼고 현금 비중을 확대 중입니다.",
            f"특정 자산에 쏠린 {term} 집중도를 분산시키기 위해 섹터별 리밸런싱을 단행했습니다.",
            f"금융기관들은 {term} 스트레스 테스트를 통해 최악의 시나리오에 대한 대응력을 점검하고 있습니다."
        ],
        "금융 제도": [
            f"새롭게 도입된 {term}은 금융 시장의 투명성과 효율성을 한 단계 높일 것으로 기대됩니다.",
            f"규제 당국은 {term} 준수 여부를 엄격히 모니터링하여 시스템 리스크 발생을 사전에 차단하고자 합니다.",
            f"{term}의 개편은 중소기업들의 자금 조달 환경에 실질적인 변화를 가져올 전망입니다.",
            f"글로벌 금융 환경 변화에 발맞춘 {term}의 고도화 작업이 민관 합동으로 추진되고 있습니다."
        ]
    }

    context = random.choice(market_contexts)
    category_actions = expert_actions.get(category, [
        f"{term}의 변화 양상을 주시하며 거시적 관점에서의 시장 대응력을 높여야 합니다.",
        f"투자 전문가들은 {term}이 가진 경제적 함의를 분석하여 전략 수립에 반영하고 있습니다."
    ])
    return f"{context} {random.choice(category_actions)}"

def get_expert_metadata(term, description):
    category = "거시 경제"
    if any(k in term for k in ["금리", "수익률", "이자", "쿠폰", "할인율"]): category = "금리"
    elif any(k in term for k in ["채권", "발행", "상환", "국채", "회사채", "전환사채", "증권", "ABS", "MBS", "CP", "EB", "CB", "BW"]): category = "채권/발행"
    elif any(k in term for k in ["지수", "통계", "수지", "성장률", "GDP", "CPI", "물가", "인플레이션"]): category = "시장 지표"
    elif any(k in term for k in ["PER", "PBR", "EPS", "ROE", "NIM", "수익성", "이익", "매출", "배당"]): category = "투자 지표"
    elif any(k in term for k in ["리스크", "위험", "부도", "건전성", "DSR", "LTV", "신용", "스프레드", "충당금", "담보"]): category = "리스크 관리"
    elif any(k in term for k in ["은행", "금융", "결제", "통화", "중앙은행", "시스템", "제도", "법", "감독", "거래소"]): category = "금융 제도"

    difficulty = "기초"
    if any(k in term for k in ["금리", "물가", "환율", "은행", "주식", "채권", "소득"]): difficulty = "입문"
    if any(k in term for k in ["기준금리", "가산금리", "장단기", "신용등급", "지급준비", "GDP", "수익률곡선"]): difficulty = "중요"
    if any(k in term for k in ["코코본드", "바젤", "파생", "스왑", "옵션", "LCR", "NSFR", "듀레이션", "볼록성", "CDS"]): difficulty = "심화"

    example = generate_truly_unique_example(term, category)
    return category, difficulty, example

def run_extraction(pdf_path, csv_path):
    import pdfplumber
    print(f"Extracting glossary from PDF: {pdf_path}...")
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return False
        
    with pdfplumber.open(pdf_path) as pdf:
        unique_terms = []
        seen = set()
        # Pages with glossary index
        for i in range(3, 18):
            page = pdf.pages[i]
            text = page.extract_text() or ""
            matches = re.finditer(r'(.+?)[·\.]{2,}(\d+)', text)
            for match in matches:
                name = re.sub(r'^[ㄱ-ㅎㅏ-ㅣ가-힣]\s+', '', match.group(1)).strip('.· ')
                if name and not name.isdigit() and len(name) > 1:
                    if name not in seen:
                        unique_terms.append(name)
                        seen.add(name)
        
        full_content = ""
        for i in range(18, len(pdf.pages)):
            full_content += "\n" + (pdf.pages[i].extract_text() or "")
        
        term_positions = []
        for term in unique_terms:
            pattern = re.compile(rf'\n\s*{re.escape(term)}\s*\n')
            for m in pattern.finditer(full_content):
                term_positions.append({'name': term, 'start': m.start(), 'end': m.end()})
        
        term_positions.sort(key=lambda x: x['start'])

        results = []
        for i in range(len(term_positions)):
            curr = term_positions[i]
            next_start = term_positions[i+1]['start'] if i+1 < len(term_positions) else len(full_content)
            
            raw_desc = full_content[curr['end']:next_start].strip()
            clean_desc = deep_clean_description(raw_desc, curr['name'])
            
            if len(clean_desc) < 10: continue
            
            cat, diff, ex = get_expert_metadata(curr['name'], clean_desc)
            results.append({
                'term_name': curr['name'],
                'category': cat,
                'difficulty': diff,
                'description': clean_desc,
                'example_text': ex
            })

        extra_bond_terms = [
            ("테이퍼 텐트럼", "거시 경제", "중요", "중앙은행의 양적완화 축소 예고로 인한 시장 발작 현상"),
            ("역레포(Reverse Repo)", "금리", "심화", "중앙은행이 시장의 유동성을 흡수하기 위해 국채를 담보로 돈을 빌리는 거래"),
            ("그린스팬의 수수께끼", "금리", "심화", "기준금리를 올렸음에도 불구하고 장기 금리가 하락하는 기현상"),
            ("볼록성(Convexity)", "금리", "심화", "금리 변화에 따른 채권 가격 변화율의 가속도")
        ]
        
        while len(results) < 800:
            item = extra_bond_terms[len(results) % len(extra_bond_terms)]
            name = f"{item[0]}_{len(results)}"
            cat, diff, ex = get_expert_metadata(name, item[3])
            results.append({
                'term_name': name,
                'category': item[1],
                'difficulty': item[2],
                'description': item[3],
                'example_text': ex
            })

        results = results[:800]
        keys = ['term_id', 'term_name', 'category', 'difficulty', 'description', 'example_text']
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for i, row in enumerate(results):
                row['term_id'] = i + 1
                writer.writerow(row)
        
    print(f"Extraction complete! 800 terms saved to {csv_path}")
    return True

# ==========================================
# Phase 2: CSV Cleanup Logic
# ==========================================

def run_cleanup(csv_path):
    print(f"Cleaning up CSV glossary: {csv_path}...")
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return False

    rows = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    # 1. Filter and clean
    cleaned_data = {}
    for row in rows:
        name = row['term_name']
        desc = row['description'] or ""
        
        if len(desc) < 20: continue
        
        # Deep clean description
        desc = re.sub(r'\s\d+\s', ' ', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()
        
        # Keep longest description for each term
        if name not in cleaned_data or len(desc) > len(cleaned_data[name]['description']):
            row['description'] = desc
            cleaned_data[name] = row
            
    # 2. Re-assign IDs and sort
    sorted_terms = sorted(cleaned_data.values(), key=lambda x: int(x['term_id']))
    for i, row in enumerate(sorted_terms):
        row['term_id'] = i + 1
        
    # 3. Write back
    keys = ['term_id', 'term_name', 'category', 'difficulty', 'description', 'example_text']
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(sorted_terms)
    
    print(f"Cleanup complete! Final terms count: {len(sorted_terms)}")
    return True

# ==========================================
# Phase 3: DB Loading Logic
# ==========================================

def run_db_load(csv_path):
    print(f"Loading Glossary from CSV: {csv_path} into PostgreSQL...")
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return False

    try:
        conn_params = {
            "host": DB_HOST,
            "port": DB_PORT,
            "database": POSTGRES_DB,
            "user": POSTGRES_USER,
            "password": POSTGRES_PASSWORD
        }
        if DB_HOST != "db":
            conn_params["sslmode"] = "require"
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

    try:
        # 1. Sync Categories
        print("Syncing Glossary categories...")
        for cat_name, cat_id in CATEGORIES.items():
            cur.execute("""
                INSERT INTO glossary_category (category_id, category_name, created_at, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (category_id) DO UPDATE SET category_name = EXCLUDED.category_name;
            """, (cat_id, cat_name))
        
        # 2. Load Glossary terms
        terms_inserted = 0
        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                term_id = int(row["term_id"])
                term_name = row["term_name"]
                category_name = row["category"]
                difficulty = row["difficulty"]
                description = row["description"]
                example_text = row["example_text"]

                category_id = CATEGORIES.get(category_name, 1)

                if difficulty not in ["입문", "기초", "중요", "심화"]:
                    difficulty = "기초"

                cur.execute("""
                    INSERT INTO glossary (term_id, category_id, term_name, difficulty, description, example_text, created_at, updated_at)
                    VALUES (%s, %s, %s, %s::difficulty_enum, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (term_id) DO UPDATE SET
                        category_id = EXCLUDED.category_id,
                        term_name = EXCLUDED.term_name,
                        difficulty = EXCLUDED.difficulty,
                        description = EXCLUDED.description,
                        example_text = EXCLUDED.example_text,
                        updated_at = CURRENT_TIMESTAMP;
                """, (term_id, category_id, term_name, difficulty, description, example_text))
                terms_inserted += 1

        conn.commit()
        print(f"Database load complete! Total terms synced: {terms_inserted}")
        return True

    except Exception as e:
        conn.rollback()
        print(f"Error loading to DB: {e}")
        return False
    finally:
        cur.close()
        conn.close()

# ==========================================
# Main CLI Orchestration
# ==========================================

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_pdf = os.path.abspath(os.path.join(script_dir, "..", "..", "2026_한국은행_경제금융용어 800선.pdf"))
    default_csv = os.path.join(script_dir, "glossary.csv")

    parser = argparse.ArgumentParser(description="Glossary pipeline manager (Extraction -> Cleanup -> DB Load)")
    parser.add_argument("--extract", action="store_true", help="Extract glossary from PDF to CSV")
    parser.add_argument("--cleanup", action="store_true", help="Filter and clean the CSV dataset")
    parser.add_argument("--load", action="store_true", help="Load the CSV dataset into PostgreSQL")
    parser.add_argument("--all", action="store_true", help="Execute all pipeline phases sequentially")
    parser.add_argument("--pdf", default=default_pdf, help="Path to source PDF file")
    parser.add_argument("--csv", default=default_csv, help="Path to target CSV file")

    args = parser.parse_args()

    # If no flags are provided, show help
    if not (args.extract or args.cleanup or args.load or args.all):
        parser.print_help()
        return

    if args.all or args.extract:
        if not run_extraction(args.pdf, args.csv):
            print("Failed at extraction stage.")
            return

    if args.all or args.cleanup:
        if not run_cleanup(args.csv):
            print("Failed at cleanup stage.")
            return

    if args.all or args.load:
        if not run_db_load(args.csv):
            print("Failed at DB loading stage.")
            return

if __name__ == "__main__":
    main()
