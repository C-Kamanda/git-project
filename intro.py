import os
import pandas as pd
import requests
import psycopg2
from datetime import date


def write_to_postgres(df: pd.DataFrame) -> None:
    dbname = os.environ.get("POSTGRES_DB")
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")

    if not all([dbname, user, password]):
        print("PostgreSQL not configured; skipping database write.")
        return

    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS exchange_rates (
                        currency TEXT NOT NULL,
                        rate DOUBLE PRECISION NOT NULL,
                        date_ex DATE NOT NULL
                    )
                    """
                )
                for _, row in df.iterrows():
                    cur.execute(
                        "INSERT INTO exchange_rates (currency, rate, date_ex) VALUES (%s, %s, %s)",
                        (row["currency"], row["rate"], row["date_ex"]),
                    )
        print("Wrote exchange rates to PostgreSQL.")
    finally:
        conn.close()


today = date.today().strftime("%Y-%m-%d")

access_key = os.environ.get(
    "EXCHANGE_API_KEY",
    "bc89bf8b4ccabe27029a0e4477a6e96f",
)
symbols = "KES,USD,AUD,CAD,PLN,MXN"
url = f"http://api.exchangeratesapi.io/v1/{today}?access_key={access_key}&symbols={symbols}"

resp = requests.get(url)
resp.raise_for_status()
mydict = resp.json()

# Build DataFrame from the 'rates' dictionary returned by the API
rates = mydict.get("rates", {})
date_ex = mydict.get("date", today)

today_df = pd.DataFrame(list(rates.items()), columns=["currency", "rate"])
today_df["date_ex"] = date_ex

print(today_df)
write_to_postgres(today_df)