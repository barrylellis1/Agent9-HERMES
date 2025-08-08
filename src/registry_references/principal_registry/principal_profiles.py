from src.agents.models.a9_core_models import A9PrincipalContextProfile

# C-level principal profiles for Agent9

cfo_profile = A9PrincipalContextProfile(
    user_id="cfo_001",
    first_name="Lars",
    last_name="Mikkelsen",
    role="CFO",
    department="Finance",
    responsibilities=[
        "maximize EBIT",
        "manage revenue",
        "control expenses"
    ],
    business_processes=[
        "Finance: Profitability Analysis",
        "Finance: Revenue Growth Analysis",
        "Finance: Expense Management",
        "Finance: Cash Flow Management",
        "Finance: Budget vs. Actuals"
    ],

   default_filters={"profit_center_hierarchyid": "Total", "customer_hierarchyid": "Total"},
    typical_timeframes=["Monthly", "Quarterly"],
    principal_groups=["Executive Leadership", "Finance Committee"],
    persona_profile={
        "decision_style": "analytical",
        "risk_tolerance": "low",
        "communication_style": "concise",
        "values": ["accuracy", "compliance", "predictability"]
    },

    preferences={"channel": "Slack", "ui": "summary_dashboard"},
    permissions=["finance_read", "finance_write"],
    source="HR Database",
    description="CFO responsible for financial performance in EMEA."
)

ceo_profile = A9PrincipalContextProfile(
    user_id="ceo_001",
    first_name="Alex",
    last_name="Morgan",
    role="CEO",
    department="Executive",
    responsibilities=[
        "set strategic direction",
        "oversee company performance",
        "lead executive team"
    ],
    business_processes=[
        "Strategy: Market Share Analysis",
        "Strategy: EBITDA Growth Tracking",
        "Strategy: Capital Allocation Efficiency",
        "Operations: Global Performance Oversight",
        "Finance: Investor Relations Reporting"
    ],

    default_filters={"profit_center_hierarchyid": "#"},
    typical_timeframes=["Quarterly", "Annually"],
    principal_groups=["Executive Leadership", "Board of Directors"],
    persona_profile={
        "decision_style": "visionary",
        "risk_tolerance": "medium",
        "communication_style": "inspirational",
        "values": ["growth", "innovation", "leadership"]
    },

    preferences={"channel": "Email", "ui": "executive_dashboard"},
    permissions=["executive_read", "executive_write"],
    source="HR Database",
    description="CEO driving company strategy and performance."
)

coo_profile = A9PrincipalContextProfile(
    user_id="coo_001",
    first_name="Priya",
    last_name="Desai",
    role="COO",
    department="Operations",
    responsibilities=[
        "optimize operations",
        "reduce operational costs",
        "improve process efficiency"
    ],
    business_processes=[
        "Operations: Order-to-Cash Cycle Optimization",
        "Operations: Inventory Turnover Analysis",
        "Operations: Production Cost Management",
        "Supply Chain: Logistics Efficiency"
    ],

    default_filters={"profit_center_hierarchyid": "Best Run U", "customer_hierarchyid": "17100001"},
    typical_timeframes=["Monthly", "Quarterly"],
    principal_groups=["Executive Leadership", "Operations Committee"],
    persona_profile={
        "decision_style": "pragmatic",
        "risk_tolerance": "medium",
        "communication_style": "direct",
        "values": ["efficiency", "execution", "quality"]
    },
    preferences={"channel": "Email", "ui": "operations_dashboard"},
    permissions=["operations_read", "operations_write"],
    source="HR Database",
    description="COO focused on operational excellence and efficiency."
)

chro_profile = A9PrincipalContextProfile(
    user_id="chro_001",
    first_name="Sofia",
    last_name="Eriksson",
    role="CHRO",
    department="Human Resources",
    responsibilities=[
        "develop talent strategy",
        "manage organizational culture",
        "oversee employee engagement"
    ],
    business_processes=[
        "HR: Employee Attrition Rate Analysis",
        "HR: Recruitment Cycle Time",
        "HR: Compensation Ratio Analysis",
        "HR: Workforce Diversity Reporting"
    ],

    default_filters={"profit_center_hierarchyid": "Best Run U"},
    typical_timeframes=["Quarterly", "Annually"],
    principal_groups=["Executive Leadership", "HR Council"],
    persona_profile={
        "decision_style": "collaborative",
        "risk_tolerance": "medium",
        "communication_style": "empathetic",
        "values": ["inclusion", "development", "well-being"]
    },
    preferences={"channel": "Slack", "ui": "hr_dashboard"},
    permissions=["hr_read", "hr_write"],
    source="HR Database",
    description="CHRO responsible for talent strategy and organizational culture."
)

cmo_profile = A9PrincipalContextProfile(
    user_id="cmo_001",
    first_name="Mateo",
    last_name="Silva",
    role="CMO",
    department="Marketing",
    responsibilities=[
        "drive market growth",
        "manage brand",
        "lead marketing campaigns"
    ],
    business_processes=[
        "Marketing: Campaign ROI Analysis",
        "Marketing: Customer Acquisition Cost (CAC)",
        "Marketing: Customer Lifetime Value (CLV)",
        "Marketing: Brand Awareness Tracking"
    ],
    default_filters={"profit_center_hierarchyid": "Best Run U", "customer_hierarchyid": "17100001"},
    typical_timeframes=["Monthly", "Quarterly"],
    principal_groups=["Executive Leadership", "Marketing Council"],
    persona_profile={
        "decision_style": "creative",
        "risk_tolerance": "high",
        "communication_style": "persuasive",
        "values": ["creativity", "growth", "customer focus"]
    },
    preferences={"channel": "Slack", "ui": "marketing_dashboard"},
    permissions=["marketing_read", "marketing_write"],
    source="HR Database",
    description="CMO responsible for market expansion and brand leadership."
)

cio_profile = A9PrincipalContextProfile(
    user_id="cio_001",
    first_name="Jin",
    last_name="Park",
    role="CIO",
    department="IT",
    responsibilities=[
        "manage IT strategy",
        "ensure data security",
        "drive digital transformation"
    ],
    business_processes=[
        "IT: Project Spend vs. Budget",
        "IT: System Uptime/Downtime Analysis",
        "IT: Cybersecurity Incident Rate",
        "IT: Digital Transformation ROI"
    ],

    default_filters={"profit_center_hierarchyid": "Best Run U", "customer_hierarchyid": "17100001"},
    typical_timeframes=["Monthly", "Annually"],
    principal_groups=["Executive Leadership", "IT Steering Committee"],
    persona_profile={
        "decision_style": "systematic",
        "risk_tolerance": "low",
        "communication_style": "precise",
        "values": ["security", "innovation", "reliability"]
    },
    preferences={"channel": "Email", "ui": "it_dashboard"},
    permissions=["it_read", "it_write"],
    source="HR Database",
    description="CIO leading IT strategy and digital transformation."
)

cdo_profile = A9PrincipalContextProfile(
    user_id="cdo_001",
    first_name="Anika",
    last_name="Schneider",
    role="CDO",
    department="Data & Analytics",
    responsibilities=[
        "govern data assets",
        "drive data-driven culture",
        "ensure data compliance"
    ],
    business_processes=[
        "Data: Data Quality Score Tracking",
        "Data: Data Access Compliance Audits",
        "Data: Analytics Adoption Rate",
        "Data: Self-Service BI Usage"
    ],

    default_filters={"profit_center_hierarchyid": "Best Run U", "customer_hierarchyid": "17100001"},
    typical_timeframes=["Quarterly", "Annually"],
    principal_groups=["Executive Leadership", "Data Governance Board"],
    persona_profile={
        "decision_style": "evidence-based",
        "risk_tolerance": "medium",
        "communication_style": "informative",
        "values": ["compliance", "insight", "accuracy"]
    },
    preferences={"channel": "Slack", "ui": "data_dashboard"},
    permissions=["data_read", "data_write"],
    source="HR Database",
    description="CDO responsible for data governance and analytics."
)

# Dictionary for easy lookup
from .principal_roles import PrincipalRole

manager_profile = A9PrincipalContextProfile(
    user_id="manager_001",
    first_name="Morgan",
    last_name="Taylor",
    role="manager",
    department="Operations",
    responsibilities=[
        "manage team",
        "oversee projects",
        "report to executives"
    ],
    business_processes=[
        "Team: Productivity Metrics", 
        "Team: Project Milestone Tracking", 
        "Team: Budget Adherence"
    ],

    default_filters={"profit_center_hierarchyid": "Best Run U", "customer_hierarchyid": "17100001"},
    typical_timeframes=["Monthly", "Quarterly"],
    principal_groups=["Management Team"],
    persona_profile={"decision_style": "collaborative"},
    preferences={"channel": "Email", "ui": "manager_dashboard"},
    permissions=["manager_read", "manager_write"],
    source="HR Database",
    description="Manager responsible for team and project oversight."
)

default_principal_profiles = {
    PrincipalRole.CFO: cfo_profile,
    PrincipalRole.CEO: ceo_profile,
    PrincipalRole.COO: coo_profile,
    PrincipalRole.CHRO: chro_profile,
    PrincipalRole.CMO: cmo_profile,
    PrincipalRole.CIO: cio_profile,
    PrincipalRole.CDO: cdo_profile,
    PrincipalRole.MANAGER: manager_profile,  # Added manager profile
}
