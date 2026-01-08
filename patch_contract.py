
import re
import os

CONTRACT_PATH = "src/registry_references/data_product_registry/data_products/fi_star_schema.yaml"

# Define the updates for the contract
# We need to replace the blocks for specific KPIs.
# The format in the contract is slightly different (keys: name, calculation, filters, etc)

UPDATES = {
    "Net Revenue": """  - name: Net Revenue
    data_product_id: FI_Star_Schema
    description: "Total net revenue (Gross Revenue - Sales Deductions)."
    calculation: "SUM(\\"Transaction Value Amount\\") WHERE \\"Parent Account/Group Description\\" = 'Net Revenue'"
    filters:
      "Parent Account/Group Description": "Net Revenue"
    business_terms: ["Finance: Revenue Growth Analysis", "Finance: Profitability Analysis"]
    aggregation: SUM
    base_column: "Transaction Value Amount"
    join_tables: [FI_Star_View]
    diagnostic_questions:
      - "How does Net Revenue compare to Gross Revenue this period?"
      - "What is the trend of Net Revenue over the last 4 quarters?"
""",
    "Operating Income": """  - name: Operating Income
    data_product_id: FI_Star_Schema
    description: "Operating Income."
    # Complex filter: Includes Net Revenue branch, Gross Margin branch (COGS), and Op Expense branch
    calculation: "SUM(\\"Transaction Value Amount\\") WHERE \\"Parent Account/Group Description\\" IN (...)"
    business_terms: ["Finance: Profitability Analysis"]
    aggregation: SUM
    base_column: "Transaction Value Amount"
    filters:
      "Parent Account/Group Description": 
        - "Net Revenue"
        - "Gross Margin"
        - "Building Expense"
        - "Employee Expense"
        - "Operating Expense"
    join_tables: [FI_Star_View]
    diagnostic_questions:
      - "What is the operating income margin this quarter?"
      - "How does operating income compare to budget?"
""",
    "Operating Expense": """  - name: Operating Expense
    data_product_id: FI_Star_Schema
    description: "Total Operating Expense."
    # Complex filter: Direct children (Other) + Grandchildren via Building/Employee
    calculation: "SUM(\\"Transaction Value Amount\\") WHERE \\"Parent Account/Group Description\\" IN (...)"
    business_terms: ["Finance: Expense Management"]
    aggregation: SUM
    base_column: "Transaction Value Amount"
    filters:
      "Parent Account/Group Description": 
        - "Building Expense"
        - "Employee Expense"
        - "Operating Expense"
    join_tables: [FI_Star_View]
    diagnostic_questions:
      - "Which category of operating expense is growing the fastest?"
      - "How does total operating expense compare to the previous year?"
""",
    "Building Expense": """  - name: Building Expense
    data_product_id: FI_Star_Schema
    description: "Total Building Expense (includes Periodic & Utilities)."
    calculation: "SUM(\\"Transaction Value Amount\\") WHERE \\"Parent Account/Group Description\\" = 'Building Expense'"
    filters:
      "Parent Account/Group Description": "Building Expense"
    business_terms: ["Finance: Expense Management", "Finance: Facilities Management"]
    aggregation: SUM
    base_column: "Transaction Value Amount"
    join_tables: [FI_Star_View]
""",
    "Employee Expense": """  - name: Employee Expense
    data_product_id: FI_Star_Schema
    description: "Total Employee Expense (includes Payroll, Travel, Office, Other)."
    calculation: "SUM(\\"Transaction Value Amount\\") WHERE \\"Parent Account/Group Description\\" = 'Employee Expense'"
    filters:
      "Parent Account/Group Description": "Employee Expense"
    business_terms: ["Finance: Expense Management", "Finance: Human Resources"]
    aggregation: SUM
    base_column: "Transaction Value Amount"
    join_tables: [FI_Star_View]
""",
    "Net Income": """  - name: Net Income
    data_product_id: FI_Star_Schema
    description: "Net Income."
    # Same as Operating Income for MVP coverage
    calculation: "SUM(\\"Transaction Value Amount\\") WHERE \\"Parent Account/Group Description\\" IN (...)"
    business_terms: ["Finance: Profitability Analysis", "Finance: Investor Relations Reporting"]
    aggregation: SUM
    base_column: "Transaction Value Amount"
    filters:
      "Parent Account/Group Description": 
        - "Net Revenue"
        - "Gross Margin"
        - "Building Expense"
        - "Employee Expense"
        - "Operating Expense"
    join_tables: [FI_Star_View]
    diagnostic_questions:
      - "What is the net income for the current fiscal year?"
      - "How does net income compare to the same period last year?"
""",
    "Earnings Before Interest & Taxes": """  - name: Earnings Before Interest & Taxes
    data_product_id: FI_Star_Schema
    description: "Earnings Before Interest & Taxes (EBIT)."
    # Same as Operating Income for MVP coverage
    calculation: "SUM(\\"Transaction Value Amount\\") WHERE \\"Parent Account/Group Description\\" IN (...)"
    business_terms: ["Finance: Profitability Analysis", "Strategy: EBITDA Growth Tracking"]
    aggregation: SUM
    base_column: "Transaction Value Amount"
    filters:
      "Parent Account/Group Description": 
        - "Net Revenue"
        - "Gross Margin"
        - "Building Expense"
        - "Employee Expense"
        - "Operating Expense"
    join_tables: [FI_Star_View]
    synonyms: ["EBIT"]
    diagnostic_questions:
      - "What is the EBIT margin for the current quarter?"
""",
    "Cash Flow from Operating Activities": """  - name: Cash Flow from Operating Activities
    data_product_id: FI_Star_Schema
    description: "Cash Flow from Operating Activities (CFO)."
    calculation: "SUM(\\"Transaction Value Amount\\") WHERE \\"Parent Account/Group Description\\" = 'Cash Flow from Operating Activities (CFO)'"
    filters:
      "Parent Account/Group Description": "Cash Flow from Operating Activities (CFO)"
    business_terms: ["Finance: Cash Flow Management"]
    aggregation: SUM
    base_column: "Transaction Value Amount"
    join_tables: [FI_Star_View]
    synonyms: ["CFO", "Operating Cash Flow"]
"""
}

def patch_contract():
    with open(CONTRACT_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    
    for kpi_name, replacement in UPDATES.items():
        print(f"Patching {kpi_name}...")
        # Pattern to find the KPI block in contract
        # Start with "  - name: <kpi_name>" and capture until the next "  - name:" or EOF
        pattern = r"(^  - name: " + re.escape(kpi_name) + r"\n.*?)(?=^  - name: |\Z)"
        
        match = re.search(pattern, new_content, flags=re.MULTILINE | re.DOTALL)
        if match:
            new_content = new_content.replace(match.group(1), replacement)
            print(f"  -> Replaced block for {kpi_name}")
        else:
            print(f"  -> Block not found for {kpi_name}")

    with open(CONTRACT_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Done.")

if __name__ == "__main__":
    patch_contract()
