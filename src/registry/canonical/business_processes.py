"""
Canonical business process taxonomy.

These definitions are the single source of truth. They are seeded into every
client's registry at onboarding time via scripts/onboard_client.py.

To add a new business process: add an entry here, then re-run onboard_client
for any clients that should have it.

Schema matches the Supabase `business_processes` table:
  id, name, domain, description, display_name, owner_role,
  stakeholder_roles, tags, metadata
"""

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Finance
# ---------------------------------------------------------------------------

FINANCE_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "finance_revenue_growth_analysis",
        "name": "Revenue Growth Analysis",
        "domain": "Finance",
        "display_name": "Finance: Revenue Growth Analysis",
        "description": "Tracking and analysis of revenue growth trends across channels, products, and periods",
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager", "COO"],
        "tags": ["finance", "revenue", "growth", "top-line"],
        "metadata": {},
    },
    {
        "id": "finance_profitability_analysis",
        "name": "Profitability Analysis",
        "domain": "Finance",
        "display_name": "Finance: Profitability Analysis",
        "description": "Analysis of profit margins, cost structures, and profit drivers",
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "tags": ["finance", "profitability", "margin", "analysis"],
        "metadata": {},
    },
    {
        "id": "finance_expense_management",
        "name": "Expense Management",
        "domain": "Finance",
        "display_name": "Finance: Expense Management",
        "description": "Monitoring and control of operating expenses, SG&A, and cost efficiency",
        "owner_role": "CFO",
        "stakeholder_roles": ["Finance Manager", "COO"],
        "tags": ["finance", "expense", "cost", "opex"],
        "metadata": {},
    },
    {
        "id": "finance_budget_vs_actuals",
        "name": "Budget vs. Actuals",
        "domain": "Finance",
        "display_name": "Finance: Budget vs. Actuals",
        "description": "Comparison of budgeted financial targets against actual performance",
        "owner_role": "CFO",
        "stakeholder_roles": ["Finance Manager", "Department Heads"],
        "tags": ["finance", "budget", "actuals", "variance"],
        "metadata": {},
    },
    {
        "id": "finance_cash_flow_management",
        "name": "Cash Flow Management",
        "domain": "Finance",
        "display_name": "Finance: Cash Flow Management",
        "description": "Monitoring of cash inflows, outflows, and liquidity position",
        "owner_role": "CFO",
        "stakeholder_roles": ["Finance Manager", "CEO"],
        "tags": ["finance", "cash", "liquidity", "working-capital"],
        "metadata": {},
    },
    {
        "id": "finance_investor_relations_reporting",
        "name": "Investor Relations Reporting",
        "domain": "Finance",
        "display_name": "Finance: Investor Relations Reporting",
        "description": "Financial reporting and communications for investors and stakeholders",
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Board"],
        "tags": ["finance", "investor", "reporting", "disclosure"],
        "metadata": {},
    },
    {
        "id": "financial_reporting",
        "name": "Financial Reporting",
        "domain": "Finance",
        "display_name": "Finance: Financial Reporting",
        "description": "Preparation and delivery of internal and external financial statements",
        "owner_role": "CFO",
        "stakeholder_roles": ["Finance Manager", "Auditors"],
        "tags": ["finance", "reporting", "statements", "compliance"],
        "metadata": {},
    },
    {
        "id": "tax_management",
        "name": "Tax Management",
        "domain": "Finance",
        "display_name": "Finance: Tax Management",
        "description": "Tax planning, compliance, and optimisation across jurisdictions",
        "owner_role": "CFO",
        "stakeholder_roles": ["Finance Manager"],
        "tags": ["finance", "tax", "compliance"],
        "metadata": {},
    },
]

# ---------------------------------------------------------------------------
# Strategy
# ---------------------------------------------------------------------------

STRATEGY_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "strategy_ebitda_growth_tracking",
        "name": "EBITDA Growth Tracking",
        "domain": "Strategy",
        "display_name": "Strategy: EBITDA Growth Tracking",
        "description": "Tracking EBITDA growth relative to targets and market benchmarks",
        "owner_role": "CEO",
        "stakeholder_roles": ["CFO", "Board"],
        "tags": ["strategy", "ebitda", "growth"],
        "metadata": {},
    },
    {
        "id": "strategy_market_share_analysis",
        "name": "Market Share Analysis",
        "domain": "Strategy",
        "display_name": "Strategy: Market Share Analysis",
        "description": "Analysis of market position and competitive share across segments",
        "owner_role": "CEO",
        "stakeholder_roles": ["CMO", "CFO"],
        "tags": ["strategy", "market-share", "competitive"],
        "metadata": {},
    },
    {
        "id": "strategy_capital_allocation_efficiency",
        "name": "Capital Allocation Efficiency",
        "domain": "Strategy",
        "display_name": "Strategy: Capital Allocation Efficiency",
        "description": "Evaluation of returns on capital invested across business units",
        "owner_role": "CEO",
        "stakeholder_roles": ["CFO", "Board"],
        "tags": ["strategy", "capital", "roic", "efficiency"],
        "metadata": {},
    },
]

# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

OPERATIONS_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "operations_inventory_turnover_analysis",
        "name": "Inventory Turnover Analysis",
        "domain": "Operations",
        "display_name": "Operations: Inventory Turnover Analysis",
        "description": "Analysis of inventory efficiency and stock turnover rates",
        "owner_role": "COO",
        "stakeholder_roles": ["Supply Chain Manager", "CFO"],
        "tags": ["operations", "inventory", "turnover"],
        "metadata": {},
    },
    {
        "id": "operations_manufacturing_efficiency",
        "name": "Manufacturing Efficiency",
        "domain": "Operations",
        "display_name": "Operations: Manufacturing Efficiency",
        "description": "Tracking of production efficiency, OEE, and waste reduction",
        "owner_role": "COO",
        "stakeholder_roles": ["Plant Manager"],
        "tags": ["operations", "manufacturing", "efficiency", "oee"],
        "metadata": {},
    },
    {
        "id": "operations_order_to_cash_cycle_optimization",
        "name": "Order-to-Cash Cycle Optimization",
        "domain": "Operations",
        "display_name": "Operations: Order-to-Cash Cycle Optimization",
        "description": "Optimisation of the end-to-end order fulfilment and payment collection process",
        "owner_role": "COO",
        "stakeholder_roles": ["Sales Manager", "Finance Manager"],
        "tags": ["operations", "order-to-cash", "cycle-time"],
        "metadata": {},
    },
    {
        "id": "order_processing",
        "name": "Order Processing",
        "domain": "Operations",
        "display_name": "Operations: Order Processing",
        "description": "Management and tracking of customer order processing workflows",
        "owner_role": "COO",
        "stakeholder_roles": ["Sales Manager"],
        "tags": ["operations", "orders", "fulfilment"],
        "metadata": {},
    },
]

# ---------------------------------------------------------------------------
# Supply Chain
# ---------------------------------------------------------------------------

SUPPLY_CHAIN_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "supply_chain_logistics_efficiency",
        "name": "Logistics Efficiency",
        "domain": "Supply Chain",
        "display_name": "Supply Chain: Logistics Efficiency",
        "description": "Tracking of logistics costs, delivery performance, and supply chain efficiency",
        "owner_role": "COO",
        "stakeholder_roles": ["Logistics Manager", "CFO"],
        "tags": ["supply-chain", "logistics", "delivery"],
        "metadata": {},
    },
]

# ---------------------------------------------------------------------------
# Sales
# ---------------------------------------------------------------------------

SALES_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "sales_management",
        "name": "Sales Management",
        "domain": "Sales",
        "display_name": "Sales: Sales Management",
        "description": "Management of sales pipeline, targets, and team performance",
        "owner_role": "Sales Manager",
        "stakeholder_roles": ["CEO", "CFO"],
        "tags": ["sales", "pipeline", "targets"],
        "metadata": {},
    },
    {
        "id": "sales_operations",
        "name": "Sales Operations",
        "domain": "Sales",
        "display_name": "Sales: Sales Operations",
        "description": "Sales process efficiency, tooling, and operational support",
        "owner_role": "Sales Manager",
        "stakeholder_roles": ["CFO"],
        "tags": ["sales", "operations", "enablement"],
        "metadata": {},
    },
]

# ---------------------------------------------------------------------------
# Marketing
# ---------------------------------------------------------------------------

MARKETING_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "marketing_campaign_roi_tracking",
        "name": "Campaign ROI Tracking",
        "domain": "Marketing",
        "display_name": "Marketing: Campaign ROI Tracking",
        "description": "Measurement of marketing campaign returns against investment",
        "owner_role": "CMO",
        "stakeholder_roles": ["CFO", "Marketing Manager"],
        "tags": ["marketing", "roi", "campaign"],
        "metadata": {},
    },
    {
        "id": "marketing_customer_acquisition_cost",
        "name": "Customer Acquisition Cost",
        "domain": "Marketing",
        "display_name": "Marketing: Customer Acquisition Cost",
        "description": "Tracking of cost per new customer acquired across channels",
        "owner_role": "CMO",
        "stakeholder_roles": ["CFO", "Sales Manager"],
        "tags": ["marketing", "cac", "acquisition"],
        "metadata": {},
    },
    {
        "id": "marketing_brand_sentiment_analysis",
        "name": "Brand Sentiment Analysis",
        "domain": "Marketing",
        "display_name": "Marketing: Brand Sentiment Analysis",
        "description": "Analysis of brand perception and customer sentiment across channels",
        "owner_role": "CMO",
        "stakeholder_roles": ["CEO"],
        "tags": ["marketing", "brand", "sentiment"],
        "metadata": {},
    },
]

# ---------------------------------------------------------------------------
# HR
# ---------------------------------------------------------------------------

HR_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "hr_employee_attrition_rate_analysis",
        "name": "Employee Attrition Rate Analysis",
        "domain": "HR",
        "display_name": "HR: Employee Attrition Rate Analysis",
        "description": "Tracking and analysis of employee turnover and retention rates",
        "owner_role": "CHRO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "tags": ["hr", "attrition", "retention", "turnover"],
        "metadata": {},
    },
    {
        "id": "hr_talent_acquisition_effectiveness",
        "name": "Talent Acquisition Effectiveness",
        "domain": "HR",
        "display_name": "HR: Talent Acquisition Effectiveness",
        "description": "Measurement of hiring quality, time-to-fill, and recruitment ROI",
        "owner_role": "CHRO",
        "stakeholder_roles": ["CEO"],
        "tags": ["hr", "recruitment", "talent"],
        "metadata": {},
    },
    {
        "id": "hr_compensation_ratio_analysis",
        "name": "Compensation Ratio Analysis",
        "domain": "HR",
        "display_name": "HR: Compensation Ratio Analysis",
        "description": "Analysis of pay equity, compensation ratios, and total reward competitiveness",
        "owner_role": "CHRO",
        "stakeholder_roles": ["CFO"],
        "tags": ["hr", "compensation", "pay-equity"],
        "metadata": {},
    },
    {
        "id": "hr_workforce_diversity_reporting",
        "name": "Workforce Diversity Reporting",
        "domain": "HR",
        "display_name": "HR: Workforce Diversity Reporting",
        "description": "Reporting on workforce diversity metrics and inclusion initiatives",
        "owner_role": "CHRO",
        "stakeholder_roles": ["CEO", "Board"],
        "tags": ["hr", "diversity", "inclusion", "dei"],
        "metadata": {},
    },
]

# ---------------------------------------------------------------------------
# IT
# ---------------------------------------------------------------------------

IT_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "it_system_uptime_downtime_analysis",
        "name": "System Uptime/Downtime Analysis",
        "domain": "IT",
        "display_name": "IT: System Uptime/Downtime Analysis",
        "description": "Tracking of system availability, incident frequency, and SLA compliance",
        "owner_role": "CTO",
        "stakeholder_roles": ["COO"],
        "tags": ["it", "uptime", "availability", "sla"],
        "metadata": {},
    },
    {
        "id": "it_cybersecurity_incident_rate",
        "name": "Cybersecurity Incident Rate",
        "domain": "IT",
        "display_name": "IT: Cybersecurity Incident Rate",
        "description": "Monitoring of security incidents, vulnerabilities, and response times",
        "owner_role": "CISO",
        "stakeholder_roles": ["CTO", "CEO"],
        "tags": ["it", "security", "cyber", "incidents"],
        "metadata": {},
    },
    {
        "id": "it_project_spend_vs_budget",
        "name": "Project Spend vs. Budget",
        "domain": "IT",
        "display_name": "IT: Project Spend vs. Budget",
        "description": "Tracking of IT project expenditure against approved budgets",
        "owner_role": "CTO",
        "stakeholder_roles": ["CFO"],
        "tags": ["it", "project", "budget", "spend"],
        "metadata": {},
    },
    {
        "id": "it_digital_transformation_roi",
        "name": "Digital Transformation ROI",
        "domain": "IT",
        "display_name": "IT: Digital Transformation ROI",
        "description": "Measurement of returns from digital transformation investments",
        "owner_role": "CTO",
        "stakeholder_roles": ["CEO", "CFO"],
        "tags": ["it", "digital", "transformation", "roi"],
        "metadata": {},
    },
]

# ---------------------------------------------------------------------------
# Compliance & Data
# ---------------------------------------------------------------------------

COMPLIANCE_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "compliance",
        "name": "Compliance Management",
        "domain": "Compliance",
        "display_name": "Compliance: Compliance Management",
        "description": "Management of regulatory compliance obligations and reporting",
        "owner_role": "CCO",
        "stakeholder_roles": ["CFO", "Legal"],
        "tags": ["compliance", "regulatory", "governance"],
        "metadata": {},
    },
    {
        "id": "data_access_compliance_audits",
        "name": "Data Access Compliance Audits",
        "domain": "Compliance",
        "display_name": "Compliance: Data Access Compliance Audits",
        "description": "Auditing of data access controls and governance compliance",
        "owner_role": "CCO",
        "stakeholder_roles": ["CTO", "Legal"],
        "tags": ["compliance", "data-access", "audit"],
        "metadata": {},
    },
]

DATA_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "data_quality_score_tracking",
        "name": "Data Quality Score Tracking",
        "domain": "Data",
        "display_name": "Data: Data Quality Score Tracking",
        "description": "Monitoring of data quality metrics across enterprise data assets",
        "owner_role": "CDO",
        "stakeholder_roles": ["CTO"],
        "tags": ["data", "quality", "governance"],
        "metadata": {},
    },
    {
        "id": "data_analytics_adoption_rate",
        "name": "Analytics Adoption Rate",
        "domain": "Data",
        "display_name": "Data: Analytics Adoption Rate",
        "description": "Tracking of analytics tool adoption and data-driven decision making",
        "owner_role": "CDO",
        "stakeholder_roles": ["CTO", "CEO"],
        "tags": ["data", "analytics", "adoption"],
        "metadata": {},
    },
    {
        "id": "data_self_service_bi_usage",
        "name": "Self-Service BI Usage",
        "domain": "Data",
        "display_name": "Data: Self-Service BI Usage",
        "description": "Measurement of self-service BI tool adoption and active usage",
        "owner_role": "CDO",
        "stakeholder_roles": ["CTO"],
        "tags": ["data", "bi", "self-service"],
        "metadata": {},
    },
]

# ---------------------------------------------------------------------------
# Pricing, Product, Team
# ---------------------------------------------------------------------------

PRICING_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "pricing_strategy",
        "name": "Pricing Strategy",
        "domain": "Pricing",
        "display_name": "Pricing: Pricing Strategy",
        "description": "Analysis and management of pricing models, elasticity, and margin optimisation",
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Sales Manager"],
        "tags": ["pricing", "strategy", "margin"],
        "metadata": {},
    },
    {
        "id": "product_management",
        "name": "Product Management",
        "domain": "Product",
        "display_name": "Product: Product Management",
        "description": "Management of product portfolio, roadmap, and lifecycle performance",
        "owner_role": "CPO",
        "stakeholder_roles": ["CEO", "Sales Manager"],
        "tags": ["product", "portfolio", "roadmap"],
        "metadata": {},
    },
]

TEAM_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "team_budget_adherence",
        "name": "Budget Adherence",
        "domain": "Team",
        "display_name": "Team: Budget Adherence",
        "description": "Team-level tracking of spending against allocated budgets",
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO", "Department Heads"],
        "tags": ["team", "budget", "adherence"],
        "metadata": {},
    },
    {
        "id": "team_productivity_metrics",
        "name": "Productivity Metrics",
        "domain": "Team",
        "display_name": "Team: Productivity Metrics",
        "description": "Measurement of team output, efficiency, and productivity indicators",
        "owner_role": "COO",
        "stakeholder_roles": ["Department Heads"],
        "tags": ["team", "productivity", "efficiency"],
        "metadata": {},
    },
    {
        "id": "team_project_milestone_tracking",
        "name": "Project Milestone Tracking",
        "domain": "Team",
        "display_name": "Team: Project Milestone Tracking",
        "description": "Tracking of project delivery milestones and schedule adherence",
        "owner_role": "PMO",
        "stakeholder_roles": ["COO", "Department Heads"],
        "tags": ["team", "project", "milestones"],
        "metadata": {},
    },
]

# ---------------------------------------------------------------------------
# Master list — all canonical business processes
# ---------------------------------------------------------------------------

ALL_BUSINESS_PROCESSES: List[Dict[str, Any]] = (
    FINANCE_BUSINESS_PROCESSES
    + STRATEGY_BUSINESS_PROCESSES
    + OPERATIONS_BUSINESS_PROCESSES
    + SUPPLY_CHAIN_BUSINESS_PROCESSES
    + SALES_BUSINESS_PROCESSES
    + MARKETING_BUSINESS_PROCESSES
    + HR_BUSINESS_PROCESSES
    + IT_BUSINESS_PROCESSES
    + COMPLIANCE_BUSINESS_PROCESSES
    + DATA_BUSINESS_PROCESSES
    + PRICING_BUSINESS_PROCESSES
    + TEAM_BUSINESS_PROCESSES
)

# Quick lookup: id → definition
BP_BY_ID: Dict[str, Dict[str, Any]] = {bp["id"]: bp for bp in ALL_BUSINESS_PROCESSES}
