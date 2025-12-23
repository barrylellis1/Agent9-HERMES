"""Quick script to verify Deep Analysis variance numbers."""
import duckdb
import os

# Use a copy or wait for DB to be available
db_path = "data/agent9-hermes-api.duckdb"

try:
    conn = duckdb.connect(db_path, read_only=True)
    
    # First, let's understand the data range
    print("=== Data Date Range ===")
    result = conn.execute("""
        SELECT 
            MIN(strptime(CAST(date AS VARCHAR), '%Y%m%d')) as min_date,
            MAX(strptime(CAST(date AS VARCHAR), '%Y%m%d')) as max_date
        FROM FinancialTransactions
    """).fetchone()
    print(f"Date range: {result[0]} to {result[1]}")
    
    # Check Gross Revenue total by year
    print("\n=== Gross Revenue by Year (Actual only) ===")
    result = conn.execute("""
        SELECT 
            EXTRACT(year FROM strptime(CAST(ft.date AS VARCHAR), '%Y%m%d')) as year,
            SUM(CAST(REPLACE(ft.value, ',', '.') AS DECIMAL(18,2))) as total
        FROM FinancialTransactions ft
        JOIN GLAccounts ga ON ft.accountid = ga.accountid
        JOIN GLAccountsHierarchy gah ON ga.accountid = gah.HIERARCHYID
        WHERE ft.version = 'Actual'
          AND gah.DESCRIPTION = 'Gross Revenue'
        GROUP BY 1
        ORDER BY 1
    """).fetchall()
    for row in result:
        print(f"Year {int(row[0])}: {row[1]:,.2f}")
    
    # Check by Profit Center for 2025
    print("\n=== Gross Revenue by Profit Center (2025 only) ===")
    result = conn.execute("""
        SELECT 
            COALESCE(pct.LONG_DESCR, 'Unassigned') as profit_center,
            SUM(CAST(REPLACE(ft.value, ',', '.') AS DECIMAL(18,2))) as total
        FROM FinancialTransactions ft
        JOIN GLAccounts ga ON ft.accountid = ga.accountid
        JOIN GLAccountsHierarchy gah ON ga.accountid = gah.HIERARCHYID
        LEFT JOIN ProfitCenter pc ON ft.profitcenterid = pc.profitcenterid
        LEFT JOIN ProfitCenterTexts pct ON pc.profitcenterid = pct.PROFITCENTERID
        WHERE ft.version = 'Actual'
          AND gah.DESCRIPTION = 'Gross Revenue'
          AND EXTRACT(year FROM strptime(CAST(ft.date AS VARCHAR), '%Y%m%d')) = 2025
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT 10
    """).fetchall()
    for row in result:
        print(f"{row[0]}: {row[1]:,.2f}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    print("\nDatabase is likely locked by the running backend.")
    print("Stop the backend first or use the API to query.")
