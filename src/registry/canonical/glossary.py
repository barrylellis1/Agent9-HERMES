"""
Canonical business glossary terms.

Seeded into every client's registry at onboarding time. Clients may add their
own industry-specific terms on top of these via EXTRA_GLOSSARY_TERMS in their
client definition file.
"""

from typing import Any, Dict, List

CORE_GLOSSARY_TERMS: List[Dict[str, Any]] = [
    {
        "id": "gross_revenue",
        "term": "Gross Revenue",
        "definition": "Total revenue before deductions such as discounts, returns, and allowances.",
        "domain": "Finance",
        "tags": ["finance", "revenue", "top-line"],
        "metadata": {},
    },
    {
        "id": "net_revenue",
        "term": "Net Revenue",
        "definition": "Gross revenue minus sales deductions (discounts, returns, rebates). The actual revenue recognised.",
        "domain": "Finance",
        "tags": ["finance", "revenue"],
        "metadata": {},
    },
    {
        "id": "gross_margin",
        "term": "Gross Margin",
        "definition": "Net revenue minus cost of goods sold (COGS), expressed as a percentage of net revenue.",
        "domain": "Finance",
        "tags": ["finance", "margin", "profitability"],
        "metadata": {},
    },
    {
        "id": "ebitda",
        "term": "EBITDA",
        "definition": "Earnings Before Interest, Taxes, Depreciation, and Amortisation. A proxy for operating cash generation.",
        "domain": "Finance",
        "tags": ["finance", "profitability", "ebitda"],
        "metadata": {},
    },
    {
        "id": "cogs",
        "term": "COGS",
        "definition": "Cost of Goods Sold — the direct costs attributable to producing goods or services sold.",
        "domain": "Finance",
        "tags": ["finance", "cost", "expense"],
        "metadata": {},
    },
    {
        "id": "sga",
        "term": "SG&A",
        "definition": "Selling, General and Administrative expenses — overhead costs not directly tied to production.",
        "domain": "Finance",
        "tags": ["finance", "expense", "opex"],
        "metadata": {},
    },
    {
        "id": "operating_income",
        "term": "Operating Income",
        "definition": "Revenue minus operating expenses (COGS + SG&A), before interest and taxes. Also called EBIT.",
        "domain": "Finance",
        "tags": ["finance", "profitability"],
        "metadata": {},
    },
    {
        "id": "yoy",
        "term": "Year-over-Year (YoY)",
        "definition": "Comparison of a metric in a given period to the same period in the prior year.",
        "domain": "Finance",
        "tags": ["finance", "comparison", "timeframe"],
        "metadata": {},
    },
    {
        "id": "qoq",
        "term": "Quarter-over-Quarter (QoQ)",
        "definition": "Comparison of a metric in a given quarter to the immediately preceding quarter.",
        "domain": "Finance",
        "tags": ["finance", "comparison", "timeframe"],
        "metadata": {},
    },
    {
        "id": "kpi",
        "term": "KPI",
        "definition": "Key Performance Indicator — a quantifiable metric used to evaluate the success of an activity against an objective.",
        "domain": "General",
        "tags": ["general", "measurement"],
        "metadata": {},
    },
]

# Quick lookup: id → definition
GLOSSARY_BY_ID: Dict[str, Dict[str, Any]] = {t["id"]: t for t in CORE_GLOSSARY_TERMS}
