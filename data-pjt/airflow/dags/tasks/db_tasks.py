import requests
import psycopg2
from datetime import datetime, timedelta
from tasks.helpers import (
    API_KEY, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, 
    DB_HOST, DB_PORT, safe_float, safe_int, add_months
)

def ingest_option_cashflow_details():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD)
    cur = conn.cursor()
    
    # 1. 상세 정보가 비어 있는 채권 조회 (최대 100건만 점진적으로 처리하여 API 호출 횟수 조절)
    cur.execute("""
        SELECT b.isin_code, b.issue_date, b.maturity_date, b.payment_cycle_months, b.option_type, b.interest_type, b.cashflow_rule_id, b.option_exercise_id
        FROM bond b
        JOIN bond_cashflow_rule c ON b.cashflow_rule_id = c.cashflow_rule_id
        WHERE c.first_interest_payment_date IS NULL
        LIMIT 100;
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} bonds needing option/cashflow details enrichment.")
    
    def safe_parse_date(d_str):
        if d_str:
            d_str = str(d_str).strip()
            if len(d_str) == 8:
                try:
                    return datetime.strptime(d_str, "%Y%m%d").date()
                except ValueError:
                    return None
        return None
        
    for row in rows:
        isin_code, issue_date, maturity_date, payment_cycle, option_type, interest_type, cashflow_rule_id, option_exercise_id = row
        
        use_api_data = False
        
        # API 수집 변수 초기화
        api_interest_payment_method = None
        api_interest_payment_unit_months = None
        api_interest_calculation_months = None
        api_interest_pre_post_type = None
        api_first_interest_payment_date = None
        api_interest_payment_basis = None
        api_interest_month_end_type = None
        
        api_option_type = option_type
        api_exercise_start_date_1 = None
        api_exercise_end_date_1 = None
        api_exercise_start_date_2 = None
        api_exercise_end_date_2 = None
        api_exercise_reason = None
        
        # 1-1. KSD OpenAPI 호출 시도 (최선)
        ksd_intr_url = f"http://apis.data.go.kr/B552481/BondSvc/getBondIntrPayInfo?serviceKey={API_KEY}&resultType=json&isinCd={isin_code}"
        ksd_opt_url = f"http://apis.data.go.kr/B552481/BondSvc/getBondOptionInfo?serviceKey={API_KEY}&resultType=json&isinCd={isin_code}"
        
        try:
            intr_resp = requests.get(ksd_intr_url, timeout=10)
            opt_resp = requests.get(ksd_opt_url, timeout=10)
            
            if intr_resp.status_code == 200 and opt_resp.status_code == 200:
                intr_data = intr_resp.json()
                opt_data = opt_resp.json()
                
                intr_items = intr_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                opt_items = opt_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                
                # 리스트 형태 보정
                if not isinstance(intr_items, list):
                    intr_items = [intr_items] if intr_items else []
                if not isinstance(opt_items, list):
                    opt_items = [opt_items] if opt_items else []
                
                if intr_items or opt_items:
                    use_api_data = True
                    print(f"KSD API data found for {isin_code}.")
                    
                    if intr_items:
                        item = intr_items[0]
                        api_interest_payment_method = item.get('intrPayMthdNm')
                        api_interest_payment_unit_months = item.get('intrPayCyclCtt')
                        api_interest_calculation_months = item.get('intrCmpuMthdNm')
                        api_interest_pre_post_type = item.get('intrPayDivNm')
                        api_first_interest_payment_date = safe_parse_date(item.get('firstIntrPayDt'))
                        api_interest_payment_basis = item.get('bnkHldyIntPayDtDivNm')
                        api_interest_month_end_type = item.get('monthEndDivNm')
                        
                    if opt_items:
                        item = opt_items[0]
                        opt_kind = item.get('optnKindNm')
                        if opt_kind in ('CALL', 'PUT', 'CALL+PUT', '옵션해당사항없음'):
                            api_option_type = opt_kind
                        api_exercise_start_date_1 = safe_parse_date(item.get('optnExertStrtDt1'))
                        api_exercise_end_date_1 = safe_parse_date(item.get('optnExertEndDt1'))
                        api_exercise_start_date_2 = safe_parse_date(item.get('optnExertStrtDt2'))
                        api_exercise_end_date_2 = safe_parse_date(item.get('optnExertEndDt2'))
                        api_exercise_reason = item.get('optnExertRsnCtt')
        except Exception as e:
            print(f"KSD API calling failed for {isin_code}: {e}.")
            
        # 1-2. KSD API 호출 실패/공백 시 FSC 채권기본정보 OpenAPI 호출 시도 (차선)
        if not use_api_data:
            fsc_basi_url = f"http://apis.data.go.kr/1160100/GetBondIssuInfoService_V2/getBondBasiInfo_V2?serviceKey={API_KEY}&resultType=json&isinCd={isin_code}"
            try:
                print(f"Trying FSC Basic Info API for {isin_code}...")
                fsc_resp = requests.get(fsc_basi_url, timeout=20)
                if fsc_resp.status_code == 200:
                    fsc_data = fsc_resp.json()
                    fsc_items = fsc_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                    if not isinstance(fsc_items, list):
                        fsc_items = [fsc_items] if fsc_items else []
                        
                    if fsc_items:
                        use_api_data = True
                        item = fsc_items[0]
                        print(f"FSC Basic Info API data found for {isin_code}.")
                        
                        api_interest_payment_method = item.get('bondIntTcdNm')
                        api_interest_payment_unit_months = item.get('intPayCyclCtt')
                        api_interest_calculation_months = item.get('intCmpuMcdNm')
                        api_interest_pre_post_type = item.get('intPayMmntDcdNm')
                        
                        # 차기 이자지급일을 활용하거나 발행일 + 주기 계산
                        nxt_dt = safe_parse_date(item.get('nxtmCopnDt'))
                        if nxt_dt:
                            api_first_interest_payment_date = nxt_dt
                        else:
                            api_first_interest_payment_date = add_months(issue_date, payment_cycle)
                            
                        api_interest_payment_basis = item.get('bnkHldyIntPydyDcdNm')
                        api_interest_month_end_type = item.get('sttrHldyIntPydyDcdNm')
                        
                        # 옵션타입 싱크
                        opt_kind = item.get('optnTcdNm')
                        if opt_kind in ('CALL', 'PUT', 'CALL+PUT', '옵션해당사항없음'):
                            api_option_type = opt_kind
            except Exception as e:
                print(f"FSC Basic Info API calling failed for {isin_code}: {e}.")

        # 1-3. FSC 채권권리일정정보 OpenAPI 호출 시도 (최초이자지급일 및 옵션행사일 보완)
        fsc_righ_url = f"http://apis.data.go.kr/1160100/GetBondRighScheInfoService_V2/getBondRighExerSche_V2?serviceKey={API_KEY}&resultType=json&isinCd={isin_code}&numOfRows=1000"
        try:
            print(f"Trying FSC Rights Schedule API for {isin_code}...")
            righ_resp = requests.get(fsc_righ_url, timeout=20)
            if righ_resp.status_code == 200:
                righ_data = righ_resp.json()
                righ_items = righ_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                if not isinstance(righ_items, list):
                    righ_items = [righ_items] if righ_items else []
                
                valid_interest_dates = []
                valid_exercise_dates = []
                
                for item in righ_items:
                    scrs_sced_nm = item.get('scrsScedDcdNm')
                    event_date = safe_parse_date(item.get('basDt'))
                    if not event_date:
                        continue
                    
                    if scrs_sced_nm == '원리금지급일':
                        if event_date >= issue_date:
                            valid_interest_dates.append(event_date)
                    elif scrs_sced_nm == '조기상환일':
                        if event_date >= issue_date:
                            valid_exercise_dates.append(event_date)
                
                if valid_interest_dates:
                    api_first_interest_payment_date = min(valid_interest_dates)
                    use_api_data = True
                    print(f"FSC Rights Schedule API first interest date found: {api_first_interest_payment_date}")
                    
                if valid_exercise_dates:
                    valid_exercise_dates.sort()
                    api_exercise_start_date_1 = valid_exercise_dates[0]
                    api_exercise_end_date_1 = valid_exercise_dates[-1]
                    api_exercise_reason = f"조기상환 권리 행사 일정 수집 완료 (행사 가능일수: {len(valid_exercise_dates)}개)"
                    use_api_data = True
                    print(f"FSC Rights Schedule API exercise date(s) found: {valid_exercise_dates}")
        except Exception as e:
            print(f"FSC Rights Schedule API calling failed for {isin_code}: {e}.")

        # 1-4. FSC 채권권리행사정보 OpenAPI 호출 시도 (조기행사 옵션 시작일 추가 보완)
        if option_type in ('CALL', 'PUT', 'CALL+PUT'):
            fsc_rede_url = f"http://apis.data.go.kr/1160100/GetBondRedeInfoService_V2/getEarlExerOpti_V2?serviceKey={API_KEY}&resultType=json&isinCd={isin_code}&numOfRows=1000"
            try:
                print(f"Trying FSC Rights Exercise API for {isin_code}...")
                rede_resp = requests.get(fsc_rede_url, timeout=20)
                if rede_resp.status_code == 200:
                    rede_data = rede_resp.json()
                    rede_items = rede_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                    if not isinstance(rede_items, list):
                        rede_items = [rede_items] if rede_items else []
                    
                    if rede_items:
                        use_api_data = True
                        item = rede_items[0]
                        strt_dt = safe_parse_date(item.get('optiExerStrtDt'))
                        if strt_dt:
                            api_exercise_start_date_1 = strt_dt
                            print(f"FSC Rights Exercise Option Start Date found: {api_exercise_start_date_1}")
                            
                            opt_kind = item.get('optiTpCd')
                            if opt_kind in ('CALL', 'PUT', 'CALL+PUT', '옵션해당사항없음'):
                                api_option_type = opt_kind
                            
                            exer_amt = item.get('optiExerAmt')
                            if exer_amt:
                                api_exercise_reason = f"조기상환 권리 행사 (행사금액: {exer_amt})"
            except Exception as e:
                print(f"FSC Rights Exercise API calling failed for {isin_code}: {e}.")
                
        # 1-3. 데이터베이스 적재 (API 데이터 vs 계산 Fallback)
        if use_api_data:
            print(f"Updating DB with actual API data for {isin_code}.")
            
            # 이자지급조건 업데이트 (결측치에 한해 Fallback 적용)
            cur.execute("""
                UPDATE bond_cashflow_rule SET
                    interest_payment_method = %s,
                    interest_payment_unit_months = %s,
                    interest_calculation_months = %s,
                    interest_pre_post_type = %s,
                    first_interest_payment_date = %s,
                    interest_payment_basis = %s,
                    interest_month_end_type = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE cashflow_rule_id = %s;
            """, (
                api_interest_payment_method or interest_type,
                api_interest_payment_unit_months or f"{payment_cycle}개월",
                api_interest_calculation_months or "정형",
                api_interest_pre_post_type or ("선급" if interest_type == "할인채" else "후급"),
                api_first_interest_payment_date or add_months(issue_date, payment_cycle),
                api_interest_payment_basis or "직후영업일",
                api_interest_month_end_type or "직후영업일",
                cashflow_rule_id
            ))
            
            # 옵션 정보 업데이트 (결측치인 경우 룰 기반 계산 대입)
            has_option = api_option_type in ('CALL', 'PUT', 'CALL+PUT')
            default_start_1 = add_months(issue_date, 12) if has_option else None
            default_end_1 = add_months(maturity_date, -1) if has_option else None
            default_start_2 = add_months(issue_date, 24) if api_option_type == 'CALL+PUT' else None
            default_end_2 = add_months(maturity_date, -1) if api_option_type == 'CALL+PUT' else None
            default_reason = "투자자/발행인 선택에 의한 조기상환 권리 행사" if has_option else None
            
            cur.execute("""
                UPDATE bond_option_exercise SET
                    option_type = %s,
                    exercise_start_date_1 = %s,
                    exercise_end_date_1 = %s,
                    exercise_start_date_2 = %s,
                    exercise_end_date_2 = %s,
                    exercise_reason = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE option_exercise_id = %s;
            """, (
                api_option_type,
                api_exercise_start_date_1 or default_start_1,
                api_exercise_end_date_1 or default_end_1,
                api_exercise_start_date_2 or default_start_2,
                api_exercise_end_date_2 or default_end_2,
                api_exercise_reason or default_reason,
                option_exercise_id
            ))
            
            # 마스터 테이블 옵션 싱크
            if api_option_type != option_type:
                cur.execute("""
                    UPDATE bond SET option_type = %s, updated_at = CURRENT_TIMESTAMP WHERE bond_id = (
                        SELECT bond_id FROM bond WHERE isin_code = %s
                    );
                """, (api_option_type, isin_code))
                
        else:
            print(f"Running fallback calculation for {isin_code}.")
            # 1) 이자지급 상세 조건 계산
            first_interest_date = add_months(issue_date, payment_cycle)
            pre_post_type = "선급" if interest_type == "할인채" else "후급"
            
            cur.execute("""
                UPDATE bond_cashflow_rule SET
                    interest_payment_method = %s,
                    interest_payment_unit_months = %s,
                    interest_calculation_months = %s,
                    interest_pre_post_type = %s,
                    first_interest_payment_date = %s,
                    interest_payment_basis = %s,
                    interest_month_end_type = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE cashflow_rule_id = %s;
            """, (
                interest_type,
                f"{payment_cycle}개월",
                "정형",
                pre_post_type,
                first_interest_date,
                "직후영업일",
                "직후영업일",
                cashflow_rule_id
            ))
            
            # 2) 옵션 행사 상세 조건 계산
            has_option = option_type in ('CALL', 'PUT', 'CALL+PUT')
            ex_start_1 = add_months(issue_date, 12) if has_option else None
            ex_end_1 = add_months(maturity_date, -1) if has_option else None
            ex_start_2 = add_months(issue_date, 24) if option_type == 'CALL+PUT' else None
            ex_end_2 = add_months(maturity_date, -1) if option_type == 'CALL+PUT' else None
            ex_reason = "투자자/발행인 선택에 의한 조기상환 권리 행사" if has_option else None
            
            cur.execute("""
                UPDATE bond_option_exercise SET
                    option_type = %s,
                    exercise_start_date_1 = %s,
                    exercise_end_date_1 = %s,
                    exercise_start_date_2 = %s,
                    exercise_end_date_2 = %s,
                    exercise_reason = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE option_exercise_id = %s;
            """, (
                option_type,
                ex_start_1,
                ex_end_1,
                ex_start_2,
                ex_end_2,
                ex_reason,
                option_exercise_id
            ))
            
        print(f"Successfully enriched {isin_code} details.")
        
    conn.commit()
    cur.close()
    conn.close()

def ingest_daily_market_data():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD)
    cur = conn.cursor()
    
    # 최근 3일의 일별 시세를 수집 (주말/공휴일 공백 대비)
    today = datetime.now()
    dates_to_query = [(today - timedelta(days=i)).strftime("%Y%m%d") for i in range(1, 4)]
    
    for date_str in dates_to_query:
        print(f"Fetching daily price data for date: {date_str}")
        url = f"http://apis.data.go.kr/1160100/service/GetBondSecuritiesInfoService/getBondPriceInfo?serviceKey={API_KEY}&numOfRows=1000&pageNo=1&resultType=json&basDt={date_str}"
        
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
                print(f"Received {len(items)} price records for {date_str}.")
                
                for item in items:
                    isin_code = item.get('isinCd')
                    short_code = item.get('srtnCd')
                    short_name = item.get('itmsNm')
                    price_str = item.get('clprPrc')
                    ytm_str = item.get('clprBnfRt')
                    volume_str = item.get('trqu')
                    change_rate_str = item.get('clprVs')
                    
                    # 1) Bond 테이블에서 bond_id 조회
                    cur.execute('SELECT bond_id FROM bond WHERE isin_code = %s;', (isin_code,))
                    res = cur.fetchone()
                    if res:
                        bond_id = res[0]
                        
                        # 2) Bond 테이블의 short_code / short_name 업데이트
                        cur.execute("""
                            UPDATE bond SET
                                short_code = COALESCE(short_code, %s),
                                short_name = COALESCE(short_name, %s),
                                updated_at = CURRENT_TIMESTAMP
                            WHERE bond_id = %s;
                        """, (short_code, short_name, bond_id))
                        
                        # 3) BondMarketData 테이블에 적재 (UPSERT)
                        price = safe_float(price_str)
                        ytm = safe_float(ytm_str)
                        volume = safe_int(volume_str)
                        
                        base_date = datetime.strptime(date_str, "%Y%m%d").date()
                        
                        cur.execute("""
                            INSERT INTO bond_market_data (
                                bond_id, base_date, price, ytm, trading_volume, price_change_rate, created_at, updated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            ON CONFLICT (bond_id, base_date) DO UPDATE SET
                                price = EXCLUDED.price,
                                ytm = EXCLUDED.ytm,
                                trading_volume = EXCLUDED.trading_volume,
                                price_change_rate = EXCLUDED.price_change_rate,
                                updated_at = CURRENT_TIMESTAMP;
                        """, (bond_id, base_date, price, ytm, volume, change_rate_str))
                        
            else:
                print(f"Failed to fetch market data for {date_str}. Status code: {resp.status_code}")
        except Exception as e:
            print(f"Error fetching/processing market data for {date_str}: {e}")
            
    conn.commit()
    cur.close()
    conn.close()

def verify_data_count():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD)
    cur = conn.cursor()
    
    cur.execute("SELECT count(*) FROM bond;")
    bond_count = cur.fetchone()[0]
    print(f"Total records in Bond table: {bond_count}")
    
    cur.execute("SELECT count(*) FROM bond_cashflow_rule WHERE first_interest_payment_date IS NOT NULL;")
    cashflow_count = cur.fetchone()[0]
    print(f"Enriched records in BondCashflowRule table: {cashflow_count}")
    
    cur.execute("SELECT count(*) FROM bond_option_exercise WHERE exercise_start_date_1 IS NOT NULL OR option_type = '옵션해당사항없음';")
    option_count = cur.fetchone()[0]
    print(f"Enriched records in BondOptionExercise table: {option_count}")
    
    cur.execute("SELECT count(*) FROM bond_market_data;")
    market_count = cur.fetchone()[0]
    print(f"Total records in BondMarketData table: {market_count}")
    
    if bond_count >= 1000:
        print("Verification SUCCESS: 1,000 or more records loaded.")
    else:
        print(f"Verification WARNING: Only {bond_count} records found.")
        
    cur.close()
    conn.close()
