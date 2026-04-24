"""
SQL Server Lubricants Test Data Setup Script
=============================================
Downloads all 6 tables from BigQuery LubricantsBusiness dataset, loads them
into a local SQL Server 2022 Docker container, then builds the same
LubricantsStarSchemaView star schema join as BigQuery.

BigQuery tables → SQL Server tables (identical column names):
  GLAccounts          (gl_account_id, account_name, account_type, account_category, account_group)
  Products            (product_id, product_name, product_line, product_category)
  Customers           (customer_id, customer_name, customer_segment, customer_region)
  ProfitCenters       (profit_center_id, profit_center_name, business_unit)
  Channels            (channel_id, channel_name, channel_type)
  FinancialTransactions (transaction_id, fiscal_year, fiscal_period, transaction_date,
                         amount, version, currency, gl_account_id, product_id,
                         customer_id, profit_center_id, channel_id)

Star schema view (T-SQL equivalent of BigQuery view):
  LubricantsStarSchemaView  — same 21 columns as BigQuery, same join logic

Usage:
    .venv/Scripts/python scripts/setup_sqlserver_lubricants_test.py

Prerequisites:
  - Docker Desktop running
  - ODBC Driver 17 or 18 for SQL Server installed
    https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
  - GCP key at C:/Users/Blell/Documents/Agent9/API Keys/agent9-465818-2e57f7c9b334.json
"""

import os
import sys
import time
import subprocess
import logging
import pyodbc
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

CONTAINER_NAME = "agent9_sqlserver"
SA_PASSWORD    = "Agent9Test!2024"
HOST           = "localhost"
PORT           = 1433
DATABASE       = "agent9_lubricants"

GCP_KEY_PATH = Path(
    r"C:\Users\Blell\Documents\Agent9\API Keys\agent9-465818-2e57f7c9b334.json"
)
BQ_PROJECT = "agent9-465818"
BQ_DATASET = "LubricantsBusiness"

# All 6 tables to download from BigQuery
BQ_TABLES = [
    "GLAccounts",
    "Products",
    "Customers",
    "ProfitCenters",
    "Channels",
    "FinancialTransactions",
]

ODBC_DRIVERS = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"]

# ── Star schema view — T-SQL equivalent of the BigQuery view ──────────────────

STAR_SCHEMA_VIEW_SQL = """
CREATE OR ALTER VIEW [LubricantsStarSchemaView] AS
SELECT
    ft.transaction_id,
    ft.fiscal_year,
    ft.fiscal_period,
    ft.transaction_date,
    ft.amount,
    ft.version,
    ft.currency,
    gl.account_name,
    gl.account_type,
    gl.account_category,
    gl.account_group,
    p.product_name,
    p.product_line,
    p.product_category,
    c.customer_name,
    c.customer_segment,
    c.customer_region,
    pc.profit_center_name,
    pc.business_unit,
    ch.channel_name,
    ch.channel_type
FROM        [FinancialTransactions]    ft
LEFT JOIN   [GLAccounts]              gl  ON ft.gl_account_id    = gl.gl_account_id
LEFT JOIN   [Products]                p   ON ft.product_id       = p.product_id
LEFT JOIN   [Customers]               c   ON ft.customer_id      = c.customer_id
LEFT JOIN   [ProfitCenters]           pc  ON ft.profit_center_id = pc.profit_center_id
LEFT JOIN   [Channels]                ch  ON ft.channel_id       = ch.channel_id
"""

# ── SQL Server dtype mapping ──────────────────────────────────────────────────

def _sql_type(col: str, dtype) -> str:
    dtype_str = str(dtype)
    if "datetime" in dtype_str or "date" in dtype_str:
        return "DATE"
    if "int" in dtype_str:
        return "BIGINT"
    if "float" in dtype_str or "decimal" in dtype_str:
        return "DECIMAL(18,4)"
    # Specific columns that should be numeric
    if col in ("amount",):
        return "DECIMAL(18,4)"
    if col in ("fiscal_year", "fiscal_period_num"):
        return "INT"
    return "NVARCHAR(500)"


# ── Helpers ───────────────────────────────────────────────────────────────────

def detect_odbc_driver() -> str:
    available = [d for d in pyodbc.drivers() if "SQL Server" in d]
    log.info("Available ODBC drivers: %s", available)
    for preferred in ODBC_DRIVERS:
        if preferred in available:
            log.info("Using: %s", preferred)
            return preferred
    if available:
        log.warning("Using fallback driver: %s", available[0])
        return available[0]
    raise RuntimeError(
        "No SQL Server ODBC driver found.\n"
        "Download: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server"
    )


def build_conn_str(driver: str, database: str = "master") -> str:
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={HOST},{PORT};"
        f"DATABASE={database};"
        f"UID=sa;"
        f"PWD={SA_PASSWORD};"
        f"Encrypt=no;"
        f"TrustServerCertificate=yes;"
    )


def ensure_container_running() -> None:
    """Check container state; start or create as needed."""
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Status}}", CONTAINER_NAME],
        capture_output=True, text=True
    )
    status = result.stdout.strip()

    if status == "running":
        log.info("Container '%s' already running.", CONTAINER_NAME)
        return

    if status == "exited":
        log.info("Container '%s' stopped — starting it.", CONTAINER_NAME)
        subprocess.run(["docker", "start", CONTAINER_NAME], check=True)
        return

    # Not found — pull and create
    log.info("Creating SQL Server 2022 container '%s'...", CONTAINER_NAME)
    log.info("(First run: Docker will pull the image — this may take a few minutes.)")
    subprocess.run([
        "docker", "run",
        "-e", "ACCEPT_EULA=Y",
        "-e", f"SA_PASSWORD={SA_PASSWORD}",
        "-e", "MSSQL_PID=Developer",
        "-p", f"{PORT}:1433",
        "--name", CONTAINER_NAME,
        "-d",
        "mcr.microsoft.com/mssql/server:2022-latest",
    ], check=True)


def wait_for_sqlserver(driver: str, timeout: int = 120) -> pyodbc.Connection:
    """Poll until SQL Server accepts connections."""
    conn_str = build_conn_str(driver, "master")
    deadline = time.time() + timeout
    last_err = None
    while time.time() < deadline:
        try:
            conn = pyodbc.connect(conn_str, autocommit=True, timeout=5)
            log.info("SQL Server is ready.")
            return conn
        except Exception as e:
            last_err = e
            log.info("  Waiting for SQL Server... (%s)", str(e)[:80])
            time.sleep(4)
    raise TimeoutError(f"SQL Server not ready after {timeout}s. Last error: {last_err}")


def fetch_all_tables() -> dict[str, pd.DataFrame]:
    """Download all 6 tables from BigQuery and return as {table_name: DataFrame}."""
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
    except ImportError:
        raise RuntimeError(
            "google-cloud-bigquery not installed.\n"
            "Run: .venv/Scripts/pip install google-cloud-bigquery"
        )

    if not GCP_KEY_PATH.exists():
        raise FileNotFoundError(f"GCP key not found: {GCP_KEY_PATH}")

    log.info("Connecting to BigQuery project %s ...", BQ_PROJECT)
    credentials = service_account.Credentials.from_service_account_file(str(GCP_KEY_PATH))
    client = bigquery.Client(project=BQ_PROJECT, credentials=credentials)

    tables = {}
    for table_name in BQ_TABLES:
        query = f"SELECT * FROM `{BQ_PROJECT}.{BQ_DATASET}.{table_name}`"
        log.info("Fetching %s ...", table_name)
        df = client.query(query).to_dataframe()
        log.info("  %d rows, columns: %s", len(df), list(df.columns))
        tables[table_name] = df

    return tables


def create_database(conn: pyodbc.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute(f"""
        IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{DATABASE}')
            CREATE DATABASE [{DATABASE}]
    """)
    cursor.close()
    log.info("Database [%s] ready.", DATABASE)


def load_table(conn: pyodbc.Connection, table_name: str, df: pd.DataFrame) -> None:
    """Drop, recreate, and bulk-load one table."""
    cursor = conn.cursor()

    # Drop if exists
    cursor.execute(
        f"IF OBJECT_ID('[{table_name}]', 'U') IS NOT NULL DROP TABLE [{table_name}]"
    )

    # Build CREATE TABLE with appropriate column types
    col_defs = []
    for col in df.columns:
        sql_type = _sql_type(col, df[col].dtype)
        col_defs.append(f"[{col}] {sql_type}")
    cursor.execute(f"CREATE TABLE [{table_name}] ({', '.join(col_defs)})")
    cursor.close()

    # Bulk insert via fast_executemany
    conn.autocommit = False
    cursor = conn.cursor()
    try:
        cursor.fast_executemany = True
        placeholders = ", ".join("?" * len(df.columns))
        insert_sql = f"INSERT INTO [{table_name}] VALUES ({placeholders})"

        data = []
        for row in df.itertuples(index=False, name=None):
            cleaned = tuple(
                None if (v is None or (isinstance(v, float) and pd.isna(v))) else
                v.item() if hasattr(v, "item") else v
                for v in row
            )
            data.append(cleaned)

        cursor.executemany(insert_sql, data)
        conn.commit()
        log.info("  Loaded %d rows into [%s].", len(df), table_name)
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed loading [{table_name}]: {e}") from e
    finally:
        conn.autocommit = True
        cursor.close()


def create_star_schema_view(conn: pyodbc.Connection) -> None:
    """Create LubricantsStarSchemaView — T-SQL equivalent of the BigQuery view."""
    cursor = conn.cursor()
    cursor.execute(STAR_SCHEMA_VIEW_SQL)
    log.info("View [LubricantsStarSchemaView] created.")
    cursor.close()


def verify(conn: pyodbc.Connection, tables: dict) -> None:
    """Print row counts for all tables and run KPI spot-checks on the view."""
    cursor = conn.cursor()

    log.info("\n── Row counts ──────────────────────────────────────────")
    for table_name in BQ_TABLES:
        cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        log.info("  %-25s %7d rows", table_name, cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM [LubricantsStarSchemaView]")
    log.info("  %-25s %7d rows (view)", "LubricantsStarSchemaView", cursor.fetchone()[0])

    log.info("\n── View sample — latest 5 transactions ─────────────────")
    cursor.execute("""
        SELECT TOP 5
            transaction_id, fiscal_year, fiscal_period,
            CAST(amount AS DECIMAL(18,2)), version,
            product_line, channel_name, profit_center_name
        FROM [LubricantsStarSchemaView]
        ORDER BY transaction_date DESC
    """)
    for row in cursor.fetchall():
        log.info("  %s", row)

    log.info("\n── KPI spot-checks ─────────────────────────────────────")

    # Net Revenue by year
    cursor.execute("""
        SELECT fiscal_year,
               CAST(SUM(CAST(amount AS FLOAT)) AS DECIMAL(18,0)) AS net_revenue
        FROM [LubricantsStarSchemaView]
        WHERE account_type = 'Revenue'
        GROUP BY fiscal_year
        ORDER BY fiscal_year DESC
    """)
    log.info("  Net Revenue by year:")
    for row in cursor.fetchall():
        log.info("    %s   $%s", row[0], f"{row[1]:,.0f}")

    # Revenue by channel
    cursor.execute("""
        SELECT channel_name,
               CAST(SUM(CAST(amount AS FLOAT)) AS DECIMAL(18,0)) AS revenue
        FROM [LubricantsStarSchemaView]
        WHERE account_type = 'Revenue'
        GROUP BY channel_name
        ORDER BY revenue DESC
    """)
    log.info("  Revenue by channel:")
    for row in cursor.fetchall():
        log.info("    %-35s $%s", row[0], f"{row[1]:,.0f}")

    # Revenue by product line
    cursor.execute("""
        SELECT product_line,
               CAST(SUM(CAST(amount AS FLOAT)) AS DECIMAL(18,0)) AS revenue
        FROM [LubricantsStarSchemaView]
        WHERE account_type = 'Revenue'
        GROUP BY product_line
        ORDER BY revenue DESC
    """)
    log.info("  Revenue by product line:")
    for row in cursor.fetchall():
        log.info("    %-35s $%s", row[0], f"{row[1]:,.0f}")

    cursor.close()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=== Agent9 SQL Server — Lubricants Setup ===\n")

    # 1. Start Docker container
    try:
        ensure_container_running()
    except subprocess.CalledProcessError as e:
        log.error("Docker failed: %s\nMake sure Docker Desktop is running first.", e)
        sys.exit(1)

    # 2. Detect ODBC driver
    driver = detect_odbc_driver()

    # 3. Wait for SQL Server to be ready
    master_conn = wait_for_sqlserver(driver, timeout=120)
    create_database(master_conn)
    master_conn.close()

    # 4. Fetch all 6 tables from BigQuery
    tables = fetch_all_tables()

    # 5. Load into SQL Server
    conn = pyodbc.connect(build_conn_str(driver, DATABASE), autocommit=True)

    log.info("\nLoading tables into SQL Server...")
    for table_name, df in tables.items():
        load_table(conn, table_name, df)

    # 6. Create star schema view
    create_star_schema_view(conn)

    # 7. Verify
    verify(conn, tables)
    conn.close()

    log.info("\n=== Setup complete ===")
    log.info("SQL Server connection details for Agent9:")
    log.info("  Backend:  sqlserver")
    log.info("  Host:     %s", HOST)
    log.info("  Port:     %d", PORT)
    log.info("  Database: %s", DATABASE)
    log.info("  Username: sa")
    log.info("  Password: %s", SA_PASSWORD)
    log.info("\nNext steps:")
    log.info("  1. Start Docker Desktop if not running, then re-run this script")
    log.info("  2. Run the onboarding workflow: connect to sqlserver backend, inspect schema")
    log.info("  3. Run SA assessment against dp_lubricants_sqlserver")
    log.info("  4. Verify SA → DA → SF → VA pipeline works identically to BigQuery path")


if __name__ == "__main__":
    main()
