"""Execute a client's KPIs against their real database and report what comes back.

WHAT THIS IS FOR
----------------
"The generated SQL looks right" and "the KPI returns a sensible number" are
different claims, and only the second one matters to a reader. This closes the
gap by running each KPI's SQL against the live warehouse and flagging results
that cannot be true.

WHY IT EXISTS
-------------
Written by hand on 2026-08-10 to validate Apex (Snowflake) and Hess (SQL Server),
which had never been executed against their own databases. Apex passed. Hess did
not, and none of it was visible from the SQL:

    gross_margin_pct    165.57% reported   vs   34.43% actual
    gross_profit        6,236M  reported   vs  1,297M actual   (4.8x)
    operating_income    6,816M  reported   vs    717M actual   (9.5x)
    5 further KPIs      NULL — referencing account types absent from the data

COGS, SGA and Other are stored NEGATIVE; three KPIs negated them again, adding
cost to revenue. The impossible percentage would eventually have been noticed;
the property that would not is that the DIRECTION inverted — reported margin rose
+2.66pp while the true margin fell 2.66pp, so Situation Awareness sees a healthy
business and raises nothing.

Checks are deliberately crude and unarguable: a percentage outside ±100, a NULL,
an error. Anything subtler needs a human who knows the business.

USAGE
-----
    python scripts/validate_client_kpis.py --client hess
    python scripts/validate_client_kpis.py --client apex_lubricants --kpi gross_margin_pct

Snowflake note: password auth may be refused by account MFA policy. This uses
key-pair auth via SF_PRIVATE_KEY_PATH, which is not MFA-gated, and falls back to
password only if no key is configured.
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "clients"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_client(client: str):
    m = importlib.import_module(client)
    dps = getattr(m, "DATA_PRODUCTS", None) or [getattr(m, "DATA_PRODUCT", None)]
    dp = next((d for d in dps if d), None)
    if dp is None:
        raise SystemExit(f"{client}: no DATA_PRODUCT(S) found")
    return m, dp


def _snowflake_conn():
    import snowflake.connector
    args = dict(account=os.getenv("SF_ACCOUNT"), user=os.getenv("SF_USERNAME"),
                warehouse=os.getenv("SF_WAREHOUSE"), database=os.getenv("SF_DATABASE"),
                schema=os.getenv("SF_SCHEMA"))
    key_path = os.getenv("SF_PRIVATE_KEY_PATH")
    if key_path and os.path.exists(key_path):
        # Key-pair first: password auth is rejected outright when the account
        # enforces MFA, and the failure message points at credentials rather
        # than at the auth method, which is misleading.
        from cryptography.hazmat.primitives import serialization
        with open(key_path, "rb") as f:
            key = serialization.load_pem_private_key(f.read(), password=None)
        args["private_key"] = key.private_bytes(
            serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption())
    elif os.getenv("SF_PASSWORD"):
        args["password"] = os.getenv("SF_PASSWORD")
    return snowflake.connector.connect(**args)


def _sqlserver_conn():
    import pyodbc
    drivers = [d for d in pyodbc.drivers() if "SQL Server" in d]
    if not drivers:
        raise SystemExit("no SQL Server ODBC driver installed")
    cs = (f"DRIVER={{{drivers[0]}}};SERVER={os.getenv('SS_HOST','localhost')},"
          f"{os.getenv('SS_PORT','1433')};DATABASE={os.getenv('SS_DATABASE','agent9_lubricants')};"
          f"UID={os.getenv('SS_USERNAME','sa')};PWD={os.getenv('SS_PASSWORD','Agent9Test!2024')};"
          f"TrustServerCertificate=yes;")
    return pyodbc.connect(cs, timeout=10)


def _bigquery_runner():
    from google.cloud import bigquery
    client = bigquery.Client()

    def run(sql):
        rows = list(client.query(sql).result())
        return rows[0][0] if rows else None
    return run


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--client", required=True, help="seed module name, e.g. hess")
    p.add_argument("--kpi", help="validate a single KPI id (default: all)")
    args = p.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    mod, dp = _load_client(args.client)
    source = (dp.get("source_system") or "").lower()
    print(f"client={args.client}  data_product={dp.get('id')}  source_system={source}\n")

    conn = None
    if source == "snowflake":
        conn = _snowflake_conn()

        def run(sql):
            c = conn.cursor()
            try:
                c.execute(sql); r = c.fetchone(); return r[0] if r else None
            finally:
                c.close()
    elif source == "sqlserver":
        conn = _sqlserver_conn()

        def run(sql):
            c = conn.cursor(); c.execute(sql); r = c.fetchone(); c.close()
            return r[0] if r else None
    elif source == "bigquery":
        run = _bigquery_runner()
    else:
        raise SystemExit(f"unsupported source_system: {source!r}")

    kpis = [k for k in getattr(mod, "KPIS", []) if k.get("sql_query")]
    if args.kpi:
        kpis = [k for k in kpis if k["id"] == args.kpi] or []
        if not kpis:
            raise SystemExit(f"KPI {args.kpi!r} not found or has no sql_query")

    print(f"{'KPI':28s} {'unit':6s} {'value':>20s}  verdict")
    problems = 0
    for k in kpis:
        unit = str(k.get("unit") or "")
        try:
            v = run(k["sql_query"])
        except Exception as e:
            print(f"{k['id']:28s} {unit:6s} {'ERROR':>20s}  {type(e).__name__}: {str(e)[:70]}")
            problems += 1
            continue
        if v is None:
            print(f"{k['id']:28s} {unit:6s} {'NULL':>20s}  returns nothing — check the account types it references")
            problems += 1
            continue
        v = float(v)
        verdict = ""
        # Only claims that cannot be true. Plausibility is a human judgement.
        if unit == "%" and not (-100.0 <= v <= 100.0):
            verdict = "<-- IMPOSSIBLE for a percentage"
            problems += 1
        print(f"{k['id']:28s} {unit:6s} {v:>20,.2f}  {verdict}")

    if conn is not None:
        conn.close()
    print(f"\n{len(kpis)} KPI(s) checked, {problems} needing attention")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
