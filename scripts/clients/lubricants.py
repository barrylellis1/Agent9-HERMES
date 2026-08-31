"""
Lubricants Business client — BigQuery backend.
Client ID: lubricants
Data product: dp_lubricants_financials (BigQuery LubricantsBusiness dataset)

BP ID fix applied here:
  KPIs previously seeded with business_process_ids=['finance_revenue_growth']
  corrected to ['finance_revenue_growth_analysis'] to match the canonical taxonomy.
"""

import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.registry.canonical.business_processes import (
    FINANCE_BUSINESS_PROCESSES,
    STRATEGY_BUSINESS_PROCESSES,
    PRICING_BUSINESS_PROCESSES,
    OPERATIONS_BUSINESS_PROCESSES,
    SALES_BUSINESS_PROCESSES,
)

CLIENT_ID = "lubricants"

CLIENT_META = {
    "id": CLIENT_ID,
    "name": "Lubricants Business",
    "industry": "Oil & Gas / Specialty Chemicals",
    "data_product_ids": ["dp_lubricants_financials", "dp_lubricants_sales"],
    # --- Corporate value model (Phase 15 Stage J) --------------------------
    # AUTHORED, not inferred. These are preferences, not facts — there is no
    # correct value to converge on and nothing to tune toward, so they must be
    # stated by whoever owns the strategy. Set here as demo values because we
    # own this client; a real customer authors their own.
    #
    # Derived from what this client's own data shows: mature product lines
    # (Synthetic Blend / Conventional / Premium / Value), gross margin under
    # base-oil cost pressure, and a contractual price-lock on the anchor
    # account that a wrong move would breach. Defend the margin, and weight
    # risk as heavily as impact because the downside here is a broken contract.
    "strategic_posture": "margin defense",
    "tradeoff_weights": {"impact": 0.4, "cost": 0.2, "risk": 0.4},
}

DATA_PRODUCT = {
    "id": "dp_lubricants_financials",
    "client_id": CLIENT_ID,
    "name": "Lubricants Business Financial Analytics",
    "domain": "Finance",
    "source_system": "bigquery",
    "description": (
        "BigQuery dataset covering the full P&L for the Lubricants Business division. "
        "Includes revenue by channel and product line, COGS by component, and SG&A."
    ),
    "owner": "Finance",
    "owner_role": "CFO",
    "metadata": {
        "source_system": "bigquery",
        "bigquery_project": "agent9-465818",
        "bigquery_dataset": "LubricantsBusiness",
        # SIGN CONVENTION -- declared because its absence caused a real defect.
        # In this view `amount` is SIGNED: Revenue is positive, and COGS / SGA /
        # Other (D&A, Interest, Tax) are stored NEGATIVE. Every P&L line therefore
        # SUMS -- no CASE-based negation is needed or correct.
        #
        # Nothing declared this before, so KPI authors guessed and split two ways:
        # derived KPIs negated COGS (adding cost to revenue -> gross margin read
        # 166.75% instead of 33.25%), while cost KPIs passed the negative straight
        # through to a registry that declares unit '$' with inverse_logic=True,
        # inverting every threshold verdict (COGS +8.0% YoY graded GREEN).
        #
        # Rule for new KPIs: sum signed amounts for P&L aggregates; negate ONLY
        # when presenting a standalone cost as a positive magnitude, to match the
        # registry's positive_trend_is_good=false convention.
        "sign_convention": "signed",
        "positive_account_types": ["Revenue"],
        "negative_account_types": ["COGS", "SGA", "Other"],
        # Phase 16 step 1 (DEVELOPMENT_PLAN.md) -- the one real consumer
        # (A9_Data_Product_Agent._collect_group_by_items, tier 4) already reads
        # this from DataProduct.metadata, so no schema change needed for this
        # field specifically, only seeding it. Business-term short names
        # (resolved to technical columns later via `business_terms` below),
        # not raw column names -- _collect_group_by_items' own docstring:
        # "raw attribute names (not yet resolved to technical columns)".
        "fallback_group_by_dimensions": ["product_line", "channel", "profit_center"],
    },
    "time_dimensions": [
        {
            "type": "fiscal_year_period",
            "year_column": "fiscal_year",
            "period_column": "fiscal_period",
            "period_column_type": "string",
            "period_type": "month",
            "column": "",
            "source_columns": ["fiscal_year", "fiscal_period"],
            "display_expr": "CONCAT(CAST(fiscal_year AS STRING), '-', fiscal_period)",
            "sort_expr": "fiscal_year * 100 + CAST(fiscal_period AS INT64)",
            "label": "Fiscal Period",
            "granularity": "month",
            "primary": True,
        },
    ],
    # Phase 16 step 1 (DEVELOPMENT_PLAN.md) -- the one LIVE contract read
    # (A9_Deep_Analysis_Agent._dims_from_contract) came only from
    # src/registry_references/data_product_registry/data_products/
    # lubricants_star_schema.yaml until now. Declared order copied verbatim
    # from that YAML's views[].llm_profile.dimension_semantics, cross-checked
    # 2026-08-29 against the REAL BigQuery view schema
    # (agent9-465818.LubricantsBusiness.LubricantsStarSchemaView) -- all 17
    # columns confirmed to actually exist, not just present in the fixture.
    # _dims_from_contract applies its own ban-list filter (flags, _id,
    # transaction_date, version, fiscal ytd/qtd/mtd) at read time, same as it
    # always has for the YAML source -- this list is the full declared order,
    # unfiltered, matching "honoured verbatim" in that method's own docstring.
    "dimension_semantics": [
        "product_name", "product_line", "product_category",
        "customer_name", "customer_segment", "customer_region",
        "profit_center_name", "business_unit",
        "channel_name", "channel_type",
        "account_name", "account_type", "account_category", "account_group",
        "fiscal_year", "fiscal_period", "transaction_date",
    ],
    # Phase 16 step 2 (DEVELOPMENT_PLAN.md) -- the canonical, enforced version
    # of the metadata.sign_convention/positive_account_types/negative_account_types
    # fields above. Those predate this field, are read by zero agent code (only
    # written by this seed script), and are left in place rather than removed --
    # harmless, and removing them buys nothing. This field is what
    # src/registry/validators/measure_semantics_validator.py actually consumes.
    "measure_semantics": {
        "type_column": "account_type",
        "amount_column": "amount",
        "stored_sign": {"Revenue": "positive", "COGS": "negative", "SGA": "negative", "Other": "negative"},
    },
    # Phase 16 step 4 (DEVELOPMENT_PLAN.md) -- ported from lubricants_star_
    # schema.yaml's column_aliases: section. Never actually reached in
    # practice (source_system=bigquery routes explicitly in
    # generate_sql_for_kpi before this fallback), seeded anyway for
    # consistency and so the registry is a complete substitute for the YAML.
    "column_aliases": {
        "measure": "amount",
        "date": "transaction_date",
        "version": "version",
        "default_version_value": "Actual",
    },
    # Phase 16 step 5 (DEVELOPMENT_PLAN.md) -- ported verbatim from
    # lubricants_star_schema.yaml's views[].llm_profile.exposed_columns:
    # section. Never actually reached in practice (source_system=bigquery
    # routes explicitly before this last-resort fallback), seeded anyway so
    # the registry is a complete substitute for the YAML before it's deleted.
    # Keyed by lowercased view name, matching _get_exposed_columns' own key.
    "exposed_columns": {
        "lubricantsstarschemaview": [
            "transaction_id", "fiscal_year", "fiscal_period", "transaction_date",
            "amount", "version", "currency",
            "account_name", "account_type", "account_category", "account_group",
            "product_name", "product_line", "product_category",
            "customer_name", "customer_segment", "customer_region",
            "profit_center_name", "business_unit",
            "channel_name", "channel_type",
        ],
    },
}

_VIEW = "LubricantsStarSchemaView"
_BQ_PREFIX = f"`agent9-465818.LubricantsBusiness.{_VIEW}`"

_DIMS = [
    {"name": "Profit Center", "field": "profit_center_name"},
    {"name": "Customer Segment", "field": "customer_segment"},
    {"name": "Product Line", "field": "product_line"},
    {"name": "Channel", "field": "channel"},
    {"name": "Region", "field": "region"},
]

# ---------------------------------------------------------------------------
# Sales data product (Aug 2026) — LubricantsSalesStarView
#
# Order/line-level Sales data, generated by scripts/generate_lubricants_sales_data.py
# as a direct decomposition of the SAME revenue basis FinancialTransactions uses
# (see that script's docstring) -- SUM(net_amount) here reconciles exactly to the
# Net Revenue KPI above, to the cent, for any slice. This is deliberate: Sales
# adds order-volume and fulfillment truth underneath the Finance dollar view
# (a physical/operational layer the Finance-only data product cannot express),
# rather than an independently-sampled dataset that merely looks similar.
# ---------------------------------------------------------------------------

_SALES_DP_ID = "dp_lubricants_sales"
_SALES_VIEW = "LubricantsSalesStarView"
_SALES_BQ_PREFIX = f"`agent9-465818.LubricantsBusiness.{_SALES_VIEW}`"

SALES_DATA_PRODUCT: Dict[str, Any] = {
    "id": _SALES_DP_ID,
    "client_id": CLIENT_ID,
    "name": "Lubricants Sales Orders",
    "domain": "Sales",
    "source_system": "bigquery",
    "description": (
        "BigQuery dataset covering Sales Order header and line-item detail for the "
        "Lubricants Business division -- order volume, units sold, and fulfillment "
        "status underneath the Finance revenue figures. Net amount reconciles "
        "exactly to dp_lubricants_financials' Net Revenue KPI (same generation basis)."
    ),
    "owner": "Sales Operations",
    "owner_role": "COO",
    "metadata": {
        "source_system": "bigquery",
        "bigquery_project": "agent9-465818",
        "bigquery_dataset": "LubricantsBusiness",
        "reconciles_to": "dp_lubricants_financials.net_revenue",
    },
    # Three genuinely distinct dates live on this data product (order / delivery /
    # revenue-recognition), and they disagree: 90.2% of line items have delivery_date
    # in a DIFFERENT fiscal month than the period their revenue was actually
    # recognized in (verified live, Aug 2026 -- a 15-60 day shipping lag routinely
    # crosses a month boundary). fiscal_year_period is PRIMARY because 4 of the 5
    # Sales KPIs below (order count, units sold, avg order value) are volume/value
    # metrics that must reconcile to Finance's recognition period, matching
    # dp_lubricants_financials' own time_dimensions convention exactly (same
    # fiscal_year_start_month=1 default, same zero-padded fiscal_period format).
    # order_date and delivery_date are kept as non-primary entries -- captured for
    # a genuinely delivery-keyed KPI (e.g. order_fulfillment_rate) once per-KPI time
    # dimension selection exists; see docs/architecture/data_product_time_dimension_planning.md.
    # DPA's _resolve_time_spec (a9_data_product_agent.py) only consults the PRIMARY
    # entry today -- there is no per-KPI override yet, so order_fulfillment_rate and
    # order_cancellation_rate below are ALSO filtered by fiscal_year_period for now,
    # not by their own more-correct date. Known, tracked, not silently accepted.
    "time_dimensions": [
        {
            "type": "fiscal_year_period",
            "year_column": "fiscal_year",
            "period_column": "fiscal_period",
            "period_column_type": "string",
            "period_type": "month",
            "column": "",
            "source_columns": ["fiscal_year", "fiscal_period"],
            "display_expr": "CONCAT(CAST(fiscal_year AS STRING), '-', fiscal_period)",
            "sort_expr": "fiscal_year * 100 + CAST(fiscal_period AS INT64)",
            "label": "Fiscal Period (Revenue Recognition)",
            "granularity": "month",
            "primary": True,
        },
        {
            "type": "date",
            "column": "order_date",
            "label": "Order Date",
            "granularity": "month",
            "primary": False,
        },
        {
            "type": "date",
            "column": "delivery_date",
            "label": "Delivery Date",
            "granularity": "month",
            "primary": False,
        },
    ],
}

_SALES_DIMS = [
    {"name": "Product Line", "field": "product_line"},
    {"name": "Customer Segment", "field": "customer_segment"},
    {"name": "Sales Org", "field": "sales_org"},
]

DATA_PRODUCTS: List[Dict[str, Any]] = [DATA_PRODUCT, SALES_DATA_PRODUCT]

KPIS: List[Dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # Revenue KPIs — business_process_ids corrected to finance_revenue_growth_analysis
    # -----------------------------------------------------------------------
    {
        "id": "net_revenue",
        "client_id": CLIENT_ID,
        "name": "Net Revenue",
        "domain": "Finance",
        "description": "Total net revenue across all channels and product lines",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis", "finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "plan_version_value": "Budget",
        # Phase 17 T1 (docs/architecture/kpi_semantic_contract.md §3): a segment's
        # revenue dollars genuinely sum to the enterprise total -- the plain-vanilla
        # additive case §3 contrasts gross_margin_pct against.
        "unit_class": "currency",
        "additive_across_dimensions": True,
        "aggregation_method": "sum",
        "sign_convention": "natural",
        "inverse_logic": False,
        "scope_eligible": "both",
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
            {"comparison_type": "qoq", "green_threshold": 3.0, "yellow_threshold": -2.0, "red_threshold": -8.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "top-line", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO", "Finance Manager"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "product_sales_revenue",
        "client_id": CLIENT_ID,
        "name": "Product Sales Revenue",
        "domain": "Finance",
        "description": "Revenue from product sales (excludes service revenue)",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_category = 'Product Sales' AND version = 'Actual'",
        "filters": {"account_category": "Product Sales", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "product-sales", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "service_revenue",
        "client_id": CLIENT_ID,
        "name": "Service Revenue",
        "domain": "Finance",
        "description": "Revenue from service contracts and technical services",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_category = 'Service Revenue' AND version = 'Actual'",
        "filters": {"account_category": "Service Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 8.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "services", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["COO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "b2b_revenue",
        "client_id": CLIENT_ID,
        "name": "B2B Revenue",
        "domain": "Finance",
        "description": "Revenue from B2B channel customers",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        # WAS channel_name = 'B2B', which matches zero rows -- the actual channel
        # value is 'B2B Direct Sales', so this KPI returned None since seeding.
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE channel_name = 'B2B Direct Sales' AND account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"channel": "B2B Direct Sales", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "b2b", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "ecommerce_revenue",
        "client_id": CLIENT_ID,
        "name": "E-Commerce Revenue",
        "domain": "Finance",
        "description": "Revenue from digital / e-commerce channel",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE channel_name = 'E-Commerce' AND account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"channel": "E-Commerce", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 15.0, "yellow_threshold": 5.0, "red_threshold": 0.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "ecommerce", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["COO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "avg_transaction_value",
        "client_id": CLIENT_ID,
        "name": "Average Transaction Value",
        "domain": "Finance",
        "description": "Average revenue per transaction across all channels",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT AVG(amount) AS value FROM {_BQ_PREFIX} WHERE account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 3.0, "yellow_threshold": 0.0, "red_threshold": -3.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "transaction-value", "lubricants"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "premium_mix_pct",
        "client_id": CLIENT_ID,
        "name": "Premium Product Mix %",
        "domain": "Finance",
        "description": "Percentage of revenue from premium product lines",
        "unit": "%",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis", "finance_profitability_analysis"],
        "sql_query": f"SELECT ROUND(100.0 * SUM(CASE WHEN product_category = 'Premium' THEN amount ELSE 0 END) / NULLIF(SUM(amount), 0), 2) AS value FROM {_BQ_PREFIX} WHERE account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 2.0, "yellow_threshold": 0.0, "red_threshold": -2.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "premium-mix", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    # -----------------------------------------------------------------------
    # Profitability / Margin KPIs
    # -----------------------------------------------------------------------
    {
        "id": "gross_profit",
        "client_id": CLIENT_ID,
        "name": "Gross Profit",
        "domain": "Finance",
        "description": "Net revenue minus cost of goods sold",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        # amount is signed (COGS already negative) -- summing IS gross profit.
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_type IN ('Revenue', 'COGS') AND version = 'Actual'",
        "filters": {"version": "Actual"},
        "plan_version_value": "Budget",
        # Phase 17 T1 -- a signed sum of two additive components is itself
        # additive: segment gross-profit dollars sum to the enterprise total.
        "unit_class": "currency",
        "additive_across_dimensions": True,
        "aggregation_method": "sum",
        "sign_convention": "natural",
        "inverse_logic": False,
        "scope_eligible": "both",
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "profitability", "gross-profit", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "gross_margin_pct",
        "client_id": CLIENT_ID,
        "name": "Gross Margin %",
        "domain": "Finance",
        "description": "Gross profit as a percentage of net revenue",
        "unit": "%",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        # Gross profit (signed sum of Revenue + COGS) over revenue.
        "sql_query": f"SELECT ROUND(100.0 * SUM(CASE WHEN account_type IN ('Revenue', 'COGS') THEN amount ELSE 0 END) / NULLIF(SUM(CASE WHEN account_type = 'Revenue' THEN amount ELSE 0 END), 0), 2) AS value FROM {_BQ_PREFIX} WHERE version = 'Actual'",
        "filters": {"version": "Actual"},
        # Phase 17 T1 -- the flagship case docs/architecture/kpi_semantic_contract.md
        # §3 exists to name: this is the KPI whose segment percentages were summed
        # into a claimed -53pp enterprise move against an actual ~-5pp move.
        # scope_eligible='both': an enterprise-level margin % IS a legitimate figure
        # (this KPI's own reported value at scope=enterprise) -- what's illegitimate
        # is deriving it by SUMMING segment margins instead of the weighted
        # calculation aggregation_method names.
        "unit_class": "ratio",
        "additive_across_dimensions": False,
        "aggregation_method": "weighted_avg",
        "weight_column": "net_revenue",
        "sign_convention": "natural",
        "inverse_logic": False,
        "scope_eligible": "both",
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 1.0, "yellow_threshold": 0.0, "red_threshold": -1.5, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "margin", "gross-margin", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        # kpi_type='ratio' + the two bridge queries switch Deep Analysis onto its
        # ratio-aware path (`_maps_for_level`). Without them DA falls through to the
        # generic path, where a segment's `delta` is its own raw pp change — and raw
        # pp changes are NOT additive across segments. The Variance Breakdown header
        # summed them anyway and reported -53pp against an enterprise move of ~-5pp.
        #
        # On the bridge path DA fetches gross profit and revenue SEPARATELY per
        # segment, computes each segment's margin, and reports `delta` as a
        # REVENUE-WEIGHTED contribution (rev_share x rate_change). Those DO sum to
        # the enterprise change, which is what makes a variance decomposition
        # legitimate rather than decorative.
        #
        # Both must be full SELECT ... FROM statements: the DPA lifts the expression
        # between SELECT and FROM and re-hosts it under its own GROUP BY.
        "metadata": {
            "line": "bottom",
            "altitude": "strategic",
            "positive_trend_is_good": "true",
            "kpi_type": "ratio",
            "bridge_numerator_sql": f"SELECT SUM(CASE WHEN account_type IN ('Revenue', 'COGS') THEN amount ELSE 0 END) AS value FROM {_BQ_PREFIX} WHERE version = 'Actual'",
            "bridge_denominator_sql": f"SELECT SUM(CASE WHEN account_type = 'Revenue' THEN amount ELSE 0 END) AS value FROM {_BQ_PREFIX} WHERE version = 'Actual'",
        },
    },
    {
        "id": "operating_income",
        "client_id": CLIENT_ID,
        "name": "Operating Income",
        "domain": "Finance",
        "description": "Gross profit minus SG&A and other operating expenses (EBIT)",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        # EBIT = Revenue - COGS - SGA - D&A, all signed so it is a plain SUM.
        # D&A lives in account_category 'D&A' under account_type 'Other'; Interest
        # and Tax share that account_type and must stay excluded (they are below EBIT).
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE (account_type IN ('Revenue', 'COGS', 'SGA') OR account_category = 'D&A') AND version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "profitability", "operating-income", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "ebitda",
        "client_id": CLIENT_ID,
        "name": "EBITDA",
        "domain": "Finance",
        "description": "Earnings before interest, taxes, depreciation, and amortisation",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        # EBITDA = earnings BEFORE D&A, so D&A is excluded (this is EBIT + D&A).
        # The previous filter added account_type 'DA', which matches zero rows --
        # D&A is an account_CATEGORY under 'Other' -- so this KPI silently returned
        # a value identical to operating_income, and the two were also inverted:
        # the old operating_income excluded D&A (making it EBITDA) while this one
        # tried to include it (making it EBIT).
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_type IN ('Revenue', 'COGS', 'SGA') AND version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "profitability", "ebitda", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Board"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    # -----------------------------------------------------------------------
    # Cost / Expense KPIs
    # -----------------------------------------------------------------------
    {
        "id": "cogs",
        "client_id": CLIENT_ID,
        "name": "Cost of Goods Sold",
        "domain": "Finance",
        "description": "Total direct cost of producing and delivering products",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management", "finance_profitability_analysis"],
        # Negated to a positive magnitude so rising cost = rising number, which is
        # what this KPI's inverse_logic=True / positive_trend_is_good=false assume.
        # Passing the raw negative through made an 8.0% YoY cost INCREASE compute as
        # percent_change = -8.0% and grade GREEN. Negation (not ABS) on purpose: ABS
        # would hide a segment that legitimately nets positive from credits/returns.
        "sql_query": f"SELECT -SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_type = 'COGS' AND version = 'Actual'",
        "filters": {"account_type": "COGS", "version": "Actual"},
        "plan_version_value": "Budget",
        # Phase 17 T1 -- a segment's COGS dollars genuinely sum to the enterprise
        # total (additive_across_dimensions=true), unlike gross_margin_pct above.
        # sign_convention='negative_stored' names the fact the negation comment
        # above already reasons about: the underlying data stores COGS negative,
        # and this KPI's own SQL flips it to a positive magnitude for display.
        "unit_class": "currency",
        "additive_across_dimensions": True,
        "aggregation_method": "sum",
        "sign_convention": "negative_stored",
        "inverse_logic": True,
        "scope_eligible": "both",
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": -3.0, "yellow_threshold": 3.0, "red_threshold": 8.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cost", "cogs", "lubricants"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "base_oil_cost",
        "client_id": CLIENT_ID,
        # Id kept as base_oil_cost: it is referenced by the causal edges and the
        # kpi_accountability rows, and ids are semantic identifiers we do not churn.
        # Name/description say "raw materials" because that is what the data is.
        "name": "Raw Materials Cost",
        "domain": "Finance",
        "description": (
            "Raw materials cost — predominantly base oil, the primary input for "
            "lubricant blending. Sourced from account_category 'Raw Materials' "
            "(~41% of COGS); the warehouse carries no base-oil-specific line."
        ),
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        # WAS account_category = 'Base Oil', which matches ZERO rows -- this KPI
        # returned None from the day it was seeded. It is the source node of the
        # `confirmed` base_oil_cost -> cogs causal edge, so that edge could never
        # fire numerically; the grounding text still read convincingly because
        # mechanism/lag/provenance are static registry strings.
        #
        # 'Raw Materials' is the real category and the closest true equivalent: it
        # is 122.0M of 293.8M COGS (41.5%), and base oil is the dominant raw-material
        # input for a lubricants blender. It is NOT a base-oil-only line, so the name
        # and description say raw materials -- do not let the id imply more precision
        # than the warehouse actually carries.
        "sql_query": f"SELECT -SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_category = 'Raw Materials' AND version = 'Actual'",
        "filters": {"account_category": "Raw Materials", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": -5.0, "yellow_threshold": 5.0, "red_threshold": 15.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cost", "raw-materials", "base-oil", "lubricants"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "distribution_cost",
        "client_id": CLIENT_ID,
        "name": "Distribution Cost",
        "domain": "Finance",
        "description": "Total logistics and distribution costs for product delivery",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": f"SELECT -SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_category = 'Distribution' AND version = 'Actual'",
        "filters": {"account_category": "Distribution", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": -3.0, "yellow_threshold": 3.0, "red_threshold": 8.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cost", "distribution", "logistics", "lubricants"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "sga_expense",
        "client_id": CLIENT_ID,
        "name": "SG&A Expense",
        "domain": "Finance",
        "description": "Selling, general and administrative expenses",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": f"SELECT -SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_type = 'SGA' AND version = 'Actual'",
        "filters": {"account_type": "SGA", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": -2.0, "yellow_threshold": 3.0, "red_threshold": 8.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "expense", "sga", "opex", "lubricants"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    # -----------------------------------------------------------------------
    # Sales KPIs (Aug 2026) — dp_lubricants_sales / LubricantsSalesStarView
    # Order volume, units, and fulfillment truth underneath the Finance dollar
    # view. net_amount reconciles exactly to net_revenue above (same basis) —
    # these KPIs deliberately do NOT re-derive a dollar figure Finance already
    # owns; they measure what only order-line data can (count, quantity, status).
    # -----------------------------------------------------------------------
    {
        "id": "sales_order_count",
        "client_id": CLIENT_ID,
        "name": "Sales Order Count",
        "domain": "Sales",
        "description": "Total number of distinct sales orders placed in the period.",
        "unit": "orders",
        "data_product_id": _SALES_DP_ID,
        "view_name": _SALES_VIEW,
        "business_process_ids": ["sales_operations", "order_processing"],
        "sql_query": f"SELECT COUNT(DISTINCT sales_order_id) AS value FROM {_SALES_BQ_PREFIX}",
        "filters": {},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _SALES_DIMS,
        "tags": ["sales", "orders", "volume", "lubricants"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO", "Sales Manager"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "units_sold",
        "client_id": CLIENT_ID,
        "name": "Units Sold",
        "domain": "Sales",
        "description": "Total quantity of product units sold across all sales order lines in the period.",
        "unit": "units",
        "data_product_id": _SALES_DP_ID,
        "view_name": _SALES_VIEW,
        "business_process_ids": ["sales_operations", "operations_order_to_cash_cycle_optimization"],
        "sql_query": f"SELECT SUM(quantity) AS value FROM {_SALES_BQ_PREFIX}",
        "filters": {},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _SALES_DIMS,
        "tags": ["sales", "volume", "units", "lubricants"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO", "Sales Manager"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "average_order_value",
        "client_id": CLIENT_ID,
        "name": "Average Order Value",
        "domain": "Sales",
        "description": "Net sales value per order (SUM net amount / distinct order count).",
        "unit": "$",
        "data_product_id": _SALES_DP_ID,
        "view_name": _SALES_VIEW,
        "business_process_ids": ["sales_operations"],
        "sql_query": f"SELECT SAFE_DIVIDE(SUM(net_amount), COUNT(DISTINCT sales_order_id)) AS value FROM {_SALES_BQ_PREFIX}",
        "filters": {},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _SALES_DIMS,
        "tags": ["sales", "order-value", "lubricants"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO", "Sales Manager"],
        "metadata": {"line": "middle", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "order_fulfillment_rate",
        "client_id": CLIENT_ID,
        "name": "Order Fulfillment Rate",
        "domain": "Sales",
        "description": "Percentage of sales order lines with delivery status Completed.",
        "unit": "%",
        "data_product_id": _SALES_DP_ID,
        "view_name": _SALES_VIEW,
        "business_process_ids": ["order_processing", "operations_order_to_cash_cycle_optimization"],
        "sql_query": f"SELECT SAFE_DIVIDE(COUNTIF(delivery_status = 'C'), COUNT(*)) * 100 AS value FROM {_SALES_BQ_PREFIX}",
        "filters": {"delivery_status": "C"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 2.0, "yellow_threshold": 0.0, "red_threshold": -2.0, "inverse_logic": False},
        ],
        "dimensions": _SALES_DIMS,
        "tags": ["sales", "fulfillment", "operations", "lubricants"],
        "owner_role": "COO",
        "stakeholder_roles": ["Sales Manager"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "order_cancellation_rate",
        "client_id": CLIENT_ID,
        "name": "Order Cancellation Rate",
        "domain": "Sales",
        "description": "Percentage of sales orders with lifecycle status Cancelled.",
        "unit": "%",
        "data_product_id": _SALES_DP_ID,
        "view_name": _SALES_VIEW,
        "business_process_ids": ["order_processing"],
        "sql_query": f"SELECT SAFE_DIVIDE(COUNTIF(lifecycle_status = 'X'), COUNT(*)) * 100 AS value FROM {_SALES_BQ_PREFIX}",
        "filters": {"lifecycle_status": "X"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": True},
        ],
        "dimensions": _SALES_DIMS,
        "tags": ["sales", "cancellations", "operations", "lubricants"],
        "owner_role": "COO",
        "stakeholder_roles": ["Sales Manager"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
]

# ── 11I-A: derive plan_variance + projected_breach + acceleration threshold rows ──
# Threshold-presence gating (Option A): a KPI runs a statistical pattern ONLY if it
# carries a threshold row for that comparison_type. These three KPIs already have
# plan_version_value="Budget" set but no plan_variance row — without one, the field
# is inert (11I-A never fires plan variance / budget-anchored projection for them).
#   plan_variance    — percent-of-budget tolerance bands, by KPI category.
#   projected_breach — budget-anchored (mirrors each KPI's own plan_variance red band).
#   acceleration     — self-calibrating against the KPI's own volatility; uniform
#     sensitivity row applies to every KPI (yellow = fire floor x, red = HIGH x).
_PLAN_VARIANCE_BANDS: Dict[str, Dict[str, Any]] = {
    "net_revenue":  {"green_threshold": 5.0, "yellow_threshold": 10.0, "red_threshold": 15.0, "inverse_logic": False},  # revenue
    "gross_profit": {"green_threshold": 3.0, "yellow_threshold": 8.0,  "red_threshold": 12.0, "inverse_logic": False},  # profitability
    "cogs":         {"green_threshold": 5.0, "yellow_threshold": 15.0, "red_threshold": 25.0, "inverse_logic": True},   # cost
}
_ACCEL_ROW: Dict[str, Any] = {
    "comparison_type": "acceleration",
    "green_threshold": None,
    "yellow_threshold": 2.0,   # fire floor: |acceleration| > 2x rolling velocity std
    "red_threshold": 3.0,      # HIGH severity at >= 3x (else MEDIUM)
    "inverse_logic": False,
}
for _kpi in KPIS:
    _ths = _kpi.setdefault("thresholds", [])
    _band = _PLAN_VARIANCE_BANDS.get(_kpi["id"])
    if _band is not None and _kpi.get("plan_version_value") and not any(
        t.get("comparison_type") == "plan_variance" for t in _ths
    ):
        _ths.append({"comparison_type": "plan_variance", **_band})
    _pv = next((t for t in _ths if t.get("comparison_type") == "plan_variance"), None)
    if _pv is not None and not any(t.get("comparison_type") == "projected_breach" for t in _ths):
        _ths.append({
            "comparison_type": "projected_breach",
            "green_threshold": _pv.get("green_threshold"),
            "yellow_threshold": _pv.get("yellow_threshold"),
            "red_threshold": _pv.get("red_threshold"),
            "inverse_logic": _pv.get("inverse_logic", False),
        })
    if not any(t.get("comparison_type") == "acceleration" for t in _ths):
        _ths.append(dict(_ACCEL_ROW))


# ---------------------------------------------------------------------------
# KPI relationships — cross-branch CAUSAL edges only (theory layer, Phase 15 D/E)
# ---------------------------------------------------------------------------
# Deliberately NOT the P&L arithmetic (net_revenue -> gross_profit -> operating_
# income -> ebitda, revenue channel splits, cogs component sums). That decomposition
# belongs to the Value Driver Tree spine, which theory_layer_design.md §7 derives
# from 12C objectives/driver weights — this table is reserved for cross-branch
# causal edges drawn only when active in a situation (the anti-hairball rule).
# The required `conflict_direction` field is conflict-detection semantics and has
# no meaning for an accounting identity, which is the schema telling you the same thing.
#
# PROVENANCE HONESTY: this is a hand-authored demo fixture, not accreted client
# knowledge. `confirmed` here means "a domain fact a Lubricants CFO would recognise
# on sight", not "this client's exec blessed it in a review" — the real meaning of
# that rung. Nothing here is `va_validated`; per the epistemic guardrail only VA
# running DiD/Granger on a specific edge can ever earn `intervention_tested`.
# Mixed provenance is intentional: it demonstrates SF correctly caveating template
# edges while citing confirmed ones.
KPI_RELATIONSHIPS: List[Dict[str, Any]] = [
    {
        "kpi_id": "net_revenue",
        "related_kpi_id": "gross_margin_pct",
        "client_id": CLIENT_ID,
        "relationship_type": "volume_margin",
        "conflict_direction": "diverging",
        "description": "Rising revenue with falling margin signals mix shift or pricing pressure",
        # Corrected 2026-08-20: originally left "unknown" for lack of a
        # recorded mechanism, but the direction here doesn't need one --
        # it's structural. Gross Margin % is CALCULATED FROM Net Revenue and
        # COGS ((Revenue - COGS) / Revenue): revenue movements (volume,
        # price, mix) move the ratio, the ratio cannot move revenue. Net
        # Revenue is therefore a legitimate root-cause candidate when
        # analysing Gross Margin %; Gross Margin % is never a legitimate
        # root-cause candidate when analysing Net Revenue -- a derived ratio
        # isn't an upstream cause of one of its own inputs. This is what
        # correctly removes "Addressing Gross Margin %" from Net Revenue's
        # own framing gate (previously shown, unfiltered, at hop 1) while
        # keeping "Addressing Net Revenue" available from Gross Margin %'s.
        #
        # Reclassified 2026-08-22 (docs/architecture/kpi_relationship_basis_design.md):
        # direction was right, epistemic category wasn't. This is an
        # accounting identity, not a believed empirical claim -- there is no
        # "confidence" in arithmetic. confidence/causal_rung dropped (neither
        # applies to a relationship that's true by construction); provenance
        # stays "confirmed" (the edge itself is real, just not evidence-based).
        "mechanism": "Gross Margin % is calculated from Net Revenue and COGS; revenue movements (volume, price, mix) move the ratio directly, not the reverse.",
        "provenance": "confirmed",
        "causal_direction": "kpi_causes_related",
    },
    {
        "kpi_id": "product_sales_revenue",
        "related_kpi_id": "cogs",
        "client_id": CLIENT_ID,
        "relationship_type": "cost_revenue",
        "conflict_direction": "diverging",
        "description": "Revenue growing slower than COGS indicates eroding unit economics",
        # Describes a co-movement (revenue vs. COGS growth rates), not a
        # recorded cause -- "unknown", same honesty as above.
        "causal_direction": "unknown",
    },
    {
        "kpi_id": "gross_margin_pct",
        "related_kpi_id": "cogs",
        "client_id": CLIENT_ID,
        "relationship_type": "custom",
        "conflict_direction": "diverging",
        "description": "COGS increases compress gross margin when revenue is flat",
        # Reclassified 2026-08-22 (docs/architecture/kpi_relationship_basis_design.md
        # §1): the previous mechanism text ("Base oil price volatility passes
        # through to COGS with a lag") described a real but ONE-HOP-REMOVED
        # claim -- an external commodity price affecting COGS's dollar value,
        # not what this edge actually connects. COGS is the other direct
        # algebraic input to Gross Margin % ((Revenue - COGS) / Revenue) --
        # this edge is an accounting identity, same category as the
        # net_revenue<->gross_margin_pct edge above. lag_periods dropped (an
        # identity sums same-period, by construction, no lag); confidence and
        # causal_rung dropped for the same reason as above. The genuinely
        # causal base-oil-price story that used to live here has no KPI to
        # attach to yet -- see design note §3, not solved by this edit.
        "mechanism": "Gross Margin % is calculated from Net Revenue and COGS; COGS movements directly move the ratio (Revenue held constant), not the reverse.",
        "provenance": "confirmed",
        # The formula is explicit: COGS (via the ratio) drives margin, not
        # the reverse. related_kpi_id (cogs) causes kpi_id (gross_margin_pct).
        "causal_direction": "related_causes_kpi",
    },
    {
        # The 11F anchor scenario, now expressible as an internal edge because
        # base_oil_cost is itself a registered KPI (account_category = 'Raw Materials').
        "kpi_id": "base_oil_cost",
        "related_kpi_id": "cogs",
        "client_id": CLIENT_ID,
        "relationship_type": "custom",
        # Both are costs: moving together upward is the adverse signal.
        "conflict_direction": "converging",
        "description": "Raw materials (base oil) cost is a direct component of total COGS",
        # Reclassified 2026-08-22 (docs/architecture/kpi_relationship_basis_design.md
        # §1): confirmed against base_oil_cost's own sql_query
        # (SUM(amount) WHERE account_category = 'Raw Materials') -- this is
        # an exact account_category sub-slice WITHIN cogs's own
        # account_type = 'COGS' bucket. COGS literally equals the sum of its
        # account_category components; this is an accounting identity, not
        # an inferred pass-through relationship. The old mechanism ("price
        # moves pass through with an inventory-buffered lag") described the
        # real, but genuinely external, causal story -- commodity spot price
        # affecting this ledger line's dollar value -- which this edge does
        # not encode (it connects two ledger lines, not a commodity price to
        # a ledger line). That external claim has no KPI to attach to yet;
        # see design note §3. lag_periods/confidence/causal_rung dropped --
        # an identity component sums same-period, by construction.
        "mechanism": "Raw Materials (base oil) is an account_category component of COGS; it sums into the COGS total directly, not via an inferred pass-through.",
        "provenance": "confirmed",
        # base_oil_cost (kpi_id) causes cogs (related_kpi_id) -- this is the
        # edge that lets base_oil_cost validly reach a gross_margin_pct
        # analysis at 2 hops (through the cogs edge above, both confirmed).
        "causal_direction": "kpi_causes_related",
    },
    {
        "kpi_id": "premium_mix_pct",
        "related_kpi_id": "gross_margin_pct",
        "client_id": CLIENT_ID,
        "relationship_type": "volume_margin",
        # Premium mix rising while margin falls means something else (input cost,
        # discounting) is overwhelming the mix benefit — that divergence is the signal.
        "conflict_direction": "diverging",
        "description": "Premium product mix shift moves blended gross margin without any pricing action",
        "mechanism": "Synthetic Blend and High Mileage formulations carry structurally higher gross margin than conventional grades, so a shift in mix moves blended margin on its own. Margin falling while premium mix rises indicates input-cost or discounting pressure masking the mix benefit.",
        "lag_periods": 0,
        "causal_rung": "correlational",
        "provenance": "template",
        "confidence": "moderate",
        # premium_mix_pct (kpi_id) causes gross_margin_pct (related_kpi_id).
        "causal_direction": "kpi_causes_related",
    },
    {
        "kpi_id": "distribution_cost",
        "related_kpi_id": "cogs",
        "client_id": CLIENT_ID,
        "relationship_type": "custom",
        "conflict_direction": "converging",
        "description": "Freight and packaging costs are a direct COGS component",
        # Reclassified 2026-08-22 (docs/architecture/kpi_relationship_basis_design.md
        # §1): confirmed against distribution_cost's own sql_query
        # (SUM(amount) WHERE account_category = 'Distribution') -- same shape
        # as base_oil_cost above, an exact account_category sub-slice within
        # cogs's own account_type = 'COGS' bucket. Accounting identity, not
        # an inferred pass-through claim. lag_periods dropped along with
        # confidence/causal_rung -- an identity component sums same-period.
        # provenance upgraded from "template" to "confirmed" -- an identity
        # doesn't need graduating through the evidence ladder at all; it's
        # true by construction from day one, same as the other three edges
        # reclassified alongside it.
        "mechanism": "Distribution (freight and packaging) is an account_category component of COGS; it sums into the COGS total directly, not via an inferred pass-through.",
        "provenance": "confirmed",
        # distribution_cost (kpi_id) causes cogs (related_kpi_id).
        "causal_direction": "kpi_causes_related",
    },
    # ------------------------------------------------------------------
    # Cross-data-product: Sales (dp_lubricants_sales) volume/price drivers
    # of Net Revenue (dp_lubricants_financials), added Aug 2026.
    #
    # NOT arithmetic in disguise, despite Sales SUM(net_amount) reconciling
    # to net_revenue exactly by construction (see
    # generate_lubricants_sales_data.py). These three are genuine
    # decomposition DRIVERS, the same epistemic shape as premium_mix_pct's
    # existing edge into gross_margin_pct: each is ONE factor (volume, order
    # frequency, price/mix), not the whole story, and each carries real
    # information -- knowing units_sold rose doesn't by itself tell you
    # net_revenue rose (price/mix could move the other way). order_fulfillment_rate
    # and order_cancellation_rate deliberately NOT mapped here -- their
    # relationship to revenue is real but more indirect, and needs its own
    # look at whether cancelled/unfulfilled orders are already excluded
    # from units_sold's own count before claiming a clean edge.
    # ------------------------------------------------------------------
    {
        "kpi_id": "units_sold",
        "related_kpi_id": "net_revenue",
        "client_id": CLIENT_ID,
        "relationship_type": "custom",
        "conflict_direction": "diverging",
        "description": "Units sold moving opposite to net revenue signals a price or mix problem",
        "mechanism": "Net Revenue is a function of units sold and price/mix; more units sold, price and mix held constant, drives higher revenue. Sales order line data carries unit volume directly, decomposing a revenue move into its volume component.",
        "lag_periods": 0,
        "causal_rung": "correlational",
        "provenance": "confirmed",
        "confidence": "high",
        "causal_direction": "kpi_causes_related",
    },
    {
        "kpi_id": "sales_order_count",
        "related_kpi_id": "net_revenue",
        "client_id": CLIENT_ID,
        "relationship_type": "custom",
        "conflict_direction": "diverging",
        "description": "Order count moving opposite to net revenue signals an order-size or mix problem",
        "mechanism": "More completed orders, average order value held constant, drives higher revenue -- the transaction-frequency component, distinct from order size.",
        "lag_periods": 0,
        "causal_rung": "correlational",
        "provenance": "confirmed",
        "confidence": "high",
        "causal_direction": "kpi_causes_related",
    },
    {
        "kpi_id": "average_order_value",
        "related_kpi_id": "net_revenue",
        "client_id": CLIENT_ID,
        "relationship_type": "custom",
        "conflict_direction": "diverging",
        "description": "Average order value moving opposite to net revenue signals an order-volume problem",
        "mechanism": "Higher average order value, order count held constant, drives higher revenue -- the price/mix component, distinct from order volume.",
        "lag_periods": 0,
        "causal_rung": "correlational",
        "provenance": "confirmed",
        "confidence": "high",
        "causal_direction": "kpi_causes_related",
    },
]


# KPI arithmetic decomposition (Phase 17 T2, see
# src/registry/models/kpi_decomposition.py's module docstring for the full
# linear/ratio design). Only the two edges that reconcile EXACTLY against real
# BigQuery values are seeded -- deliberately, not the full account_category
# tree implied by cogs' own sql_query.
#
# gross_profit = net_revenue - cogs: true by construction (gross_profit's
# sql_query literally sums the same Revenue+COGS rows net_revenue and cogs
# each sum separately). cogs's edge carries sign=-1 because the `cogs` KPI's
# OWN reported value is already a positive cost magnitude (its sql_query
# negates the raw signed amount) -- net_revenue MINUS that positive magnitude
# is gross_profit, not a plain addition of both KPI values.
#
# gross_margin_pct = ratio(gross_profit, net_revenue), matching its own
# sql_query's 100 * SUM(Revenue+COGS) / SUM(Revenue) exactly.
#
# NOT seeded: cogs -> base_oil_cost + distribution_cost. base_oil_cost
# (Raw Materials) is only 41.5% of COGS (122.0M of 293.8M, per that KPI's own
# comment) and distribution_cost covers another slice -- neither this pair
# nor any other combination of currently-registered KPIs sums to the full
# COGS total (Packaging, Labor and other account_categories exist in the
# data with no KPI of their own). Seeding that edge would fail
# check_tree_reconciles against real values -- exactly the defect the
# reconciliation check exists to catch, so it is not seeded rather than
# seeded-and-silenced. Filed as a fast-follow: either register the
# remaining COGS account_categories as their own KPIs, or don't decompose
# COGS further until that's done.
KPI_DECOMPOSITIONS: List[Dict[str, Any]] = [
    {
        "parent_kpi_id": "gross_profit",
        "child_kpi_id": "net_revenue",
        "client_id": CLIENT_ID,
        "operation": "linear",
        "sign": 1,
    },
    {
        "parent_kpi_id": "gross_profit",
        "child_kpi_id": "cogs",
        "client_id": CLIENT_ID,
        "operation": "linear",
        "sign": -1,
    },
    {
        "parent_kpi_id": "gross_margin_pct",
        "child_kpi_id": "gross_profit",
        "client_id": CLIENT_ID,
        "operation": "ratio",
        # sign is ignored for operation='ratio' (see the model docstring) but
        # still set explicitly -- PostgREST's bulk insert derives its column
        # list from the request's first row, so a later row omitting a key
        # present elsewhere in the same batch sends NULL instead of letting
        # the column's DB DEFAULT apply.
        "sign": 1,
        "weight_kpi_id": "net_revenue",
    },
]


# External-world ports (Phase 17 T4, docs/architecture/theory_layer_design.md §2.3).
#
# This is the exact story the 2026-08-22 kpi_relationship_basis_design.md
# reclassification (see the base_oil_cost -> cogs edge above) explicitly
# removed and flagged as homeless: "The old mechanism ('price moves pass
# through with an inventory-buffered lag') described the real, but
# genuinely external, causal story... which this edge does not encode
# ... That external claim has no KPI to attach to yet." A Port is that home
# -- base oil SPOT PRICE is not itself a registered KPI (it's an external
# field), so it cannot be a kpi_relationships edge; linked_kpi_id is the
# INTERNAL side (base_oil_cost) the external move enters at.
#
# PROVENANCE HONESTY (same caveat as KPI_RELATIONSHIPS/ASSUMPTIONS above):
# current_signal below is a qualitative restatement of the 11F anchor
# scenario itself (Base Oil rising while COGS/base_oil_cost declines -- the
# transmission that SHOULD have happened and hasn't), not a live-queried
# number. source='manual' says so explicitly; a live MA re-query
# (source='ma_query') is a follow-up, not built this stage.
PORTS: List[Dict[str, Any]] = [
    {
        "client_id": CLIENT_ID,
        "name": "Base Oil Price",
        "port_type": "input_costs",
        "linked_kpi_id": "base_oil_cost",
        "lag_periods": 1,
        "buffer_description": (
            "One-month inventory buffer between spot base-oil purchases and COGS "
            "recognition; hedges and contract repricing lag further slow transmission "
            "-- carried over verbatim from the mechanism text the kpi_relationships "
            "edge above used to hold before its 2026-08-22 reclassification."
        ),
        "current_signal": (
            "Base oil spot price rising while base_oil_cost/COGS is declining -- an "
            "external move that should have transmitted and hasn't (theory_layer_design.md "
            "§2.3's own anchor scenario). The interesting object is whatever is absorbing "
            "it in the chain (inventory layers, hedges, mix shift) -- not yet identified."
        ),
        "source": "manual",
    },
]


# Theory-layer assumption register (see docs/architecture/theory_layer_design.md).
#
# Seeded rows carry an EXPLICIT stable `id` so onboarding upserts on the primary key
# instead of delete-first. This table also accumulates rows written at runtime by SF
# HITL approval (source='sf_hitl_approval'), and that accreted knowledge is the whole
# point of the theory layer — a delete-by-client pass here would erase it.
#
# PROVENANCE HONESTY: same caveat as KPI_RELATIONSHIPS above. `confirmed` means "a
# Lubricants CFO would recognise this on sight", not "this client's exec blessed it".
ASSUMPTIONS: List[Dict[str, Any]] = [
    {
        # Hard constraint: SF must not propose mid-quarter list-price increases on
        # anchor accounts. This is the row that makes the causal-grounding A/B visible
        # — without it SF cheerfully recommends exactly the move the contracts forbid.
        "id": "8dd4e22c-f23f-48dc-b76e-f4eb89367a3e",
        "client_id": CLIENT_ID,
        "scope": "gross_margin_pct",
        "record_type": "constraint",
        "text": (
            "Cannot raise list prices on Lubricants anchor accounts mid-quarter "
            "(contractual price-lock clause)"
        ),
        "status": "active",
        "source": "manual",
        "provenance": "confirmed",
        "confidence": "high",
    },
]


PRINCIPALS: List[Dict[str, Any]] = [
    {
        "id": "cfo_001",
        "client_id": CLIENT_ID,
        "name": "Sarah Chen",
        "first_name": "Sarah",
        "last_name": "Chen",
        "title": "Chief Financial Officer",
        "role": "CFO",
        "workflow_role": "decision_maker",
        "department": "Finance",
        "source": "HR Database",
        "description": (
            "CFO responsible for financial performance of the Lubricants Business. "
            "Key focus areas: revenue growth across product lines and channels, "
            "gross margin protection against base oil price volatility, "
            "and SG&A cost discipline."
        ),
        "responsibilities": [
            "maximize EBIT",
            "manage revenue across product lines and channels",
            "control COGS and SG&A expenses",
            "protect gross margin against base oil volatility",
            "oversee divisional P&L reporting",
        ],
        # Corrected: use finance_revenue_growth_analysis (matches canonical BP + KPI BP IDs)
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "finance_cash_flow_management",
            "finance_budget_vs_actuals",
            "financial_reporting",
            "pricing_strategy",
        ],
        "default_filters": {
            "Profit Center Name": ["Total"],
            "Customer Segment": ["Total"],
            "Fiscal Year": ["2024", "2025", "2026"],
        },
        "typical_timeframes": ["Monthly", "Quarterly"],
        "principal_groups": ["Executive Leadership", "Finance Committee"],
        "persona_profile": {
            "decision_style": "analytical",
            "risk_tolerance": "low",
            "communication_style": "concise",
            "values": ["accuracy", "compliance", "predictability"],
        },
        "preferences": {"channel": "Slack", "ui": "summary_dashboard"},
        "permissions": ["finance_read", "finance_write"],
        "metadata": {
            "kpi_line_preference": "bottom_line_first",
            "kpi_altitude_preference": "strategic_first",
        },
    },
    {
        "id": "ceo_001",
        "client_id": CLIENT_ID,
        "name": "David Torres",
        "first_name": "David",
        "last_name": "Torres",
        "title": "Chief Executive Officer",
        "role": "CEO",
        "workflow_role": "decision_maker",
        "department": "Executive",
        "source": "HR Database",
        "description": "CEO driving Lubricants Business strategy and market growth.",
        "responsibilities": [
            "set strategic direction for lubricants portfolio",
            "oversee company performance across all divisions",
            "drive market share growth",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "strategy_market_share_analysis",
            "strategy_ebitda_growth_tracking",
        ],
        "default_filters": {"Fiscal Year": ["2024", "2025", "2026"]},
        "typical_timeframes": ["Quarterly", "Annually"],
        "persona_profile": {"decision_style": "strategic", "risk_tolerance": "moderate", "communication_style": "executive"},
        "metadata": {"kpi_line_preference": "top_line_first", "kpi_altitude_preference": "strategic_first"},
    },
    {
        "id": "coo_001",
        "client_id": CLIENT_ID,
        "name": "Rachel Kim",
        "first_name": "Rachel",
        "last_name": "Kim",
        "title": "Chief Operating Officer",
        "role": "COO",
        "workflow_role": "decision_maker",
        "department": "Operations",
        "source": "HR Database",
        "description": "COO overseeing production, supply chain, and operational efficiency.",
        "responsibilities": [
            "manage manufacturing and supply chain operations",
            "drive COGS reduction",
            "oversee distribution network",
        ],
        "business_process_ids": [
            "finance_expense_management",
            "finance_profitability_analysis",
            "operations_inventory_turnover_analysis",
            "supply_chain_logistics_efficiency",
        ],
        "default_filters": {"Fiscal Year": ["2024", "2025", "2026"]},
        "typical_timeframes": ["Monthly", "Quarterly"],
        "persona_profile": {"decision_style": "operational", "risk_tolerance": "low", "communication_style": "detailed"},
        "metadata": {"kpi_line_preference": "bottom_line_first", "kpi_altitude_preference": "operational_first"},
    },
    {
        "id": "finance_001",
        "client_id": CLIENT_ID,
        "name": "Marcus Webb",
        "first_name": "Marcus",
        "last_name": "Webb",
        "title": "Finance Manager",
        "role": "Finance Manager",
        "workflow_role": "framer",
        "department": "Finance",
        "source": "HR Database",
        "description": "Finance Manager supporting P&L analysis and budget management.",
        "responsibilities": [
            "financial reporting and variance analysis",
            "budget management",
            "cost control",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "finance_budget_vs_actuals",
            "finance_cash_flow_management",
            "financial_reporting",
        ],
        "default_filters": {"Fiscal Year": ["2024", "2025", "2026"]},
        "typical_timeframes": ["Monthly"],
        "persona_profile": {"decision_style": "analytical", "risk_tolerance": "low", "communication_style": "detailed"},
        "metadata": {"kpi_line_preference": "balanced", "kpi_altitude_preference": "operational_first", "settings_admin": "true"},
    },
]

# Business processes: Finance + Strategy + Pricing + Operations + Sales (the latter
# two added Aug 2026 for dp_lubricants_sales' order_processing / sales_operations /
# operations_order_to_cash_cycle_optimization KPI references)
BUSINESS_PROCESS_IDS = [
    bp["id"] for bp in FINANCE_BUSINESS_PROCESSES + STRATEGY_BUSINESS_PROCESSES + PRICING_BUSINESS_PROCESSES
    + OPERATIONS_BUSINESS_PROCESSES + SALES_BUSINESS_PROCESSES
]

EXTRA_BUSINESS_PROCESSES: List[Dict[str, Any]] = []

# Dimension-label glossary terms — added 2026-08-24 so the Variance Breakdown
# exhibit (DivergingBarChart.tsx / IsIsNotExhibit) can show a governed
# business label instead of the raw dimension_semantics field name from
# lubricants_star_schema.yaml (e.g. "customer_region" -> "Customer Region").
# Resolved via A9_Data_Governance_Agent.resolve_dimension_label() ->
# BusinessGlossaryProvider.get_by_technical_name(), which searches
# technical_mappings values — the reverse direction from the core terms
# above (which map a business term FORWARD to a technical name).
#
# One entry per entry in dimension_semantics (src/registry_references/
# data_product_registry/data_products/lubricants_star_schema.yaml). If that
# contract's dimension list changes, this list needs a matching update — it
# is not derived automatically, the same manual-sync discipline as every
# other registry seed file per root CLAUDE.md.
EXTRA_GLOSSARY_TERMS: List[Dict[str, Any]] = [
    {
        "id": "dim_product_name", "term": "Product Name",
        "definition": "The specific product SKU or item name.",
        "domain": "Product", "tags": ["dimension", "product"],
        "technical_mappings": {"bigquery": "product_name"},
    },
    {
        "id": "dim_product_line", "term": "Product Line",
        "definition": "The product family or line a SKU belongs to (e.g. Engine Oils, Compressor Oil).",
        "domain": "Product", "tags": ["dimension", "product"],
        "technical_mappings": {"bigquery": "product_line"},
    },
    {
        "id": "dim_product_category", "term": "Product Category",
        "definition": "The broad category a product line rolls up to.",
        "domain": "Product", "tags": ["dimension", "product"],
        "technical_mappings": {"bigquery": "product_category"},
    },
    {
        "id": "dim_customer_name", "term": "Customer Name",
        "definition": "The specific named customer account.",
        "domain": "Customer", "tags": ["dimension", "customer"],
        "technical_mappings": {"bigquery": "customer_name"},
    },
    {
        "id": "dim_customer_segment", "term": "Customer Segment",
        "definition": "The customer's market segment (e.g. Retail Partners, Commercial & Industrial).",
        "domain": "Customer", "tags": ["dimension", "customer"],
        "technical_mappings": {"bigquery": "customer_segment"},
    },
    {
        "id": "dim_customer_region", "term": "Customer Region",
        "definition": "The geographic region the customer is based in.",
        "domain": "Customer", "tags": ["dimension", "customer"],
        "technical_mappings": {"bigquery": "customer_region"},
    },
    {
        "id": "dim_profit_center_name", "term": "Profit Center",
        "definition": "The internal profit center the transaction is booked against.",
        "domain": "Organization", "tags": ["dimension", "organization"],
        "technical_mappings": {"bigquery": "profit_center_name"},
    },
    {
        "id": "dim_business_unit", "term": "Business Unit",
        "definition": "The business unit the transaction belongs to.",
        "domain": "Organization", "tags": ["dimension", "organization"],
        "technical_mappings": {"bigquery": "business_unit"},
    },
    {
        "id": "dim_channel_name", "term": "Channel Name",
        "definition": "The specific named sales or distribution channel.",
        "domain": "Channel", "tags": ["dimension", "channel"],
        "technical_mappings": {"bigquery": "channel_name"},
    },
    {
        "id": "dim_channel_type", "term": "Channel Type",
        "definition": "The category of sales or distribution channel (e.g. Direct, Distributor).",
        "domain": "Channel", "tags": ["dimension", "channel"],
        "technical_mappings": {"bigquery": "channel_type"},
    },
    {
        "id": "dim_account_name", "term": "Account Name",
        "definition": "The specific general ledger account name.",
        "domain": "Finance", "tags": ["dimension", "account"],
        "technical_mappings": {"bigquery": "account_name"},
    },
    {
        "id": "dim_account_type", "term": "Account Type",
        "definition": "The general ledger account type (e.g. Revenue, Expense, Cost of Sales).",
        "domain": "Finance", "tags": ["dimension", "account"],
        "technical_mappings": {"bigquery": "account_type"},
    },
    {
        "id": "dim_account_category", "term": "Account Category",
        "definition": "The category a general ledger account rolls up to within its account type.",
        "domain": "Finance", "tags": ["dimension", "account"],
        "technical_mappings": {"bigquery": "account_category"},
    },
    {
        "id": "dim_account_group", "term": "Account Group",
        "definition": "The broadest general ledger account grouping.",
        "domain": "Finance", "tags": ["dimension", "account"],
        "technical_mappings": {"bigquery": "account_group"},
    },
]

# ---------------------------------------------------------------------------
# Phase 11A: KPI Accountability assignments
# ---------------------------------------------------------------------------
# Ownership logic:
#   cfo_001  — accountable for all enterprise P&L KPIs
#   ceo_001  — accountable for strategic KPIs (ebitda, premium_mix_pct);
#              responsible (not accountable) for net_revenue to avoid
#              violating the singleton-accountable-per-scope constraint
#   coo_001  — accountable for operational cost/delivery KPIs
#   finance_001 — responsible for detailed revenue tracking KPIs
#                 and gross_margin_pct
#
# IDs follow the pattern acc_lub_<principal>_<kpi>.

ACCOUNTABILITY: List[Dict[str, Any]] = [
    # ------------------------------------------------------------------
    # CFO (Sarah Chen) — accountable for enterprise P&L KPIs
    # ------------------------------------------------------------------
    {
        "id": "acc_lub_cfo_net_revenue",
        "client_id": CLIENT_ID,
        "kpi_id": "net_revenue",
        "principal_id": "cfo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "CFO owns top-line revenue performance enterprise-wide.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_cfo_gross_profit",
        "client_id": CLIENT_ID,
        "kpi_id": "gross_profit",
        "principal_id": "cfo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "CFO owns gross profit — primary margin control point.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_cfo_gross_margin_pct",
        "client_id": CLIENT_ID,
        "kpi_id": "gross_margin_pct",
        "principal_id": "cfo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "CFO accountable for overall gross margin percentage.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_cfo_operating_income",
        "client_id": CLIENT_ID,
        "kpi_id": "operating_income",
        "principal_id": "cfo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "CFO accountable for EBIT / operating income.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_cfo_ebitda",
        "client_id": CLIENT_ID,
        "kpi_id": "ebitda",
        "principal_id": "cfo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "CFO accountable for enterprise EBITDA.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_cfo_sga_expense",
        "client_id": CLIENT_ID,
        "kpi_id": "sga_expense",
        "principal_id": "cfo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "CFO owns SG&A cost discipline.",
        "created_by": "seed",
    },
    # ------------------------------------------------------------------
    # CEO (David Torres) — accountable for strategic KPIs;
    # responsible for net_revenue (CFO is accountable)
    # ------------------------------------------------------------------
    {
        "id": "acc_lub_ceo_net_revenue",
        "client_id": CLIENT_ID,
        "kpi_id": "net_revenue",
        "principal_id": "ceo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "responsible",
        "notes": "CEO is responsible for net revenue growth direction; CFO is accountable.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_ceo_ebitda",
        "client_id": CLIENT_ID,
        "kpi_id": "ebitda",
        "principal_id": "ceo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "responsible",
        "notes": "CEO responsible for EBITDA as a strategic outcome; CFO is accountable.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_ceo_premium_mix_pct",
        "client_id": CLIENT_ID,
        "kpi_id": "premium_mix_pct",
        "principal_id": "ceo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "CEO sets product portfolio strategy; accountable for premium mix target.",
        "created_by": "seed",
    },
    # ------------------------------------------------------------------
    # COO (Rachel Kim) — accountable for operational cost/delivery KPIs
    # ------------------------------------------------------------------
    {
        "id": "acc_lub_coo_cogs",
        "client_id": CLIENT_ID,
        "kpi_id": "cogs",
        "principal_id": "coo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "COO owns direct manufacturing and supply chain costs.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_coo_base_oil_cost",
        "client_id": CLIENT_ID,
        "kpi_id": "base_oil_cost",
        "principal_id": "coo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "COO accountable for raw material sourcing and base oil cost.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_coo_distribution_cost",
        "client_id": CLIENT_ID,
        "kpi_id": "distribution_cost",
        "principal_id": "coo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "COO owns logistics network efficiency.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_coo_avg_transaction_value",
        "client_id": CLIENT_ID,
        "kpi_id": "avg_transaction_value",
        "principal_id": "coo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "COO accountable for operational levers driving average transaction value.",
        "created_by": "seed",
    },
    # ------------------------------------------------------------------
    # COO (Rachel Kim) — accountable for Sales KPIs (dp_lubricants_sales,
    # Aug 2026), matching the owner_role="COO" already set on each of these
    # 5 KPI records — order volume/fulfillment are operational levers, the
    # same domain as the cost/delivery KPIs above.
    # ------------------------------------------------------------------
    {
        "id": "acc_lub_coo_sales_order_count",
        "client_id": CLIENT_ID,
        "kpi_id": "sales_order_count",
        "principal_id": "coo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "COO accountable for order volume.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_coo_units_sold",
        "client_id": CLIENT_ID,
        "kpi_id": "units_sold",
        "principal_id": "coo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "COO accountable for units shipped.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_coo_average_order_value",
        "client_id": CLIENT_ID,
        "kpi_id": "average_order_value",
        "principal_id": "coo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "COO accountable for order economics.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_coo_order_fulfillment_rate",
        "client_id": CLIENT_ID,
        "kpi_id": "order_fulfillment_rate",
        "principal_id": "coo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "COO accountable for fulfillment/delivery performance.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_coo_order_cancellation_rate",
        "client_id": CLIENT_ID,
        "kpi_id": "order_cancellation_rate",
        "principal_id": "coo_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "accountable",
        "notes": "COO accountable for order-processing quality.",
        "created_by": "seed",
    },
    # ------------------------------------------------------------------
    # Finance Manager (Marcus Webb) — responsible for detailed revenue
    # tracking KPIs and gross_margin_pct
    # ------------------------------------------------------------------
    {
        "id": "acc_lub_fin_product_sales_revenue",
        "client_id": CLIENT_ID,
        "kpi_id": "product_sales_revenue",
        "principal_id": "finance_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "responsible",
        "notes": "Finance Manager tracks and reports product sales revenue.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_fin_service_revenue",
        "client_id": CLIENT_ID,
        "kpi_id": "service_revenue",
        "principal_id": "finance_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "responsible",
        "notes": "Finance Manager tracks service revenue lines.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_fin_b2b_revenue",
        "client_id": CLIENT_ID,
        "kpi_id": "b2b_revenue",
        "principal_id": "finance_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "responsible",
        "notes": "Finance Manager responsible for B2B channel revenue reporting.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_fin_ecommerce_revenue",
        "client_id": CLIENT_ID,
        "kpi_id": "ecommerce_revenue",
        "principal_id": "finance_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "responsible",
        "notes": "Finance Manager tracks e-commerce channel performance.",
        "created_by": "seed",
    },
    {
        "id": "acc_lub_fin_gross_margin_pct",
        "client_id": CLIENT_ID,
        "kpi_id": "gross_margin_pct",
        "principal_id": "finance_001",
        "scope_dimension": None,
        "scope_value": None,
        "role": "responsible",
        "notes": "Finance Manager responsible for gross margin variance analysis.",
        "created_by": "seed",
    },
]
