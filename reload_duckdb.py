
import duckdb
import os
import sys
import glob

# Add project root to path
sys.path.append(os.getcwd())

def reload_fi_star_view():
    print("--- Reloading FI Star View from CSVs ---")
    
    # Point to the API database which the backend actually uses
    db_path = "data/agent9-hermes-api.duckdb"
    
    # Path to CSVs provided by user
    csv_dir = r"C:\Users\Blell\Documents\Agent9\SAP DataSphere Data\datasphere-content-1.7\datasphere-content-1.7\SAP_Sample_Content\CSV\FI"
    
    # Use the rebalanced file and shift dates forward by 2 years to match 2026 simulation
    ft_csv = os.path.join(csv_dir, "FinancialTransactions.rebalanced.csv")
    gl_csv = os.path.join(csv_dir, "GLAccounts.csv")
    glh_csv = os.path.join(csv_dir, "GLAccountsHierarchy.csv")
    # Add other CSVs as needed for the full join
    
    print(f"Loading FinancialTransactions from: {ft_csv}")
    
    try:
        con = duckdb.connect(db_path)
        
        # 1. Drop existing tables to ensure clean reload
        tables = [
            "FinancialTransactions", "GLAccounts", "GLAccountsHierarchy", 
            "GLAccountsTexts", "Products", "ProductHierarchy", 
            "Customer", "CustomersHierarchy", "CustomerType", 
            "CustomerTypeTexts", "ProfitCenter", "ProfitCenterTexts", 
            "ProfitCenterHierarchy"
        ]
        
        for table in tables:
            print(f"Dropping table {table} if exists...")
            con.execute(f"DROP TABLE IF EXISTS {table}")

        # 2. Re-create and Load Tables
        # Using read_csv_auto for simplicity, or explicit schema if known
        
        # FinancialTransactions with Date Shift (+1 Year)
        print("Loading FinancialTransactions (with +1 Year Date Shift)...")
        # Load raw first to handle date shift cleanly
        con.execute(f"""
            CREATE TABLE FinancialTransactions AS 
            SELECT 
                TRANSACTIONID,
                ACCOUNTID,
                ACCOUNTTYPEID,
                CUSTOMERID,
                CUSTOMERTYPEID,
                PRODUCTID,
                PRODUCTCATEGORYID,
                PROFITCENTERID,
                VERSION,
                CAST(strftime(strptime(CAST("DATE" AS VARCHAR), '%Y%m%d') + INTERVAL 1 YEAR, '%Y%m%d') AS VARCHAR) as "DATE",
                "VALUE"
            FROM read_csv_auto('{ft_csv}', all_varchar=True, sep=';', decimal_separator=',')
        """)
        
        # FIX: Normalize Sales Deductions (FPA1/023) to be negative for ALL loaded data (including shifted 2026)
        # This fixes the issue where shifted 2025 data (now 2026) in future months (Mar-Dec) remains positive.
        print("Normalizing Sales Deductions (FPA1/023) signs to be negative...")
        con.execute("""
            UPDATE FinancialTransactions 
            SET "VALUE" = REPLACE(CAST(CAST(CAST(REPLACE(REPLACE("VALUE", '.', ''), ',', '.') AS DOUBLE) * -1 AS DECIMAL(15,2)) AS VARCHAR), '.', ',')
            WHERE ACCOUNTID = 'FPA1/023' 
              AND CAST(REPLACE(REPLACE("VALUE", '.', ''), ',', '.') AS DOUBLE) > 0
        """)
        
        # PATCH: Generate Synthetic Sales Deductions for Jan 2026 (Ratio: -0.35 of Gross Revenue)
        print("PATCHing: Generating Jan 2026 Sales Deductions based on Gross Revenue...")
        
        # 0. CLEANUP: Remove any existing FPA1/023 entries for Jan 2026 (from the +1 year shift) to avoid noise
        con.execute("DELETE FROM FinancialTransactions WHERE ACCOUNTID = 'FPA1/023' AND LEFT(CAST(\"DATE\" AS VARCHAR), 6) = '202601'")
        print("Cleaned up existing Jan 2026 Sales Deductions (if any).")

        # Debug: Check source data count
        count_src = con.execute("""
            SELECT COUNT(*) FROM FinancialTransactions 
            WHERE ACCOUNTID = 'FPA1/022' 
              AND LEFT(CAST("DATE" AS VARCHAR), 4) = '2026' 
              AND SUBSTR(CAST("DATE" AS VARCHAR), 5, 2) = '01'
              AND VERSION = 'Actual'
        """).fetchone()[0]
        print(f"DEBUG: Found {count_src} source rows (Gross Revenue) for Jan 2026 patch.")

        con.execute(f"""
            INSERT INTO FinancialTransactions
            SELECT 
                TRANSACTIONID || '_SD' as TRANSACTIONID,
                'FPA1/023' as ACCOUNTID,
                ACCOUNTTYPEID,
                CUSTOMERID,
                CUSTOMERTYPEID,
                PRODUCTID,
                PRODUCTCATEGORYID,
                PROFITCENTERID,
                VERSION,
                "DATE",
                REPLACE(CAST(CAST(CAST(REPLACE(REPLACE("VALUE", '.', ''), ',', '.') AS DOUBLE) * -0.35 AS DECIMAL(15,2)) AS VARCHAR), '.', ',') as "VALUE"
            FROM FinancialTransactions
            WHERE ACCOUNTID = 'FPA1/022'
              AND LEFT(CAST("DATE" AS VARCHAR), 4) = '2026'
              AND SUBSTR(CAST("DATE" AS VARCHAR), 5, 2) = '01'
              AND VERSION = 'Actual'
        """)
        
        # Debug: Verify insertion
        count_inserted = con.execute("""
            SELECT COUNT(*), SUM(CAST(REPLACE(REPLACE("VALUE", '.', ''), ',', '.') AS DOUBLE))
            FROM FinancialTransactions 
            WHERE ACCOUNTID = 'FPA1/023' 
              AND LEFT(CAST("DATE" AS VARCHAR), 6) = '202601'
              AND TRANSACTIONID LIKE '%_SD'
        """).fetchone()
        
        print(f"PATCH applied: Jan 2026 Sales Deductions inserted. Count={count_inserted[0]}, Sum={count_inserted[1]}")
        
        if count_inserted[0] > 0 and (count_inserted[1] is None or abs(count_inserted[1]) < 0.01):
             raise ValueError("CRITICAL FAILURE: Sales Deductions were inserted but values are ZERO! The calculation logic failed.")


        # PATCH: Feb 2026 Data Generation for "Current Month" Scenarios (Live Simulation)
        print("PATCHing: Generating Feb 2026 Data (Live Simulation)...")
        
        # 1. Clear any existing Feb 2026 data to avoid duplicates/conflicts
        con.execute("DELETE FROM FinancialTransactions WHERE LEFT(CAST(\"DATE\" AS VARCHAR), 6) = '202602'")
        
        # 2. Clone Jan 2026 Base Data (excluding the synthetic SDs) to Feb 2026
        con.execute("""
            INSERT INTO FinancialTransactions
            SELECT 
                TRANSACTIONID || '_FEB' as TRANSACTIONID,
                ACCOUNTID,
                ACCOUNTTYPEID,
                CUSTOMERID,
                CUSTOMERTYPEID,
                PRODUCTID,
                PRODUCTCATEGORYID,
                PROFITCENTERID,
                VERSION,
                REPLACE(CAST("DATE" AS VARCHAR), '202601', '202602') as "DATE",
                "VALUE"
            FROM FinancialTransactions
            WHERE LEFT(CAST("DATE" AS VARCHAR), 6) = '202601' 
              AND ACCOUNTID != 'FPA1/023' -- Don't clone the synthetic deductions yet
        """)

        # 3. COO Anomaly: US10_PCC3S Gross Revenue (FPA1/022) drops 20% in Feb (Supply Chain Choke)
        print("PATCHing: Applying COO Anomaly (US10_PCC3S Supply Chain Choke)...")
        con.execute("""
            UPDATE FinancialTransactions
            SET "VALUE" = REPLACE(CAST(CAST(CAST(REPLACE(REPLACE("VALUE", '.', ''), ',', '.') AS DECIMAL(15,2)) * 0.8 AS DECIMAL(15,2)) AS VARCHAR), '.', ',')
            WHERE LEFT(CAST("DATE" AS VARCHAR), 6) = '202602'
              AND PROFITCENTERID = 'US10_PCC3S'
              AND ACCOUNTID = 'FPA1/022'
        """)

        # 4. CFO Anomaly: High Sales Deductions (FPA1/023) for Feb 2026 (Margin Leak)
        print("PATCHing: Generating Feb 2026 Sales Deductions...")
        con.execute("""
            INSERT INTO FinancialTransactions
            SELECT 
                TRANSACTIONID || '_SD' as TRANSACTIONID,
                'FPA1/023' as ACCOUNTID,
                ACCOUNTTYPEID,
                CUSTOMERID,
                CUSTOMERTYPEID,
                PRODUCTID,
                PRODUCTCATEGORYID,
                PROFITCENTERID,
                VERSION,
                "DATE",
                REPLACE(CAST(CAST(CAST(REPLACE(REPLACE("VALUE", '.', ''), ',', '.') AS DOUBLE) * 
                    CASE 
                        -- CFO Story: Margin Leak in Z1 (High Deductions)
                        WHEN CUSTOMERTYPEID = 'Z1' THEN -0.18 
                        ELSE -0.05 
                    END
                AS DECIMAL(15,2)) AS VARCHAR), '.', ',') as "VALUE"
            FROM FinancialTransactions
            WHERE ACCOUNTID = 'FPA1/022'
              AND LEFT(CAST("DATE" AS VARCHAR), 6) = '202602'
              AND VERSION = 'Actual'
        """)
        print("PATCH applied: Feb 2026 Data generated.")

        # PATCH: Narrative-Aligned Data Shaping for 2025 Stories
        # 1. QA Bottleneck (US10_PCC3S): High deductions (returns) in Jan-Apr
        # 2. Customer Exp (Z1): High deductions (credits) in Jan-Jun
        # 3. Baseline: Standard 2.5% deductions elsewhere
        # 4. Remove existing anomalous 2025 deductions first
        
        print("PATCHing: Applying Narrative-Aligned Logic for 2025...")
        
        # Remove existing bad data (massive spikes in Jun/Jul)
        con.execute("DELETE FROM FinancialTransactions WHERE ACCOUNTID = 'FPA1/023' AND LEFT(CAST(\"DATE\" AS VARCHAR), 4) = '2025'")
        
        # Insert synthetic data
        con.execute(f"""
            INSERT INTO FinancialTransactions
            SELECT 
                TRANSACTIONID || '_SD' as TRANSACTIONID,
                'FPA1/023' as ACCOUNTID,
                ACCOUNTTYPEID,
                CUSTOMERID,
                CUSTOMERTYPEID,
                PRODUCTID,
                PRODUCTCATEGORYID,
                PROFITCENTERID,
                VERSION,
                "DATE",
                REPLACE(CAST(CAST(CAST(REPLACE(REPLACE("VALUE", '.', ''), ',', '.') AS DOUBLE) * 
                    CASE 
                        -- Story 1: QA Bottleneck (High Returns/Scrap) - Reduced to 5% to make 2026 look worse
                        WHEN PROFITCENTERID = 'US10_PCC3S' AND SUBSTR(CAST("DATE" AS VARCHAR), 5, 2) IN ('01', '02', '03', '04') THEN -0.05
                        -- Story 4: Customer Exp (Credits/Refunds) - Reduced to 4%
                        WHEN CUSTOMERTYPEID = 'Z1' AND SUBSTR(CAST("DATE" AS VARCHAR), 5, 2) IN ('01', '02', '03', '04', '05', '06') THEN -0.04
                        -- Baseline - Reduced to 1%
                        ELSE -0.01
                    END
                AS DECIMAL(15,2)) AS VARCHAR), '.', ',') as "VALUE"
            FROM FinancialTransactions
            WHERE ACCOUNTID = 'FPA1/022'
              AND LEFT(CAST("DATE" AS VARCHAR), 4) = '2025'
              AND VERSION = 'Actual'
        """)
        print("PATCH applied: 2025 Narrative Stories aligned.")

        # GLAccounts
        print("Loading GLAccounts...")
        con.execute(f"CREATE TABLE GLAccounts AS SELECT * FROM read_csv_auto('{os.path.join(csv_dir, 'GLAccounts.csv')}', all_varchar=True)")

        # GLAccountsHierarchy
        print("Loading GLAccountsHierarchy...")
        con.execute(f"CREATE TABLE GLAccountsHierarchy AS SELECT * FROM read_csv_auto('{os.path.join(csv_dir, 'GLAccountsHierarchy.csv')}', all_varchar=True)")
        
        # GLAccountsTexts
        print("Loading GLAccountsTexts...")
        con.execute(f"CREATE TABLE GLAccountsTexts AS SELECT * FROM read_csv_auto('{os.path.join(csv_dir, 'GLAccountsTexts.csv')}', all_varchar=True)")

        # Products
        print("Loading Products...")
        con.execute(f"CREATE TABLE Products AS SELECT * FROM read_csv_auto('{os.path.join(csv_dir, 'Products.csv')}', all_varchar=True)")

        # ProductHierarchy
        print("Loading ProductHierarchy...")
        con.execute(f"CREATE TABLE ProductHierarchy AS SELECT * FROM read_csv_auto('{os.path.join(csv_dir, 'ProductHierarchy.csv')}', all_varchar=True)")

        # Customer
        print("Loading Customer...")
        con.execute(f"CREATE TABLE Customer AS SELECT * FROM read_csv_auto('{os.path.join(csv_dir, 'Customer.csv')}', all_varchar=True)")

        # CustomersHierarchy
        print("Loading CustomersHierarchy...")
        con.execute(f"CREATE TABLE CustomersHierarchy AS SELECT * FROM read_csv_auto('{os.path.join(csv_dir, 'CustomersHierarchy.csv')}', all_varchar=True)")

        # CustomerType
        print("Loading CustomerType...")
        con.execute(f"CREATE TABLE CustomerType AS SELECT * FROM read_csv_auto('{os.path.join(csv_dir, 'CustomerType.csv')}', all_varchar=True)")
        
        # CustomerTypeTexts
        print("Loading CustomerTypeTexts...")
        con.execute(f"CREATE TABLE CustomerTypeTexts AS SELECT * FROM read_csv_auto('{os.path.join(csv_dir, 'CustomerTypeTexts.csv')}', all_varchar=True)")

        # ProfitCenter
        print("Loading ProfitCenter...")
        con.execute(f"CREATE TABLE ProfitCenter AS SELECT * FROM read_csv_auto('{os.path.join(csv_dir, 'ProfitCenter.csv')}', all_varchar=True)")

        # ProfitCenterTexts
        print("Loading ProfitCenterTexts...")
        con.execute(f"CREATE TABLE ProfitCenterTexts AS SELECT * FROM read_csv_auto('{os.path.join(csv_dir, 'ProfitCenterTexts.csv')}', all_varchar=True)")

        # ProfitCenterHierarchy
        print("Loading ProfitCenterHierarchy...")
        con.execute(f"CREATE TABLE ProfitCenterHierarchy AS SELECT * FROM read_csv_auto('{os.path.join(csv_dir, 'ProfitCenterHierarchy.csv')}', all_varchar=True)")

        # 3. Verify Row Counts
        ft_count = con.execute("SELECT COUNT(*) FROM FinancialTransactions").fetchone()[0]
        print(f"✅ FinancialTransactions loaded: {ft_count} rows")
        
        # 4. Recreate FI_Star_View
        print("Recreating FI_Star_View...")
        view_sql = """
            CREATE OR REPLACE VIEW FI_Star_View AS
            WITH FinancialTransactions_Typed AS (
                SELECT *, strptime(CAST("DATE" AS VARCHAR), '%Y%m%d') AS transaction_date FROM FinancialTransactions
            )
            SELECT
                ft.transactionid AS "Transaction ID",
                EXTRACT(year FROM ft.transaction_date) AS "Fiscal Year",
                EXTRACT(quarter FROM ft.transaction_date) AS "Fiscal Quarter",
                EXTRACT(month FROM ft.transaction_date) AS "Fiscal Month",
                CAST(strftime(ft.transaction_date, '%Y-%m') AS VARCHAR) AS "Fiscal Year-Month",
                strftime(ft.transaction_date, '%W') AS "Fiscal Week",
                CASE WHEN EXTRACT(year FROM ft.transaction_date) = EXTRACT(year FROM CURRENT_DATE) THEN 1 ELSE 0 END AS "Fiscal YTD Flag",
                CASE WHEN EXTRACT(year FROM ft.transaction_date) = EXTRACT(year FROM CURRENT_DATE) AND EXTRACT(quarter FROM ft.transaction_date) = EXTRACT(quarter FROM CURRENT_DATE) THEN 1 ELSE 0 END AS "Fiscal QTD Flag",
                CASE WHEN EXTRACT(year FROM ft.transaction_date) = EXTRACT(year FROM CURRENT_DATE) AND EXTRACT(month FROM ft.transaction_date) = EXTRACT(month FROM CURRENT_DATE) THEN 1 ELSE 0 END AS "Fiscal MTD Flag",
                CASE WHEN ft.transaction_date >= (CURRENT_DATE - INTERVAL '1' YEAR) THEN 1 ELSE 0 END AS "Rolling 12 Months Flag",
                CASE WHEN ft.transaction_date >= (CURRENT_DATE - INTERVAL '4' QUARTER) THEN 1 ELSE 0 END AS "Rolling 4 Quarters Flag",
                ft.accountid AS "Account ID",
                ft.accounttypeid AS "Account Type ID",
                ft.customerid AS "Customer ID",
                ft.customertypeid AS "Customer Type ID",
                ft.productid AS "Product ID",
                ft.productcategoryid AS "Product Category ID",
                ft.profitcenterid AS "Profit Center ID",
                ft.version AS "Version",
                ft.transaction_date AS "Transaction Date",
                CAST(REPLACE(ft.value, ',', '.') AS DECIMAL(18, 2)) AS "Transaction Value Amount",
                gah.DESCRIPTION AS "Account Hierarchy Desc",
                COALESCE(gat."MEDIUM_DESCR", gat."LONG_DESCR") AS "Account Long Description",
                gah.DESCRIPTION AS "Account/Group Description",
                gah.LEVEL AS "Parent Account/Group Hierarchy ID",
                gah_parent.DESCRIPTION AS "Parent Account/Group Description",
                ph.DESCRIPTION AS "Product Name",
                ph.LEVEL AS "Parent Product Hierarchy ID",
                ph_parent.DESCRIPTION AS "Parent Product/Group Description",
                ch.DESCRIPTION AS "Customer Name",
                ch.DESCRIPTION AS "Customer/Group Description",
                ch.LEVEL AS "Parent Customer Hierarchy ID",
                ch_parent.DESCRIPTION AS "Parent Customer/Group Description",
                COALESCE(ctt.LONG_DESCR, ctt.MEDIUM_DESCR, ctt.SHORT_DESCR) AS "Customer Type Name",
                pct.LONG_DESCR AS "Profit Center Name",
                pch.HIERARCHYID AS "Profit Center Hierarchyid",
                ch.HIERARCHYID AS "Customer Hierarchyid",
                pch.DESCRIPTION AS "Profit Center/Group Description",
                pch.LEVEL AS "Parent Profit Center Hierarchy ID",
                pch_parent.DESCRIPTION AS "Parent Profit Center/Group Description"
            FROM FinancialTransactions_Typed ft
            JOIN GLAccounts ga ON ft.accountid = ga.accountid
            LEFT JOIN GLAccountsTexts gat ON ga.accountid = gat.accountid
            LEFT JOIN GLAccountsHierarchy gah ON ga.accountid = gah.HIERARCHYID
            LEFT JOIN GLAccountsHierarchy gah_parent ON gah.LEVEL = gah_parent.HIERARCHYID
            LEFT JOIN Products p ON ft.productid = p.productid
            LEFT JOIN ProductHierarchy ph ON p.productid = ph.HIERARCHYID
            LEFT JOIN ProductHierarchy ph_parent ON ph.LEVEL = ph_parent.HIERARCHYID
            LEFT JOIN Customer c ON ft.customerid = c.customerid
            LEFT JOIN CustomersHierarchy ch ON c.customerid = ch.HIERARCHYID
            LEFT JOIN CustomersHierarchy ch_parent ON ch.LEVEL = ch_parent.HIERARCHYID
            LEFT JOIN CustomerType ct ON ft.customertypeid = ct.customertypeid
            LEFT JOIN CustomerTypeTexts ctt ON ct.customertypeid = ctt.CUSTOMERTYPEID
            LEFT JOIN ProfitCenter pc ON ft.profitcenterid = pc.profitcenterid
            LEFT JOIN ProfitCenterTexts pct ON pc.profitcenterid = pct.PROFITCENTERID
            LEFT JOIN ProfitCenterHierarchy pch ON pc.profitcenterid = pch.HIERARCHYID
            LEFT JOIN ProfitCenterHierarchy pch_parent ON pch.LEVEL = pch_parent.HIERARCHYID
        """
        con.execute(view_sql)
        print("✅ FI_Star_View recreated.")

        # 5. Check 2026 data existence
        try:
            # We need to cast date to check year because we loaded as all_varchar
            count_2026 = con.execute("SELECT COUNT(*) FROM FinancialTransactions WHERE strptime(date, '%Y%m%d') >= '2026-01-01'").fetchone()[0]
            print(f"✅ 2026 Transactions found: {count_2026} rows")
        except Exception as e:
             print(f"⚠️ Could not verify 2026 date: {e}")

        con.close()
        print("Database reload complete.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    reload_fi_star_view()
