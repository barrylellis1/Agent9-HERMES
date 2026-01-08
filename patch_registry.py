
import re
import os

REGISTRY_PATH = "src/registry/kpi/kpi_registry.yaml"

# New definitions with fixed SQL and removed filters
UPDATES = {
    "net_revenue": """  - id: net_revenue
    name: "Net Revenue"
    domain: "Finance"
    description: "Total net revenue (Gross Revenue - Sales Deductions)."
    unit: "$"
    data_product_id: "FI_Star_Schema"
    view_name: "FI_Star_View"
    business_process_ids:
      - "finance_revenue_growth_analysis"
      - "finance_profitability_analysis"
    base_column: "Transaction Value Amount"
    filters:
      "Parent Account/Group Description": "Net Revenue"
    thresholds:
      - comparison_type: "yoy"
        green_threshold: 0.10
        yellow_threshold: 0.0
        red_threshold: -0.05
        inverse_logic: false
    dimensions:
      - name: "Profit Center"
        field: "profit_center"
        description: "Business profit center"
    tags:
      - "revenue"
      - "financial"
    owner_role: "CFO"
    stakeholder_roles:
      - "CFO"
      - "CEO"
""",
    "operating_income": """  - id: operating_income
    name: "Operating Income"
    domain: "Finance"
    description: "Operating Income."
    unit: "$"
    data_product_id: "FI_Star_Schema"
    view_name: "FI_Star_View"
    business_process_ids:
      - "finance_profitability_analysis"
    base_column: "Transaction Value Amount"
    # Composite filter: Captures all branches rolling up to Op Income (Net Rev branch + Op Exp branch + Gross Margin branch)
    filters:
      "Parent Account/Group Description": 
        - "Net Revenue"
        - "Gross Margin"
        - "Building Expense"
        - "Employee Expense"
        - "Operating Expense"
    thresholds:
      - comparison_type: "yoy"
        green_threshold: 0.10
        yellow_threshold: 0.0
        red_threshold: -0.05
        inverse_logic: false
    dimensions:
      - name: "Profit Center"
        field: "profit_center"
        description: "Business profit center"
    tags:
      - "profitability"
      - "financial"
    owner_role: "CFO"
    stakeholder_roles:
      - "CFO"
      - "CEO"
""",
    "operating_expense": """  - id: operating_expense
    name: "Operating Expense"
    domain: "Finance"
    description: "Total Operating Expense."
    unit: "$"
    data_product_id: "FI_Star_Schema"
    view_name: "FI_Star_View"
    business_process_ids:
      - "finance_expense_management"
    base_column: "Transaction Value Amount"
    # Composite filter: Captures all branches rolling up to Op Expense
    filters:
      "Parent Account/Group Description": 
        - "Building Expense"
        - "Employee Expense"
        - "Operating Expense"
    thresholds:
      - comparison_type: "mom"
        green_threshold: -0.05
        yellow_threshold: 0.0
        red_threshold: 0.10
        inverse_logic: true
    dimensions:
      - name: "Profit Center"
        field: "profit_center"
        description: "Business profit center"
    tags:
      - "expense"
      - "financial"
    owner_role: "CFO"
    stakeholder_roles:
      - "CFO"
      - "Finance Manager"
""",
    "building_expense": """  - id: building_expense
    name: "Building Expense"
    domain: "Finance"
    description: "Total Building Expense (includes Periodic & Utilities)."
    unit: "$"
    data_product_id: "FI_Star_Schema"
    view_name: "FI_Star_View"
    business_process_ids:
      - "finance_expense_management"
      - "finance_facilities_management"
    base_column: "Transaction Value Amount"
    filters:
      "Parent Account/Group Description": "Building Expense"
    thresholds:
      - comparison_type: "mom"
        green_threshold: -0.05
        yellow_threshold: 0.0
        red_threshold: 0.10
        inverse_logic: true
    dimensions:
      - name: "Profit Center"
        field: "profit_center"
        description: "Business profit center"
    tags:
      - "expense"
      - "facilities"
      - "financial"
    owner_role: "Finance Manager"
    stakeholder_roles:
      - "Finance Manager"
      - "COO"
""",
    "employee_expense": """  - id: employee_expense
    name: "Employee Expense"
    domain: "Finance"
    description: "Total Employee Expense (includes Payroll, Travel, Office, Other)."
    unit: "$"
    data_product_id: "FI_Star_Schema"
    view_name: "FI_Star_View"
    business_process_ids:
      - "finance_expense_management"
      - "finance_human_resources"
    base_column: "Transaction Value Amount"
    filters:
      "Parent Account/Group Description": "Employee Expense"
    thresholds:
      - comparison_type: "mom"
        green_threshold: -0.05
        yellow_threshold: 0.0
        red_threshold: 0.10
        inverse_logic: true
    dimensions:
      - name: "Profit Center"
        field: "profit_center"
        description: "Business profit center"
    tags:
      - "expense"
      - "hr"
      - "financial"
    owner_role: "Finance Manager"
    stakeholder_roles:
      - "Finance Manager"
      - "CHRO"
""",
    "net_income": """  - id: net_income
    name: "Net Income"
    domain: "Finance"
    description: "Net Income."
    unit: "$"
    data_product_id: "FI_Star_Schema"
    view_name: "FI_Star_View"
    business_process_ids:
      - "finance_profitability_analysis"
      - "finance_investor_relations_reporting"
    base_column: "Transaction Value Amount"
    # Same as Op Income for MVP (assuming no interest/tax data)
    filters:
      "Parent Account/Group Description": 
        - "Net Revenue"
        - "Gross Margin"
        - "Building Expense"
        - "Employee Expense"
        - "Operating Expense"
    thresholds:
      - comparison_type: "yoy"
        green_threshold: 0.10
        yellow_threshold: 0.0
        red_threshold: -0.05
        inverse_logic: false
    dimensions:
      - name: "Profit Center"
        field: "profit_center"
        description: "Business profit center"
    tags:
      - "profitability"
      - "financial"
      - "bottom_line"
    owner_role: "CFO"
    stakeholder_roles:
      - "CFO"
      - "CEO"
      - "Investors"
""",
    "earnings_before_interest_and_taxes": """  - id: earnings_before_interest_and_taxes
    name: "Earnings Before Interest & Taxes"
    domain: "Finance"
    description: "Earnings Before Interest & Taxes (EBIT)."
    unit: "$"
    data_product_id: "FI_Star_Schema"
    view_name: "FI_Star_View"
    business_process_ids:
      - "finance_profitability_analysis"
      - "strategy_ebitda_growth_tracking"
    base_column: "Transaction Value Amount"
    # Same as Op Income for MVP
    filters:
      "Parent Account/Group Description": 
        - "Net Revenue"
        - "Gross Margin"
        - "Building Expense"
        - "Employee Expense"
        - "Operating Expense"
    thresholds:
      - comparison_type: "yoy"
        green_threshold: 0.10
        yellow_threshold: 0.0
        red_threshold: -0.05
        inverse_logic: false
    dimensions:
      - name: "Profit Center"
        field: "profit_center"
        description: "Business profit center"
    tags:
      - "profitability"
      - "financial"
      - "ebit"
    synonyms:
      - "EBIT"
    owner_role: "CFO"
    stakeholder_roles:
      - "CFO"
      - "CEO"
""",
    "cash_flow_from_operating_activities": """  - id: cash_flow_from_operating_activities
    name: "Cash Flow from Operating Activities"
    domain: "Finance"
    description: "Cash Flow from Operating Activities (CFO)."
    unit: "$"
    data_product_id: "FI_Star_Schema"
    view_name: "FI_Star_View"
    business_process_ids:
      - "finance_cash_flow_management"
    base_column: "Transaction Value Amount"
    filters:
      "Parent Account/Group Description": "Cash Flow from Operating Activities (CFO)"
    thresholds:
      - comparison_type: "yoy"
        green_threshold: 0.10
        yellow_threshold: 0.0
        red_threshold: -0.05
        inverse_logic: false
    dimensions:
      - name: "Profit Center"
        field: "profit_center"
        description: "Business profit center"
    tags:
      - "cash_flow"
      - "financial"
    synonyms:
      - "CFO"
      - "Operating Cash Flow"
    owner_role: "CFO"
    stakeholder_roles:
      - "CFO"
      - "CEO"
"""
}

def patch_file():
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    
    for kpi_id, replacement in UPDATES.items():
        print(f"Patching {kpi_id}...")
        # Pattern to find the KPI block
        # Start with "  - id: <kpi_id>" and capture until the next "  - id:" or EOF
        # We need to use re.DOTALL to match newlines
        pattern = r"(^  - id: " + re.escape(kpi_id) + r"\n.*?)(?=^  - id: |\Z)"
        
        match = re.search(pattern, new_content, flags=re.MULTILINE | re.DOTALL)
        if match:
            new_content = new_content.replace(match.group(1), replacement)
            print(f"  -> Replaced block for {kpi_id}")
        else:
            print(f"  -> Block not found for {kpi_id}")

    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Done.")

if __name__ == "__main__":
    patch_file()
