from __future__ import annotations

import argparse
from io import StringIO
import os
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

import pandas as pd
import psycopg2
import psycopg2.extras
import requests
from dotenv import load_dotenv


load_dotenv()

ECOS_BASE_URL = "https://ecos.bok.or.kr/api"
ECOS_BASE_RATE_STAT = "722Y001"
ECOS_MARKET_RATE_STAT = "817Y002"
FSS_DEPOSIT_URL = "https://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json"
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def get_db_config() -> dict:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("POSTGRES_DB", "bonds_db"),
        "user": os.getenv("POSTGRES_USER", "ssafyuser"),
        "password": os.getenv("POSTGRES_PASSWORD", "ssafy"),
    }


def to_decimal(value):
    if value is None or pd.isna(value):
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


class EcosInterestRateClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def auto_discover_item_code(self, stat_code: str, keyword: str) -> str | None:
        url = f"{ECOS_BASE_URL}/StatisticItemList/{self.api_key}/json/kr/1/1000/{stat_code}"
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        rows = response.json().get("StatisticItemList", {}).get("row", [])
        clean_keyword = keyword.replace(" ", "")
        for row in rows:
            item_name = row.get("ITEM_NAME", "").replace(" ", "")
            if clean_keyword in item_name:
                return row.get("ITEM_CODE")
        return None

    def fetch_ecos_data(
        self,
        stat_code: str,
        cycle: str,
        start_date: str,
        end_date: str,
        item_code: str | None,
        column_name: str,
    ) -> pd.DataFrame:
        if not item_code:
            return pd.DataFrame(columns=["date", column_name])

        url = (
            f"{ECOS_BASE_URL}/StatisticSearch/{self.api_key}/json/kr/1/100000/"
            f"{stat_code}/{cycle}/{start_date}/{end_date}/{item_code}"
        )
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        rows = response.json().get("StatisticSearch", {}).get("row", [])
        if not rows:
            return pd.DataFrame(columns=["date", column_name])

        df = pd.DataFrame(rows)[["TIME", "DATA_VALUE"]]
        df[column_name] = pd.to_numeric(df["DATA_VALUE"], errors="coerce")
        if cycle == "D":
            df["date"] = pd.to_datetime(df["TIME"], format="%Y%m%d")
        else:
            df["date"] = pd.to_datetime(df["TIME"] + "01", format="%Y%m%d")

        return df[["date", column_name]]

    def fetch_korea_rates(self, days_back: int) -> pd.DataFrame:
        end_dt = datetime.today()
        start_dt = end_dt - timedelta(days=days_back)

        base_code = self.auto_discover_item_code(ECOS_BASE_RATE_STAT, "기준금리")
        bond_3y_code = self.auto_discover_item_code(ECOS_MARKET_RATE_STAT, "국고채(3년)")
        bond_10y_code = self.auto_discover_item_code(ECOS_MARKET_RATE_STAT, "국고채(10년)")

        df_base = self.fetch_ecos_data(
            ECOS_BASE_RATE_STAT,
            "M",
            start_dt.strftime("%Y%m"),
            end_dt.strftime("%Y%m"),
            base_code,
            "base_interest_rate",
        )
        df_3y = self.fetch_ecos_data(
            ECOS_MARKET_RATE_STAT,
            "D",
            start_dt.strftime("%Y%m%d"),
            end_dt.strftime("%Y%m%d"),
            bond_3y_code,
            "three_year_yield",
        )
        df_10y = self.fetch_ecos_data(
            ECOS_MARKET_RATE_STAT,
            "D",
            start_dt.strftime("%Y%m%d"),
            end_dt.strftime("%Y%m%d"),
            bond_10y_code,
            "ten_year_yield",
        )

        merged = df_3y.sort_values("date").reset_index(drop=True)
        for df in [df_10y, df_base]:
            if not df.empty:
                merged = pd.merge(merged, df, on="date", how="outer")

        if merged.empty:
            return merged

        merged = merged.sort_values("date").ffill()
        merged["yield_curve_spread"] = merged["ten_year_yield"] - merged["three_year_yield"]
        return merged.reset_index(drop=True)


def fetch_fred_series(series_id: str, column_name: str, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    response = requests.get(FRED_CSV_URL, params={"id": series_id}, timeout=20)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))
    df["date"] = pd.to_datetime(df["observation_date"])
    df[column_name] = pd.to_numeric(df[series_id].replace(".", None), errors="coerce")
    df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]
    return df[["date", column_name]]


def fetch_us_rates(days_back: int) -> pd.DataFrame:
    end_dt = datetime.today()
    start_dt = end_dt - timedelta(days=days_back)

    df_base = fetch_fred_series("DFF", "base_interest_rate", start_dt, end_dt)
    df_3y = fetch_fred_series("DGS3", "three_year_yield", start_dt, end_dt)
    df_10y = fetch_fred_series("DGS10", "ten_year_yield", start_dt, end_dt)
    merged = pd.merge(df_base, df_3y, on="date", how="outer")
    merged = pd.merge(merged, df_10y, on="date", how="outer")

    if merged.empty:
        return merged

    merged = merged.sort_values("date").ffill()
    merged["yield_curve_spread"] = merged["ten_year_yield"] - merged["three_year_yield"]
    return merged.reset_index(drop=True)


def fetch_deposit_rates(api_key: str, top_fin_group_no: str) -> list[dict]:
    params = {"auth": api_key, "topFinGrpNo": top_fin_group_no, "pageNo": 1}
    response = requests.get(FSS_DEPOSIT_URL, params=params, timeout=20)
    response.raise_for_status()

    result = response.json().get("result", {})
    if result.get("err_cd") != "000":
        raise RuntimeError(f"FSS API request failed: {result.get('err_msg')}")

    rates_12m = {}
    for option in result.get("optionList", []):
        if option.get("save_trm") == "12":
            rates_12m[option.get("fin_prdt_cd")] = {
                "base_rate": option.get("intr_rate"),
                "prime_rate": option.get("intr_rate2"),
            }

    rows = []
    for product in result.get("baseList", []):
        product_code = product.get("fin_prdt_cd")
        if product_code not in rates_12m:
            continue

        rows.append(
            {
                "bank_name": product.get("kor_co_nm"),
                "product_name": product.get("fin_prdt_nm", "").replace("\n", " ").replace("\r", "").strip(),
                "base_rate": rates_12m[product_code]["base_rate"],
                "prime_rate": rates_12m[product_code]["prime_rate"],
            }
        )

    return rows


def upsert_base_rates(conn, country_name: str, rates: pd.DataFrame) -> int:
    if rates.empty:
        return 0

    normalized = rates.copy()
    normalized["base_date"] = pd.to_datetime(normalized["date"]).dt.date
    normalized = normalized.drop_duplicates(subset=["base_date"], keep="last")

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO "Country" (country_name, created_at, updated_at)
            VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (country_name) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
            RETURNING country_id
            """,
            (country_name,),
        )
        country_id = cur.fetchone()[0]

        rows = [
            (
                country_id,
                row["base_date"],
                to_decimal(row.get("base_interest_rate")),
                to_decimal(row.get("three_year_yield")),
                to_decimal(row.get("ten_year_yield")),
                to_decimal(row.get("yield_curve_spread")),
            )
            for _, row in normalized.iterrows()
        ]

        psycopg2.extras.execute_batch(
            cur,
            """
            INSERT INTO "BaseRate" (
                country_id, base_date, base_interest_rate, three_year_yield,
                ten_year_yield, yield_curve_spread, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (country_id, base_date) DO UPDATE SET
                base_interest_rate = EXCLUDED.base_interest_rate,
                three_year_yield = EXCLUDED.three_year_yield,
                ten_year_yield = EXCLUDED.ten_year_yield,
                yield_curve_spread = EXCLUDED.yield_curve_spread,
                updated_at = CURRENT_TIMESTAMP,
                deleted_at = NULL
            """,
            rows,
            page_size=500,
        )

    return len(rows)


def upsert_deposit_rates(conn, rows: list[dict]) -> None:
    with conn.cursor() as cur:
        for row in rows:
            if not row.get("bank_name") or not row.get("product_name"):
                continue

            cur.execute(
                """
                INSERT INTO "Bank" (bank_name, created_at, updated_at)
                VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (bank_name) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                RETURNING bank_id
                """,
                (row["bank_name"][:50],),
            )
            bank_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO "DepositRate" (
                    bank_id, product_name, base_rate, prime_rate, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (bank_id, product_name) DO UPDATE SET
                    base_rate = EXCLUDED.base_rate,
                    prime_rate = EXCLUDED.prime_rate,
                    updated_at = CURRENT_TIMESTAMP,
                    deleted_at = NULL
                """,
                (
                    bank_id,
                    row["product_name"][:50],
                    to_decimal(row.get("base_rate")),
                    to_decimal(row.get("prime_rate")),
                ),
            )


def load_base_rates(conn, days_back: int) -> None:
    ecos_api_key = os.getenv("ECOS_API_KEY")
    if ecos_api_key:
        korea_rates = EcosInterestRateClient(ecos_api_key).fetch_korea_rates(days_back)
        if not korea_rates.empty:
            count = upsert_base_rates(conn, "대한민국", korea_rates)
            print(f"Loaded {count} Korea base/yield rate rows.")
    else:
        print("Skipping ECOS rates: ECOS_API_KEY is not set.")

    us_rates = fetch_us_rates(days_back)
    if not us_rates.empty:
        count = upsert_base_rates(conn, "미국", us_rates)
        print(f"Loaded {count} US treasury rate rows.")


def load_deposit_rates(conn) -> None:
    fss_api_key = os.getenv("FSS_API_KEY")
    if not fss_api_key:
        print("Skipping deposit rates: FSS_API_KEY is not set.")
        return

    rows = fetch_deposit_rates(fss_api_key, os.getenv("FSS_TOP_FIN_GRP_NO", "020000"))
    upsert_deposit_rates(conn, rows)
    print(f"Loaded {len(rows)} 12-month deposit rate rows.")


def main():
    parser = argparse.ArgumentParser(description="Load interest and deposit rates into PostgreSQL.")
    parser.add_argument("--days-back", type=int, default=3650)
    parser.add_argument("--only", choices=["all", "base-rate", "deposit-rate"], default="all")
    args = parser.parse_args()

    conn = psycopg2.connect(**get_db_config())
    try:
        if args.only in ("all", "base-rate"):
            load_base_rates(conn, args.days_back)
        if args.only in ("all", "deposit-rate"):
            load_deposit_rates(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
