"""Debug script to investigate duplicate Customer Type Name entries"""
import duckdb

conn = duckdb.connect('data/agent9-hermes.duckdb', read_only=True)

print("=== Describe FI_Star_View ===")
try:
    df_desc = conn.execute("DESCRIBE FI_Star_View").fetchdf()
    print(df_desc.to_string())
except Exception as e:
    print(f"Error: {e}")

print("\n=== Check if FI_Star_View exists and its Customer Type Name column ===")
df_view = conn.execute("""
    SELECT DISTINCT "Customer Type Name", "Customer Type ID" 
    FROM FI_Star_View 
    LIMIT 10
""").fetchdf()
print(df_view.to_string())

print("\n=== Test direct JOIN to see if it works ===")
df_test = conn.execute("""
    SELECT DISTINCT 
        ft.customertypeid,
        COALESCE(ctt.LONG_DESCR, ctt.MEDIUM_DESCR, ctt.SHORT_DESCR) as customer_type_name_direct
    FROM FinancialTransactions ft
    LEFT JOIN CustomerType ct ON ft.customertypeid = ct.customertypeid
    LEFT JOIN CustomerTypeTexts ctt ON ct.customertypeid = ctt.CUSTOMERTYPEID
    LIMIT 10
""").fetchdf()
print(df_test.to_string())

# Check Customer Type Name aggregation
print("=== Customer Type Name Aggregation ===")
df = conn.execute("""
    SELECT 
        "Customer Type Name", 
        COUNT(*) as row_count, 
        SUM("Transaction Value Amount") as total
    FROM FI_Star_View 
    WHERE "Account Hierarchy Desc" = 'Gross Revenue' 
      AND "Version" = 'Actual'
    GROUP BY "Customer Type Name"
    ORDER BY total DESC
""").fetchdf()
print(df.to_string())

print("\n=== Customer Name Aggregation (showing Unassigned) ===")
df2 = conn.execute("""
    SELECT 
        "Customer Name", 
        "Customer Type Name",
        COUNT(*) as row_count, 
        SUM("Transaction Value Amount") as total
    FROM FI_Star_View 
    WHERE "Account Hierarchy Desc" = 'Gross Revenue' 
      AND "Version" = 'Actual'
    GROUP BY "Customer Name", "Customer Type Name"
    ORDER BY total DESC
    LIMIT 20
""").fetchdf()
print(df2.to_string())

print("\n=== Check for duplicate Customer Type IDs ===")
df3 = conn.execute("""
    SELECT 
        "Customer Type ID",
        "Customer Type Name",
        COUNT(*) as row_count
    FROM FI_Star_View 
    WHERE "Account Hierarchy Desc" = 'Gross Revenue' 
      AND "Version" = 'Actual'
    GROUP BY "Customer Type ID", "Customer Type Name"
    ORDER BY row_count DESC
""").fetchdf()
print(df3.to_string())

print("\n=== Check CustomerTypeTexts table for duplicates ===")
df4 = conn.execute("""
    SELECT * FROM CustomerTypeTexts
""").fetchdf()
print(df4.to_string())

conn.close()
