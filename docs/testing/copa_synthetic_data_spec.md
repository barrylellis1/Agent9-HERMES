# CO-PA Synthetic Test Data Specification
## Meridian Flow Systems — BigQuery Dataset

**Created:** 2026-06-09  
**Last updated:** 2026-06-18  
**Purpose:** Synthetic test data for Phases 11K–11N (Data Product Observability, EDA Dimensional Profiling, Change Detection, Background DA, Event-Driven PIB) + Data Product Onboarding (8-step workflow + Phase 12A KPI Template Generator)  
**Client ID:** `meridian`  
**Company:** Meridian Flow Systems — mid-market industrial pump, valve, and flow control equipment manufacturer. $165M annual revenue. Headquartered in Columbus, Ohio. Serves water/wastewater utilities, oil & gas, chemical process, food & beverage, mining, and general industrial customers across North America. SAP S/4HANA with CO-PA extraction to BigQuery.  
**Why pumps for CO-PA:** The order type dimension (catalog standard / engineered-to-order / aftermarket parts / service contract) creates a 30pp CM I spread within the same factory — the richest single profitability dimension in manufacturing CO-PA. This is the question every pump company CFO has asked and never gotten a clean answer to.  
**Fiscal years covered:** FY2024, FY2025, FY2026 (all 12 periods) — full FY2026 ensures demo stability throughout the year without data refreshes. P7–P12 2026 represent synthetic projected actuals with a partial H2 recovery arc.

---

## 1. BigQuery Location

| Field | Value |
|---|---|
| GCP Project | `agent9-465818` (same as lubricants) |
| Dataset | `meridian_copa` |
| Primary table | `copa_line_items` |
| Scenario tables | `copa_baseline`, `copa_drifted` (Scenario C) |
| Cadence views | `copa_fresh`, `copa_nightly`, `copa_stale` (Scenario A) |

---

## 2. Full Table Schema — `copa_line_items`

Column descriptions are written into the BQ schema at table creation time. They are surfaced by `DPA._profile_table_bigquery()` during onboarding Step 1 and by the KPI Assistant during KPI suggestion. Meaningful descriptions allow the LLM to reason about the purpose of each column without domain knowledge hardcoded in the agent.

```python
# Seed script uses BigQuery SchemaField with description= parameter
# Table created via bigquery.Client().create_table(table) with schema list

COPA_SCHEMA = [
    # --- Period dimensions ---
    SchemaField("fiscal_year",   "INT64",   "REQUIRED",
        description="SAP fiscal year (GJAHR). Calendar year — FY2024 = Jan 2024 to Dec 2024. "
                    "Use with fiscal_period for YoY comparisons. TimeDimension: fiscal_year_period."),
    SchemaField("fiscal_period", "INT64",   "REQUIRED",
        description="SAP fiscal period (MONAT). Month number within fiscal year (1=January, 12=December). "
                    "TimeDimension: fiscal_year_period — pair with fiscal_year."),
    SchemaField("posting_date",  "DATE",    "REQUIRED",
        description="Last calendar date of the fiscal period. Derived field for display and date-based filtering. "
                    "TimeDimension: date — secondary to fiscal_year_period."),
    SchemaField("updated_at",    "TIMESTAMP","REQUIRED",
        description="ETL load timestamp set by BigQuery Data Transfer Service at extraction time. "
                    "Use to assess data freshness and cadence. NOT an analytical dimension."),

    # --- Customer axis ---
    SchemaField("customer_id",   "STRING",  "REQUIRED",
        description="SAP customer number (KUNNR). High-cardinality identifier — exclude from GROUP BY "
                    "dimensional analysis. Use customer_group for segment-level profitability."),
    SchemaField("customer_group","STRING",  "REQUIRED",
        description="SAP customer group (KDGRP). Strategic segmentation by channel and scale: "
                    "TIER1_UTILITIES (large municipal / utility accounts, 36% CM II), "
                    "TIER2_INDUSTRIAL (mid-size industrial plants, 31% CM II), "
                    "REGIONAL_CONTRACTORS (EPC and system integrators, 27% CM II), "
                    "DISTRIBUTOR_ACCOUNTS (stocking distributors, 22% CM II), "
                    "EXPORT_OEM (export and OEM, 28% CM II). "
                    "Primary segment profitability driver — analyse first. 14pp CM II spread between best and worst group."),
    SchemaField("industry",      "STRING",  "REQUIRED",
        description="SAP industry sector (BRSCH). End-market industry the customer operates in: "
                    "WATER_WASTEWATER (municipal utilities, treatment plants), OIL_GAS (upstream production, pipeline), "
                    "CHEMICAL_PROCESS (refineries, chemical plants), FOOD_BEVERAGE (food processing, sanitary duty), "
                    "MINING (dewatering, slurry), GENERAL_INDUSTRIAL (manufacturing, HVAC, cooling), "
                    "POWER_GENERATION (utility, power plants). Key dimension for pricing power analysis."),
    SchemaField("sales_district","STRING",  "REQUIRED",
        description="SAP sales district (BZIRK). Geographic sales territory: NORTHEAST_US, MIDWEST_US, "
                    "SOUTHEAST_US, SOUTHWEST_US, WEST_US, CANADA, MEXICO, EXPORT_ROW. "
                    "Drives freight cost variance in CM II."),
    SchemaField("payment_terms", "STRING",  "REQUIRED",
        description="SAP payment terms key (ZTERM). Customer payment schedule: NET_30, NET_45, NET_60, "
                    "NET_90, IMMEDIATE. Affects cash conversion cycle and discount eligibility."),

    # --- Product axis ---
    SchemaField("order_type",    "STRING",  "REQUIRED",
        description="SAP order type / CO-PA characteristic. Business model classification: "
                    "CATALOG_STANDARD (off-the-shelf products from published price list, ~32% CM I), "
                    "ENGINEERED_TO_ORDER (custom-engineered specials to customer spec, ~46% CM I), "
                    "AFTERMARKET_PARTS (replacement and spare parts for installed base, ~55% CM I), "
                    "SERVICE_CONTRACT (annual maintenance agreements, recurring, ~40% CM I). "
                    "PRIMARY profitability driver — 23pp CM I spread between best and worst order type. KEY MEASURE context dimension."),
    SchemaField("material_group","STRING",  "REQUIRED",
        description="SAP material group (MATKL). Component classification for procurement and costing: "
                    "12 groups covering castings, rotating elements, seals, bearings, motors, actuators, "
                    "valve bodies, controls, fabrications, elastomers, fasteners, and sub-assemblies."),
    SchemaField("product_hierarchy_l1","STRING","REQUIRED",
        description="SAP product hierarchy level 1 (PRODH1). Top-level product division: "
                    "CENTRIFUGAL_PUMPS, POSITIVE_DISPLACEMENT, CONTROL_VALVES, "
                    "METERING_SYSTEMS, AFTERMARKET_SERVICE. "
                    "Primary product-mix driver of gross margin. Use with order_type for full profitability model."),
    SchemaField("product_hierarchy_l2","STRING","REQUIRED",
        description="SAP product hierarchy level 2 (PRODH2). Sub-category within product division. "
                    "17 sub-categories. Use for detailed product-mix analysis within a division."),

    # --- Org / channel axis ---
    SchemaField("sales_org",     "STRING",  "REQUIRED",
        description="SAP sales organisation (VKORG). Two orgs: SORG_NA (North America, ~95% revenue), "
                    "SORG_INTL (International, ~5%). Low analytical variance — use for filtering not grouping."),
    SchemaField("distribution_channel","STRING","REQUIRED",
        description="SAP distribution channel (VTWEG). Route to market: DIRECT_SALES (project/direct to end user, "
                    "highest CM II), DISTRIBUTOR_STOCK (stocking distributor for catalog items), "
                    "ENGINEERED_REP (manufacturer's representative for complex project work), "
                    "ONLINE_CATALOG (e-commerce for spare parts and small catalog items). "
                    "Significant CM II variance across channels — direct is highest margin."),
    SchemaField("sales_office",  "STRING",  "REQUIRED",
        description="SAP sales office (VKBUR). Regional office responsible for the sale: "
                    "OFFICE_CHICAGO, OFFICE_HOUSTON, OFFICE_ATLANTA, OFFICE_NYC, OFFICE_LA, OFFICE_TORONTO."),
    SchemaField("plant",         "STRING",  "REQUIRED",
        description="SAP plant (WERKS). Manufacturing or distribution facility fulfilling the order: "
                    "PLANT_OHIO, PLANT_TEXAS, PLANT_GEORGIA, PLANT_ILLINOIS, PLANT_ONTARIO. "
                    "Drives standard COGS variance through production efficiency."),
    SchemaField("profit_center", "STRING",  "REQUIRED",
        description="SAP profit centre (PRCTR). Responsibility unit for P&L accountability. "
                    "8 profit centres aligned to product divisions: centrifugal pumps, positive displacement, "
                    "control valves, metering, aftermarket, export, Canada, and shared services."),
    SchemaField("division",      "STRING",  "REQUIRED",
        description="SAP division (SPART). Product-based org unit: DIV_PUMPS, DIV_VALVES, "
                    "DIV_METERING, DIV_AFTERMARKET. Overlaps with product_hierarchy_l1 — "
                    "use product_hierarchy_l1 for finer-grained analysis."),

    # --- Customer classification axis ---
    SchemaField("customer_classification","STRING","REQUIRED",
        description="Internal strategic classification: CLASS_A (key accounts, ~55% revenue), "
                    "CLASS_B (standard, ~40%), CLASS_C (tail accounts, ~5%). "
                    "Coarse segmentation — customer_group provides more analytical resolution."),
    SchemaField("credit_tier",   "STRING",  "REQUIRED",
        description="Internal credit risk tier assigned by Finance: TIER_PLATINUM, TIER_GOLD, "
                    "TIER_STANDARD, TIER_WATCH. Low CM variance by tier — use for risk monitoring "
                    "not profitability analysis."),

    # --- Value fields (CO-PA stepped contribution margin) ---
    SchemaField("gross_revenue", "NUMERIC", "REQUIRED",
        description="Gross billing value before any deductions (list price × volume). "
                    "SAP equivalent: VVRKME value field. Always positive."),
    SchemaField("sales_deductions","NUMERIC","REQUIRED",
        description="Total sales deductions: volume discounts, customer rebates, early payment discounts. "
                    "Always negative. Typical range: −15% to −25% of gross_revenue."),
    SchemaField("net_revenue",   "NUMERIC", "REQUIRED",
        description="Net revenue after all deductions. net_revenue = gross_revenue + sales_deductions. "
                    "Primary KPI numerator for margin calculations. KEY MEASURE."),
    SchemaField("standard_cogs", "NUMERIC", "REQUIRED",
        description="Standard cost of goods sold at SAP standard costing rate. Always negative. "
                    "Typical range: −42% to −68% of net_revenue depending on order_type and product_hierarchy_l1. "
                    "AFTERMARKET_PARTS lowest COGS (45%); CATALOG_STANDARD highest (68%). KEY MEASURE."),
    SchemaField("freight_cost",  "NUMERIC", "REQUIRED",
        description="Outbound freight and logistics costs allocated to the transaction. Always negative. "
                    "Typical range: −3% to −6% of net_revenue. Highest in NORTHEAST_US and WEST_US districts. "
                    "KEY MEASURE for CM II analysis."),
    SchemaField("commission",    "NUMERIC", "REQUIRED",
        description="Sales commission allocated to the transaction. Always negative. "
                    "Typical range: −1% to −3% of net_revenue. Higher for DISTRIBUTOR channel."),
    SchemaField("cm_i",          "NUMERIC", "REQUIRED",
        description="Contribution Margin I (Gross Margin). cm_i = net_revenue + standard_cogs. "
                    "Company FY2025 average ~37% of net_revenue. "
                    "Ranges 32% (CATALOG_STANDARD) to 55% (AFTERMARKET_PARTS) by order_type. "
                    "Primary product profitability metric. KEY MEASURE."),
    SchemaField("cm_ii",         "NUMERIC", "REQUIRED",
        description="Contribution Margin II (Net Contribution Margin). "
                    "cm_ii = cm_i + freight_cost + commission. Company FY2025 average ~30.5% of net_revenue. "
                    "Primary segment profitability metric used in executive reporting. KEY MEASURE."),
    SchemaField("volume_units",  "NUMERIC", "REQUIRED",
        description="Units sold in the transaction. Used for volume-weighted analysis and "
                    "average selling price calculations."),
]

TABLE_OPTIONS = bigquery.Table(
    "agent9-465818.meridian_copa.copa_line_items",
    schema=COPA_SCHEMA
)
TABLE_OPTIONS.description = (
    "SAP S/4HANA CO-PA line items for Meridian Flow Systems (synthetic). "
    "Industrial pump, valve, and flow control equipment manufacturer. "
    "Stepped contribution margin analysis (CM I, CM II) across 21 customer, product, "
    "and organisational dimensions — including order type (catalog vs engineered vs aftermarket), "
    "customer industry, and product division. Nightly batch load via BigQuery Data Transfer Service. "
    "Fiscal year: calendar year (January = Period 1, December = Period 12). "
    "Covers FY2024, FY2025, FY2026 full year. Use fiscal_year + fiscal_period for all time filtering."
)
TABLE_OPTIONS.labels = {
    "source_system":    "sap_s4",
    "extract_type":     "copa",
    "domain":           "finance",
    "subdomain":        "profitability",
    "refresh_cadence":  "daily_batch",
    "client_id":        "meridian",
    "data_sensitivity": "internal",
    "onboarding_ready": "true",
}
TABLE_OPTIONS.time_partitioning = bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.MONTH,
    field="posting_date"
)
```

**Why column descriptions matter for onboarding:**
- `DPA._profile_table_bigquery()` surfaces them in Step 1 schema inspection output
- KPI Assistant LLM reads descriptions to identify which columns are KPI measures vs dimensions vs metadata
- The `KEY MEASURE` tag in value field descriptions signals to the LLM which fields to suggest as KPI numerators
- The `TimeDimension:` tag in period column descriptions guides the Time Dimension Mapping Wizard (Phase 12)
- The `NOT an analytical dimension` tag on `updated_at` prevents it from appearing as a suggested dimension
- High-cardinality warning on `customer_id` prevents it from being suggested as a GROUP BY dimension

**Total dimensions: 21** (20 original + `order_type`)  
**Total value fields (KPI measures): 9**  
**Total columns: 34** (4 time/metadata + 21 analytical dimensions + 9 value fields)

---

## 3. Dimension Profiles

Designed so the EDA importance ranking is **deterministic** — unit tests can assert exact rank positions.

### Expected EDA Importance Ranking (Baseline)

The pump business has a uniquely powerful top dimension: `order_type` creates a 23pp CM I spread within the same factory between catalog standard (32%) and aftermarket parts (55%). No other dimension in a typical CO-PA extract has this spread at this cardinality.

| Rank | Dimension | Cardinality | Concentration Ratio (top-3 share) | CM Variance Score | Why it ranks here |
|---|---|---|---|---|---|
| 1 | `order_type` | 4 | 0.92 (top-3 = 92%) | **Very High** — 23pp CM I spread (CATALOG_STANDARD 32% vs AFTERMARKET_PARTS 55%) | Strongest single profitability driver in the model — low cardinality × extreme margin variance |
| 2 | `customer_group` | 5 | 0.83 (top-3 = 83%) | High — 14pp CM II spread (TIER1_UTILITIES 36% vs DISTRIBUTOR_ACCOUNTS 22%) | Strategic segmentation drives net contribution; high concentration amplifies signal |
| 3 | `product_hierarchy_l1` | 5 | 0.76 | High — 22pp CM I spread (AFTERMARKET_SERVICE 55% vs CENTRIFUGAL_PUMPS 33%) | Product division captures mix between catalog/engineered/aftermarket above L2 detail |
| 4 | `industry` | 7 | 0.78 | High — 9pp CM II spread (OIL_GAS 34% vs GENERAL_INDUSTRIAL 25%) | Industry determines pricing power, specification requirements, and contract structure |
| 5 | `distribution_channel` | 4 | 0.93 | Medium-high — 15pp CM II spread (DIRECT_SALES 35% vs DISTRIBUTOR_STOCK 20%) | Channel has major margin impact but partially collinear with order_type |
| 6 | `sales_district` | 8 | 0.63 | Medium-high — 6pp freight-driven CM II spread | Geographic freight costs differentiate CM II clearly, especially WEST_US vs MIDWEST_US |
| 7 | `plant` | 5 | 0.74 | Medium — 5pp COGS variance | PLANT_TEXAS (ETO facility) vs PLANT_OHIO (standard) drives capacity utilisation variance |
| 8 | `product_hierarchy_l2` | 17 | 0.51 | Medium | Sub-category product mix moderately explanatory within each division |
| 9 | `material_group` | 12 | 0.57 | Medium | Component category moderately concentrated; seals/bearings vs castings cost profiles differ |
| 10 | `payment_terms` | 5 | 0.80 | Low — CM barely varies by payment terms | High concentration but deductions don't change significantly by payment schedule |
| 11 | `sales_office` | 6 | 0.66 | Low-medium | Office performance moderately uniform; regional variation minor |
| 12 | `profit_center` | 8 | 0.60 | Low | Near-uniform CM distribution across profit centers |
| 13 | `division` | 4 | 0.71 | Low | Overlaps heavily with `product_hierarchy_l1` — informationally redundant |
| 14 | `credit_tier` | 4 | 0.78 | Very low | Credit tier barely affects CM outcomes |
| 15 | `sales_org` | 2 | 0.96 | Very low | Near 95/5 split; minimal variance signal |
| 16 | `customer_classification` | 3 | 0.87 | Very low | Coarse segmentation; overlaps with customer_group |
| 17 | `customer_id` | ~820 | 0.17 | Excluded | Too high cardinality for GROUP BY dimensional analysis |
| 18 | `posting_date` | — | — | Excluded | Time dimension, not an analytical dimension |
| 19 | `fiscal_year` | — | — | Excluded | Time dimension |
| 20 | `fiscal_period` | — | — | Excluded | Time dimension |
| 21 | `updated_at` | — | — | Excluded | ETL metadata, not analytical |

**Unit test assertions:**
```python
assert profile.dimensions[0].dimension == "order_type"
assert profile.dimensions[1].dimension == "customer_group"
assert profile.dimensions[2].dimension == "product_hierarchy_l1"
# order_type CM I spread must be captured in the profile
assert profile.dimensions[0].cm_variance_score > profile.dimensions[1].cm_variance_score
# Low-signal dimensions ranked below 12th
low_signal = [d.dimension for d in profile.dimensions[12:]]
assert "sales_org" in low_signal
assert "customer_classification" in low_signal
```

---

### Dimension Member Values

#### `order_type` (4 members — **primary profitability driver, rank #1**)
| Member | Revenue Share | CM I % | CM II % | Notes |
|---|---|---|---|---|
| `CATALOG_STANDARD` | 42% | 32% | 24% | Price list products, competitive pricing, thin margin |
| `ENGINEERED_TO_ORDER` | 35% | 46% | 38% | Custom-engineered; specification-based, less price competition |
| `AFTERMARKET_PARTS` | 15% | 55% | 48% | Captive customer installed base; premium pricing, low freight |
| `SERVICE_CONTRACT` | 8% | 40% | 35% | Recurring annual revenue; predictable cost structure |

**Concentration ratio:** (42+35+15) = 92% → `0.92`  
**CM I spread:** 55% − 32% = **23pp** → extreme variance → rank #1  
**Why this dimension matters:** The same centrifugal pump plant that earns 32% CM I on a standard catalog pump earns 55% on the aftermarket impeller kit two years later. CFOs rarely see this cleanly; the mixed-order blending in P&L hides the magnitude.

#### `customer_group` (5 members — **rank #2**)
| Member | Revenue Share | CM I % | CM II % | Notes |
|---|---|---|---|---|
| `TIER1_UTILITIES` | 35% | 42% | 36% | Large municipal and utility accounts; long-term framework contracts, low deductions, direct delivery |
| `TIER2_INDUSTRIAL` | 28% | 38% | 31% | Mid-size industrial plants; standard terms, repeat purchase |
| `REGIONAL_CONTRACTORS` | 20% | 35% | 27% | EPC firms and system integrators; project-based, commission driven |
| `DISTRIBUTOR_ACCOUNTS` | 13% | 30% | 22% | Stocking distributors; volume discounts, complex logistics |
| `EXPORT_OEM` | 4% | 36% | 28% | Export customers and OEM manufacturers; variable freight, competitive pricing |

**Concentration ratio:** (35+28+20) = 83% → `0.83`  
**CM II spread:** 36% − 22% = **14pp** → high variance → rank #2

#### `product_hierarchy_l1` (5 divisions — **rank #3**)
| Member | Revenue Share | CM I % | CM II % | Primary order types |
|---|---|---|---|---|
| `CENTRIFUGAL_PUMPS` | 38% | 33% | 26% | CATALOG_STANDARD, ENGINEERED_TO_ORDER |
| `POSITIVE_DISPLACEMENT` | 22% | 37% | 30% | ENGINEERED_TO_ORDER, CATALOG_STANDARD |
| `CONTROL_VALVES` | 18% | 40% | 34% | ENGINEERED_TO_ORDER, CATALOG_STANDARD |
| `METERING_SYSTEMS` | 12% | 44% | 38% | ENGINEERED_TO_ORDER (skid systems) |
| `AFTERMARKET_SERVICE` | 10% | 55% | 48% | AFTERMARKET_PARTS, SERVICE_CONTRACT |

**Concentration ratio:** (38+22+18) = 78% → `0.78`  
**CM I spread:** 55% − 33% = **22pp** → rank #3  
**Note:** `AFTERMARKET_SERVICE` division is highly correlated with `order_type=AFTERMARKET_PARTS`; both will surface in dimensional analysis, demonstrating signal redundancy detection.

#### `product_hierarchy_l2` (17 sub-categories)
| Division | Sub-categories |
|---|---|
| `CENTRIFUGAL_PUMPS` | End-Suction, Split-Case, Vertical-Turbine, Submersible |
| `POSITIVE_DISPLACEMENT` | Gear-Pumps, Lobe-Pumps, Diaphragm-Pumps, Peristaltic |
| `CONTROL_VALVES` | Ball-Valves, Butterfly-Valves, Gate-Globe-Valves, Check-Valves |
| `METERING_SYSTEMS` | Chemical-Dosing-Skids, Flow-Meters, Blending-Systems |
| `AFTERMARKET_SERVICE` | OEM-Spare-Parts, Service-Contracts, Emergency-Repair |

Revenue distributed proportionally within each division with ±30% variance between sub-categories.

#### `industry` (7 members — **drift signal dimension, rank #4**)
| Member | Baseline Revenue Share | Drifted Revenue Share | Typical CM II % |
|---|---|---|---|
| `WATER_WASTEWATER` | 38% | 32% | 34% (long framework contracts) |
| `OIL_GAS` | 22% | 20% | 34% (spec-driven, premium products) |
| `CHEMICAL_PROCESS` | 18% | 16% | 31% (corrosion-resistant materials required) |
| `FOOD_BEVERAGE` | 11% | 14% | 29% (sanitary grade, lower volume) |
| `MINING` | 6% | 4% | 25% (slurry duty, high warranty cost) |
| `GENERAL_INDUSTRIAL` | 4% | 8% | 25% (highly price-competitive) |
| `POWER_GENERATION` | 1% | 6% | 28% (low volume, complex spec) |

**Baseline concentration ratio:** (38+22+18) = 78% → `0.78`  
**Drifted concentration ratio:** (32+20+16) = 68% → `0.68`  
**Change:** |0.68 − 0.78| / 0.78 = **12.8%** (below 20% absolute threshold but above the 18% test config threshold — see Scenario C2 for exact parameterisation)

**Drift narrative:** A water utility framework contract shifted to competitive rebid (WATER_WASTEWATER −6pp) while a distributor expanded into the general industrial and power generation markets. The system surfaces this as a distribution shift — CM II under pressure because GENERAL_INDUSTRIAL and POWER_GENERATION are lower-margin end markets.

#### `sales_district` (8 members)
| Member | Revenue Share | Freight Impact on CM II |
|---|---|---|
| `NORTHEAST_US` | 24% | High (dense urban, expensive last-mile delivery to utility sites) |
| `MIDWEST_US` | 21% | Low (central location, closest to PLANT_OHIO and PLANT_ILLINOIS) |
| `SOUTHEAST_US` | 18% | Medium (PLANT_GEORGIA nearby) |
| `SOUTHWEST_US` | 15% | Medium-low (proximity to PLANT_TEXAS) |
| `WEST_US` | 12% | High (distance from all manufacturing plants) |
| `CANADA` | 6% | Medium (cross-border costs, PLANT_ONTARIO for local) |
| `MEXICO` | 3% | Medium-high (cross-border complexity) |
| `EXPORT_ROW` | 1% | Very high |

**Concentration ratio:** (24+21+18) = 63% → `0.63`

#### `distribution_channel` (4 members — **rank #5**)
| Member | Revenue Share | CM II % | Notes |
|---|---|---|---|
| `DIRECT_SALES` | 48% | 35% | Project/direct to end user; no channel margin, highest CM II |
| `DISTRIBUTOR_STOCK` | 30% | 20% | Stocking distributor discount erodes CM significantly |
| `ENGINEERED_REP` | 15% | 30% | Manufacturer's rep; commission paid but specification assistance adds value |
| `ONLINE_CATALOG` | 7% | 28% | E-commerce for spare parts; growing, low transaction cost |

**Concentration ratio:** (48+30+15) = 93% → `0.93`  
**CM II spread:** 35% − 20% = **15pp** → high variance

#### `payment_terms` (5 members — **variance spike dimension**)
| Member | Baseline Transaction Share | Drifted Transaction Share |
|---|---|---|
| `NET_30` | 48% | 31% |
| `NET_60` | 27% | 22% |
| `NET_45` | 15% | 14% |
| `IMMEDIATE` | 7% | 21% |
| `NET_90` | 3% | 12% |

**Baseline CoV:** ~0.07 (very stable — CM barely varies by payment terms)  
**Drifted CoV:** ~0.16 (distribution shifted by TIER1_UTILITIES renegotiating terms on framework contract renewal)  
**Change:** 0.16 / 0.07 = **2.3× baseline** → triggers `variance_spike` signal

#### `plant` (5 members)
| Member | Revenue Share | Primary product | CM I % |
|---|---|---|---|
| `PLANT_OHIO` | 35% | Centrifugal pumps — standard catalogue | 33% |
| `PLANT_TEXAS` | 28% | Engineered-to-order and custom specials | 46% |
| `PLANT_GEORGIA` | 18% | Control valves and actuator packages | 40% |
| `PLANT_ILLINOIS` | 14% | Metering systems and chemical dosing skids | 44% |
| `PLANT_ONTARIO` | 5% | Canadian operations — mixed product range | 36% |

#### `sales_office` (6 members)
`OFFICE_CHICAGO`, `OFFICE_HOUSTON`, `OFFICE_ATLANTA`, `OFFICE_NYC`, `OFFICE_LA`, `OFFICE_TORONTO`

#### `profit_center` (8 members)
`PC_CENTRIFUGAL_NA`, `PC_PD_PUMPS_NA`, `PC_VALVES_NA`, `PC_METERING_NA`, `PC_AFTERMARKET`, `PC_EXPORT`, `PC_CANADA`, `PC_SHARED_SVC`

#### `sales_org` (2 members)
`SORG_NA` (95% revenue), `SORG_INTL` (5% revenue)

#### `division` (4 members)
`DIV_PUMPS`, `DIV_VALVES`, `DIV_METERING`, `DIV_AFTERMARKET`

#### `customer_classification` (3 members)
`CLASS_A` (key accounts, 55% revenue), `CLASS_B` (40%), `CLASS_C` (tail accounts, 5%)

#### `credit_tier` (4 members)
`TIER_PLATINUM`, `TIER_GOLD`, `TIER_STANDARD`, `TIER_WATCH`  
Revenue shares: 45%, 35%, 18%, 2% — near-uniform CM, ranks low

#### `material_group` (12 members)
`MG_CASTINGS` (iron/stainless castings), `MG_IMPELLERS` (impellers and wear rings), `MG_SEALS` (mechanical seals and packing), `MG_BEARINGS` (bearings and housings), `MG_MOTORS` (electric motors and drives), `MG_ACTUATORS` (pneumatic and electric actuators), `MG_VALVEBODY` (valve bodies and trim), `MG_CONTROLS` (control electronics and instrumentation), `MG_FABRICATION` (fabricated steel components), `MG_RUBBER` (elastomers and soft goods), `MG_FASTENERS` (fasteners and hardware), `MG_SUBASSEMBLY` (purchased sub-assemblies)

---

## 4. Value Field Distribution Logic

### Revenue Scale
| Fiscal Year | Total Net Revenue | YoY Growth |
|---|---|---|
| FY2024 | $148M | baseline |
| FY2025 | $165M | +11.5% (strong demand from water infrastructure investment cycle) |

Monthly seasonality index (period 1–12):
`[0.68, 0.74, 0.86, 0.96, 1.04, 1.10, 0.99, 0.92, 1.06, 1.14, 1.20, 1.31]`

Peak in December (end-of-year capital project closures and maintenance contract renewals), trough in January.

### Contribution Margin Waterfall (company-level averages, FY2025 baseline)
| Line | Average % of Gross Revenue |
|---|---|
| Gross Revenue | 100% |
| Sales Deductions | −17% |
| **Net Revenue** | **83%** |
| Standard COGS | −46% |
| **CM I (Gross Margin)** | **37%** |
| Freight Cost | −4% |
| Commission | −2.5% |
| **CM II (Net Contribution)** | **30.5%** |

**Why CM I is 37% (higher than typical industrial):** The FY2025 baseline has a healthy order_type mix — 35% ENGINEERED_TO_ORDER (46% CM I) and 15% AFTERMARKET_PARTS (55% CM I) pulling the blended average above 35%. The FY2026 story is a mix shift away from this healthy baseline.

Each dimension combination modifies these averages by ±10pp based on the member's profile. Generated row-by-row with normal distribution noise (σ = 2pp) for realism.

### Row-level Generation Rules
- `net_revenue = gross_revenue + sales_deductions` (sales_deductions is negative)
- `cm_i = net_revenue + standard_cogs` (standard_cogs is negative)
- `cm_ii = cm_i + freight_cost + commission` (both negative)
- Value fields always internally consistent — no negative net_revenue rows
- `volume_units` correlated with `net_revenue / (avg_selling_price_by_material_group)`

---

## 5. Row Volume

| Scenario | Table | Rows | Periods |
|---|---|---|---|
| B + D (baseline) | `copa_line_items` | 79,200 | FY2024 P1–P12 + FY2025 P1–P12 + FY2026 P1–P12 |
| C-baseline | `copa_baseline` | 26,400 | FY2025 P1–P12 only |
| C-drifted | `copa_drifted` | 26,400 | FY2025 P1–P12 (same structure, modified distributions) |

**Row construction:** 2,200 rows per period throughout all three years.  
Each row = one document (realistic CO-PA line item level — one sale per customer per material per period).  
**Seed:** fixed `random.seed(42)` for full reproducibility.

### FY2026 Full Year Design

FY2026 is split into two halves with different performance profiles. This creates a complete story arc usable at any point in the 2026 demo year.

#### H1 2026 (P1–P6) — Margin Compression

Designed to fire **live situation cards** when SA runs the enterprise assessment. YoY comparison: FY2026 P1–P6 vs FY2025 P1–P6.

| KPI | FY2025 H1 | FY2026 H1 | Change | SA Outcome |
|---|---|---|---|---|
| Net Revenue | $80M | $86.4M | +8% YoY | No breach — healthy revenue growth |
| CM I % | 37.0% | 34.4% | −2.6pp | ⚠️ **Warning** (threshold: −2pp) |
| CM II % | 30.5% | 27.8% | −2.7pp | ⚠️ **Warning** (threshold: −1.5pp) |
| Freight Cost % | 3.8% | 4.5% | +0.7pp | ⚠️ **Warning** (threshold: +0.5pp) |
| Sales Deduction Rate | 17.0% | 17.6% | +0.6pp | No breach — near threshold |

Three situation cards fire. DA surfaces the root causes:

- **`order_type` mix shift:** CATALOG_STANDARD share increases from 42% → 53% as several ENGINEERED_TO_ORDER projects are delayed into H2. Lower-margin standard pump orders fill the capacity gap. This single dimension explains ~70% of the CM I compression when DA runs across all 21 dimensions.
- **`PLANT_TEXAS` cost absorption:** The ETO manufacturing facility (PLANT_TEXAS) runs below capacity utilisation (target: 78%, actual: 61%) as engineered projects slip. Fixed overhead spreads across fewer units → standard COGS variance unfavourable.
- **`NORTHEAST_US` freight:** Water utility project deliveries to dense urban sites in Q1–Q2 push last-mile freight costs above prior year.

**`industry` dimension — early drift (H1):**
`WATER_WASTEWATER` moves to 34% (from 38% in FY2025), `GENERAL_INDUSTRIAL` to 6% (from 4%). Below the distribution shift threshold — visible in dimensional analysis as an emerging pattern but not yet a situation card. This is a leading indicator: general industrial customers are replacing some of the utility framework volume, and their CM II is 9pp lower.

#### H2 2026 (P7–P12) — Partial Recovery

Management received the H1 briefings and approved corrective actions via the HITL workflow. H2 reflects a realistic partial recovery — not a V-shape reversal, but measurable improvement. This powers the VA trajectory chart and the "solutions working" narrative.

| KPI | FY2025 H2 | FY2026 H2 | Change vs H2 2025 | Change vs H1 2026 |
|---|---|---|---|---|
| Net Revenue | $85M | $95.0M | +11.8% | +9.9% (H2 vs H1 2026) |
| CM I % | 37.2% | 35.6% | −1.6pp (below warning) | +1.2pp recovery |
| CM II % | 30.6% | 28.9% | −1.7pp (warning level) | +1.1pp recovery |
| Freight Cost % | 3.7% | 4.1% | +0.4pp (below warning) | −0.4pp improvement |
| Sales Deduction Rate | 17.0% | 17.3% | +0.3pp (no breach) | −0.3pp improvement |

**Net revenue in H2 2026 is higher than H1** — the delayed ENGINEERED_TO_ORDER projects from H1 convert in Q3/Q4. This is the pump business model: ETO backlogs are lumpy. Revenue accelerates in H2 and order type mix improves as ETO converts. This is a realistic pump company dynamics: long ETO lead times create natural H1/H2 revenue phasing.

**Period-level CM I % progression across FY2026:**
```
P1: 33.8%   P2: 34.1%   P3: 34.5%   P4: 34.6%   P5: 34.8%   P6: 34.7%
P7: 35.1%   P8: 35.4%   P9: 35.6%   P10: 35.8%  P11: 35.9%  P12: 36.1%
```
H1 = below 37% FY2025 baseline → warnings fire. H2 = ETO backlog converts, mix improves, CM I recovers toward baseline.  
The TrajectoryChart renders this as: cost-of-inaction line diverging downward in H1, actual line recovering toward expected through H2, validating the approved corrective action (accelerate ETO conversion, improve plant scheduling at PLANT_TEXAS).

**Full year 2026 totals:**
- Net Revenue: ~$181M (vs $165M FY2025 = +9.7% — strong infrastructure-driven demand)
- CM I %: ~35.0% full year average (vs 37.0% FY2025 = −2.0pp — H1 compression partially offset by H2 recovery)
- CM II %: ~28.4% full year average (vs 30.5% FY2025 = −2.1pp)

**`updated_at` for all FY2026 rows:**
Set to `2026-06-08T02:14:33Z` (yesterday's nightly batch) regardless of fiscal period. All 26,400 FY2026 rows were loaded in a single historical pre-load. `MAX(updated_at)` across the table = yesterday → cadence probe classifies as `daily_batch / healthy` without requiring the cadence views. P7–P12 data exists in the table from day one of the demo dataset — it is synthetic projected actuals, not a forecast table.

---

## 6. Four Scenario Designs

### Scenario A — Cadence Sensing (Phase 11K)

Three BigQuery **views** over `copa_line_items`. Each overrides `updated_at` with a computed value:

```sql
-- copa_fresh: simulates real-time / same-day feed
CREATE VIEW meridian_copa.copa_fresh AS
SELECT * REPLACE (CURRENT_TIMESTAMP() - INTERVAL 1 HOUR AS updated_at)
FROM meridian_copa.copa_line_items;

-- copa_nightly: simulates healthy daily_batch (ran ~8 hours ago)
CREATE VIEW meridian_copa.copa_nightly AS
SELECT * REPLACE (CURRENT_TIMESTAMP() - INTERVAL 20 HOUR AS updated_at)
FROM meridian_copa.copa_line_items;

-- copa_stale: simulates pipeline failure (3 days since last refresh)
CREATE VIEW meridian_copa.copa_stale AS
SELECT * REPLACE (CURRENT_TIMESTAMP() - INTERVAL 72 HOUR AS updated_at)
FROM meridian_copa.copa_line_items;
```

**Test assertions:**
- `copa_fresh` → `classify_refresh_cadence()` returns `"real_time"` or `"micro_batch"`
- `copa_nightly` → returns `"daily_batch"`
- `copa_stale` → `check_pipeline_health()` returns `"stale"` → `pipeline_failure` situation card emitted

---

### Scenario B — EDA Baseline (Phase 11L)

**Source:** `copa_line_items` (full 52,800 row dataset)

**Test assertions (deterministic):**
```python
profile = await dga.compute_dimension_profile("meridian_copa", "meridian")

assert profile.dimensions[0].dimension == "customer_group"
assert profile.dimensions[0].concentration_ratio > 0.80
assert profile.dimensions[1].dimension == "product_hierarchy_l1"
assert profile.dimensions[4].dimension == "sales_district"

# Low-signal dimensions ranked below top 10
low_signal = [d.dimension for d in profile.dimensions[10:]]
assert "sales_org" in low_signal
assert "customer_classification" in low_signal

# Excluded dimensions not in profile
all_dims = [d.dimension for d in profile.dimensions]
assert "customer_id" not in all_dims      # cardinality > 500 → excluded
assert "fiscal_year" not in all_dims      # time dimension → excluded
```

**Cardinality exclusion rule:** dimensions with `cardinality > 200` are excluded from profiling (too fine-grained for GROUP BY analysis). Only `customer_id` (850 unique values) triggers this.

---

### Scenario C — Drift Signal Detection (Phase 11M)

Two tables: `copa_baseline` and `copa_drifted`.

`copa_baseline` = FY2025 slice of `copa_line_items` with no modifications.

`copa_drifted` = same structure, same row count, with four controlled perturbations:

#### C1 — New Dimension Member (`new_member` signal)
**Dimension:** `customer_group`  
**Perturbation:** 5% of rows in `copa_drifted` have `customer_group = "DIGITAL_NATIVE_OEM"` (not present in `copa_baseline`).  
Reassigned from `EXPORT_OEM` rows (reducing that group from 4% → 0% and adding DIGITAL_NATIVE_OEM at 4%).  
**Business meaning:** A new class of IoT-connected pump OEMs (industrial automation companies embedding pumps in smart factory equipment) has started ordering. They demand standard catalog products in high volumes. Their order type is exclusively CATALOG_STANDARD → lower-margin orders from a previously untracked customer group.

**Test assertion:**
```python
result = await cda.sample_and_compare(
    data_product_id="meridian_copa", client_id="meridian",
    baseline_profile=baseline_profile
)
new_member_signals = [s for s in result.signals if s.signal_type == "new_member"]
assert len(new_member_signals) == 1
assert new_member_signals[0].dimension == "customer_group"
assert "DIGITAL_NATIVE_OEM" in new_member_signals[0].details
```

#### C2 — Distribution Shift (`distribution_shift` signal)
**Dimension:** `industry`  
**Perturbation:** `WATER_WASTEWATER` share drops from 38% → 20%; `GENERAL_INDUSTRIAL` rises from 4% → 18%; `POWER_GENERATION` rises from 1% → 8%. Total revenue unchanged.  
**Business meaning:** A large water utility framework contract did not renew (re-bid went to a lower-cost competitor on the catalog product lines). Volume was replaced with general industrial and power generation orders — lower-margin end markets.

**Baseline concentration ratio:** (38+22+18) = 78% → `0.78`  
**Drifted concentration ratio:** (22+20+18) = 60% → `0.60`  
**Relative change:** |0.60 − 0.78| / 0.78 = **23.1%** — above `0.18` threshold (threshold set conservatively in test config to ensure reliable trigger even with floating-point variance)

**Test assertion:**
```python
dist_signals = [s for s in result.signals if s.signal_type == "distribution_shift"]
assert len(dist_signals) == 1
assert dist_signals[0].dimension == "industry"
assert dist_signals[0].magnitude > 0.18
```

#### C3 — Volume Anomaly (`volume_anomaly` signal)
**Perturbation:** FY2025 P12 (December) `net_revenue` values multiplied by 2.4× in `copa_drifted`.  
December is already the seasonal peak (seasonality index 1.37). Multiplying by 2.4 pushes the period 3.3σ above the 12-period rolling mean.

**Rolling mean computation:** `AVG(SUM(net_revenue)) OVER (PARTITION BY fiscal_year ORDER BY fiscal_period ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING)`  
**Threshold:** > 2σ triggers signal.

**Test assertion:**
```python
vol_signals = [s for s in result.signals if s.signal_type == "volume_anomaly"]
assert len(vol_signals) == 1
assert vol_signals[0].magnitude > 2.0   # σ units above mean
```

#### C4 — Variance Spike (`variance_spike` signal)
**Dimension:** `payment_terms`  
**Perturbation:** `NET_30` share drops from 48% → 31%; `IMMEDIATE` rises from 7% → 21%; `NET_90` rises from 3% → 12%. Revenue unchanged but payment term distribution destabilises.  
**Business meaning:** A TIER1_UTILITIES customer renegotiated their framework contract terms, shifting from NET_30 to NET_90 on a large portion of their orders (cash flow pressure on the utility's budget). A new DISTRIBUTOR_ACCOUNTS customer cluster demanded IMMEDIATE payment terms to access volume discounts. The payment term mix has never been this polarised.  
**Baseline CoV:** 0.07 → **Drifted CoV:** 0.16 (2.3× baseline → above 2.0× threshold).

**Test assertion:**
```python
var_signals = [s for s in result.signals if s.signal_type == "variance_spike"]
assert len(var_signals) == 1
assert var_signals[0].dimension == "payment_terms"
assert var_signals[0].magnitude > 2.0   # × baseline CoV
```

#### Combined drift test
All four perturbations applied simultaneously in `copa_drifted`:
```python
assert result.trigger_da == True
assert len(result.signals) == 4
assert result.affected_kpi_ids == ["net_revenue", "cm_i_pct", "cm_ii_pct"]
```

---

### Scenario D — Pre-Computed DA Results (Phase 11N)

Seeded rows in `da_background_runs` Supabase table. No BQ queries required — tests the UI pre-computed path.

**Seed file:** `tests/fixtures/da_background_runs_seed.json`

Seed content: one complete `DeepAnalysisResponse` JSON for `kpi_id="cm_i_pct"`, `client_id="meridian"` with:
- `kt_is_is_not.where_is`: 21 rows across all 16 analysed dimensions (top problem segments — full 21-dimension run in scheduled mode)
- `kt_is_is_not.where_is_not`: 15 rows (top benchmark segments)  
- `summary_view.top_dimensions`: `["order_type", "customer_group", "product_hierarchy_l1", "industry", "distribution_channel"]`
- `summary_view.is_items`: 3 rows (CATALOG_STANDARD/DISTRIBUTOR_ACCOUNTS/GENERAL_INDUSTRIAL — the three worst-performing segments)
- `summary_view.is_not_items`: 3 rows (AFTERMARKET_PARTS/TIER1_UTILITIES/OIL_GAS — the benchmark segments delivering highest CM I)
- `da_state`: `"precomputed"`
- `da_completed_at`: `"2026-06-09T06:14:00Z"`

**Test assertions (Phase 11N UI):**
- `GET /api/v1/deep-analysis/background/net_revenue?client_id=meridian` returns the seeded result
- Council Debate view opens with accordion: top 5 dimensions expanded, dimensions 6–15 collapsed
- Importance badges render: `#1 · order_type`, `#2 · customer_group`, `#3 · product_hierarchy_l1`
- SA card badge shows: `"Analysis ready · today at 06:14"`
- "View Analysis" button loads pre-computed result without triggering new DA run
- Accordion: `order_type` and `customer_group` expanded by default; remaining 14 dimensions collapsed with importance rank badge

---

## 7. KPI Definitions

Five KPIs registered in Supabase for `client_id = "meridian"`:

```python
KPIDefinition(
    id="net_revenue",
    client_id="meridian",
    name="Net Revenue",
    data_product_id="meridian_copa",
    sql_query="""
        SELECT SUM(net_revenue)
        FROM `agent9-465818.meridian_copa.copa_line_items`
        WHERE fiscal_year = {year}
          AND fiscal_period <= {period}
    """,
    unit="$",
    direction="higher_is_better",
    threshold_warning=-0.05,
    threshold_critical=-0.10,
    comparison_period="yoy",
    dimensions=["order_type", "customer_group", "product_hierarchy_l1", "industry",
                "distribution_channel", "sales_district", "plant",
                "product_hierarchy_l2", "material_group", "payment_terms",
                "sales_office", "profit_center", "division",
                "credit_tier", "sales_org", "customer_classification"]
)

KPIDefinition(
    id="cm_i_pct",
    client_id="meridian",
    name="Gross Margin %",
    data_product_id="meridian_copa",
    sql_query="""
        SELECT SAFE_DIVIDE(SUM(cm_i), SUM(net_revenue)) * 100
        FROM `agent9-465818.meridian_copa.copa_line_items`
        WHERE fiscal_year = {year}
          AND fiscal_period <= {period}
    """,
    unit="%",
    direction="higher_is_better",
    threshold_warning=-2.0,    # 2pp decline
    threshold_critical=-4.0,
    comparison_period="yoy",
    dimensions=["order_type", "customer_group", "product_hierarchy_l1", "industry",
                "distribution_channel", "plant", "material_group"]
)

KPIDefinition(
    id="cm_ii_pct",
    client_id="meridian",
    name="Net Contribution Margin %",
    data_product_id="meridian_copa",
    sql_query="""
        SELECT SAFE_DIVIDE(SUM(cm_ii), SUM(net_revenue)) * 100
        FROM `agent9-465818.meridian_copa.copa_line_items`
        WHERE fiscal_year = {year}
          AND fiscal_period <= {period}
    """,
    unit="%",
    direction="higher_is_better",
    threshold_warning=-1.5,
    threshold_critical=-3.0,
    comparison_period="yoy",
    dimensions=["order_type", "customer_group", "product_hierarchy_l1", "industry",
                "distribution_channel", "sales_district"]
)

KPIDefinition(
    id="sales_deduction_rate",
    client_id="meridian",
    name="Sales Deduction Rate",
    data_product_id="meridian_copa",
    sql_query="""
        SELECT SAFE_DIVIDE(ABS(SUM(sales_deductions)), SUM(gross_revenue)) * 100
        FROM `agent9-465818.meridian_copa.copa_line_items`
        WHERE fiscal_year = {year}
          AND fiscal_period <= {period}
    """,
    unit="%",
    direction="lower_is_better",
    inverse_logic=True,
    threshold_warning=1.5,     # 1.5pp increase = bad
    threshold_critical=3.0,
    comparison_period="yoy",
    dimensions=["order_type", "customer_group", "distribution_channel", "industry", "payment_terms"]
)

KPIDefinition(
    id="freight_cost_pct",
    client_id="meridian",
    name="Freight Cost as % of Net Revenue",
    data_product_id="meridian_copa",
    sql_query="""
        SELECT SAFE_DIVIDE(ABS(SUM(freight_cost)), SUM(net_revenue)) * 100
        FROM `agent9-465818.meridian_copa.copa_line_items`
        WHERE fiscal_year = {year}
          AND fiscal_period <= {period}
    """,
    unit="%",
    direction="lower_is_better",
    inverse_logic=True,
    threshold_warning=0.5,
    threshold_critical=1.0,
    comparison_period="yoy",
    dimensions=["sales_district", "plant", "distribution_channel", "customer_group"]
)
```

---

## 8. Data Product Contract

```python
DataProduct(
    id="meridian_copa",
    client_id="meridian",
    name="Meridian CO-PA Line Items",
    description="SAP S/4HANA CO-PA extraction — stepped contribution margin by 21 dimensions including order type (catalog / engineered / aftermarket / service contract). Nightly batch load via BigQuery Data Transfer. Industrial pump and flow control equipment manufacturer.",
    source_system="bigquery",
    project_id="agent9-465818",
    dataset_id="meridian_copa",
    table_id="copa_line_items",
    time_dimensions=[
        {
            "type": "fiscal_year_period",
            "year_column": "fiscal_year",
            "period_column": "fiscal_period",
            "period_type": "month",
            "primary": True
        }
    ],
    dimension_semantics=[
        {"column": "order_type",            "label": "Order Type"},
        {"column": "customer_group",        "label": "Customer Group"},
        {"column": "industry",              "label": "Customer Industry"},
        {"column": "sales_district",        "label": "Sales District"},
        {"column": "payment_terms",         "label": "Payment Terms"},
        {"column": "material_group",        "label": "Material Group"},
        {"column": "product_hierarchy_l1",  "label": "Product Division"},
        {"column": "product_hierarchy_l2",  "label": "Product Sub-Category"},
        {"column": "sales_org",             "label": "Sales Organisation"},
        {"column": "distribution_channel",  "label": "Distribution Channel"},
        {"column": "sales_office",          "label": "Sales Office"},
        {"column": "plant",                 "label": "Manufacturing Plant"},
        {"column": "profit_center",         "label": "Profit Centre"},
        {"column": "division",              "label": "Business Division"},
        {"column": "customer_classification","label": "Customer Classification"},
        {"column": "credit_tier",           "label": "Credit Tier"},
    ],
    # 21 analytical dimensions total — excludes customer_id (high cardinality) and all time/metadata columns
    refresh_cadence="daily_batch",           # known at spec time; confirmed by Phase 11K
    metadata={
        "source_system_detail": "SAP S/4HANA CO-PA via BigQuery Data Transfer Service",
        "extraction_schedule": "nightly 02:00 UTC",
        "fiscal_year_start_month": 1
    }
)
```

---

## 9. Seed Script Requirements

**File:** `scripts/clients/meridian.py`  
**Pattern:** mirrors `scripts/clients/lubricants.py`

### What the script must do

1. **Create BQ dataset** `agent9-465818.meridian_copa` if not exists
2. **Generate and load `copa_line_items`** (79,200 rows — FY2024, FY2025, FY2026 all 12 periods):
   - Fixed `random.seed(42)` — fully reproducible
   - Dimension combinations drawn from member lists with revenue-weighted probabilities
   - Value fields computed from dimension combination averages + normal noise (σ = 2pp)
   - Internal consistency enforced: `cm_i = net_revenue + standard_cogs`, `cm_ii = cm_i + freight_cost + commission`
   - **FY2026 H1 (P1–P6):** apply margin compression profile (CM I −2.6pp, CM II −2.7pp, freight +0.7pp vs FY2025 H1)
   - **FY2026 H2 (P7–P12):** apply partial recovery profile per period-level CM I % progression table (Section 5)
   - **All FY2026 `updated_at`:** set to `2026-06-08T02:14:33Z` — single pre-load timestamp, presents as `daily_batch / healthy`
   - FY2024/FY2025 `updated_at`: set to historical nightly batch dates per period
   - Schema created with full column descriptions and table labels (Section 2)
   - Partition by `DATE_TRUNC(posting_date, MONTH)`
3. **Create cadence views** `copa_fresh`, `copa_nightly`, `copa_stale` (timestamp overrides only)
4. **Generate and load `copa_baseline`** (FY2025 slice, 26,400 rows — identical to FY2025 portion of `copa_line_items`)
5. **Generate and load `copa_drifted`** (26,400 rows with four controlled perturbations):
   - C1: Replace `EXPORT_OEM` with `DIGITAL_NATIVE_OEM` in 5% of rows
   - C2: Redistribute `industry` values per drift profile
   - C3: Multiply FY2025 P12 `net_revenue` and related value fields by 2.4
   - C4: Redistribute `payment_terms` values per drift profile
6. **Register Supabase records** for `client_id = "meridian"`:
   - 1 data product (`meridian_copa`) — with `refresh_cadence = "daily_batch"`
   - 5 KPIs (net_revenue, cm_i_pct, cm_ii_pct, sales_deduction_rate, freight_cost_pct)
   - 4 business processes (revenue_management, product_profitability, customer_profitability, supply_chain_cost)
   - 2 principals (Sarah Mitchell CFO + James Okonkwo COO — `status="template"`, `email=None`)
   - 6 KPI accountability assignments (Section 10 Step 7)
7. **Write test fixture** `tests/fixtures/da_background_runs_seed.json` with realistic 20-dimension DA result for Scenario D
8. **Run validation queries** (Section 9 below) and assert all pass before exiting

### Python dependencies required
- `google-cloud-bigquery` — already in requirements.txt (lubricants)
- `numpy` — for controlled random distributions with fixed seed
- `faker` — for synthetic customer IDs (optional)

### Validation queries (run after load)
```sql
-- Verify row count
SELECT COUNT(*) FROM meridian_copa.copa_line_items;
-- Expected: 79,200 (2,200 rows × 12 periods × 3 years)

-- Verify dimension cardinalities
SELECT 'order_type' AS dim, COUNT(DISTINCT order_type) AS cardinality FROM meridian_copa.copa_line_items
UNION ALL
SELECT 'customer_group', COUNT(DISTINCT customer_group) FROM meridian_copa.copa_line_items
UNION ALL
SELECT 'industry', COUNT(DISTINCT industry) FROM meridian_copa.copa_line_items
UNION ALL
SELECT 'product_hierarchy_l1', COUNT(DISTINCT product_hierarchy_l1) FROM meridian_copa.copa_line_items
UNION ALL
SELECT 'distribution_channel', COUNT(DISTINCT distribution_channel) FROM meridian_copa.copa_line_items
UNION ALL
SELECT 'customer_id', COUNT(DISTINCT customer_id) FROM meridian_copa.copa_line_items;
-- Expected: order_type=4, customer_group=5, industry=7, product_hierarchy_l1=5, distribution_channel=4, customer_id≈820

-- Verify CM waterfall consistency (should return 0 rows)
SELECT COUNT(*) FROM meridian_copa.copa_line_items
WHERE ABS(cm_i - (net_revenue + standard_cogs)) > 0.01
   OR ABS(cm_ii - (cm_i + freight_cost + commission)) > 0.01;

-- Verify baseline concentration ratio for order_type (should be ~0.92)
SELECT
    SUM(CASE WHEN rnk <= 3 THEN revenue_share END) AS top3_concentration
FROM (
    SELECT order_type,
           SUM(net_revenue) / SUM(SUM(net_revenue)) OVER () AS revenue_share,
           RANK() OVER (ORDER BY SUM(net_revenue) DESC) AS rnk
    FROM meridian_copa.copa_line_items
    GROUP BY order_type
);
-- Expected: ~0.92 (CATALOG_STANDARD 42% + ENGINEERED_TO_ORDER 35% + AFTERMARKET_PARTS 15%)

-- Verify CM I is higher for AFTERMARKET_PARTS than CATALOG_STANDARD (validates primary ranking logic)
SELECT order_type,
       SAFE_DIVIDE(SUM(cm_i), SUM(net_revenue)) * 100 AS cm_i_pct
FROM meridian_copa.copa_line_items
GROUP BY order_type
ORDER BY cm_i_pct DESC;
-- Expected: AFTERMARKET_PARTS ~55%, ENGINEERED_TO_ORDER ~46%, SERVICE_CONTRACT ~40%, CATALOG_STANDARD ~32%

-- Verify baseline concentration ratio for customer_group
SELECT
    SUM(CASE WHEN rnk <= 3 THEN revenue_share END) AS top3_concentration
FROM (
    SELECT customer_group,
           SUM(net_revenue) / SUM(SUM(net_revenue)) OVER () AS revenue_share,
           RANK() OVER (ORDER BY SUM(net_revenue) DESC) AS rnk
    FROM meridian_copa.copa_line_items
    GROUP BY customer_group
);
-- Expected: ~0.83
```

---

## 10. Onboarding Discoverability Metadata

This section defines the additional metadata required to make `meridian_copa` fully testable via the 8-step Data Product Onboarding workflow and the Phase 12A KPI Template Generator.

### Step 1 — Schema Inspection (DPA `_profile_table_bigquery`)

The DPA profiler queries `INFORMATION_SCHEMA.COLUMN_FIELD_PATHS` and samples the table. With the column descriptions defined in Section 2, the profiler output should include:

**Expected profiler output (assertions for onboarding integration test):**

```python
profile = await dpa.inspect_schema(
    connection_profile=meridian_bq_profile,
    table="copa_line_items",
    dataset="meridian_copa"
)

# Correct column count (4 time/metadata + 21 analytical dimensions + 9 value fields = 34)
assert len(profile["columns"]) == 34

# Dimension columns identified (STRING type, not value fields)
dim_cols = [c for c in profile["columns"] if c["type"] == "STRING"]
assert len(dim_cols) == 16   # 15 original STRING dims + order_type (also STRING)

# Measure columns identified (NUMERIC type)
measure_cols = [c for c in profile["columns"] if c["type"] == "NUMERIC"]
assert len(measure_cols) == 9   # all 9 value fields

# Time columns identified
time_cols = [c for c in profile["columns"] if c["name"] in ("fiscal_year", "fiscal_period", "posting_date", "updated_at")]
assert len(time_cols) == 4

# Column descriptions present
# order_type is the primary profitability driver
order_type_col = next(c for c in profile["columns"] if c["name"] == "order_type")
assert "KEY MEASURE context dimension" in order_type_col["description"]
assert "23pp" in order_type_col["description"] or "CM I spread" in order_type_col["description"]

customer_group_col = next(c for c in profile["columns"] if c["name"] == "customer_group")
assert "KDGRP" in customer_group_col["description"]
assert "Primary segment profitability driver" in customer_group_col["description"]

# KEY MEASURE tag surfaced for value fields
cm_ii_col = next(c for c in profile["columns"] if c["name"] == "cm_ii")
assert "KEY MEASURE" in cm_ii_col["description"]

# High-cardinality warning present on customer_id
cust_id_col = next(c for c in profile["columns"] if c["name"] == "customer_id")
assert "exclude from GROUP BY" in cust_id_col["description"].lower()
```

### Step 2 — Time Dimension Mapping (Contract YAML generation)

The Time Dimension Mapping Wizard (Phase 12) auto-detects date columns. The column descriptions provide explicit hints:

| Column | Type | Expected Detection | Description hint |
|---|---|---|---|
| `fiscal_year` | INT64 | `fiscal_year_period` (primary) | "TimeDimension: fiscal_year_period" |
| `fiscal_period` | INT64 | `fiscal_year_period` (primary, pair) | "TimeDimension: fiscal_year_period — pair with fiscal_year" |
| `posting_date` | DATE | `date` (secondary) | "TimeDimension: date — secondary" |
| `updated_at` | TIMESTAMP | Excluded | "NOT an analytical dimension" |

The generated `TimeDimensionSpec` should match the contract definition in Section 8.

### Step 4 — KPI Registration (KPI Assistant)

The KPI Assistant receives the schema profile and suggests KPIs. With `KEY MEASURE` tags in the descriptions, it should suggest all five defined KPIs unprompted.

**Expected KPI Assistant suggestions (from schema alone):**

| Suggested KPI | Triggered by |
|---|---|
| Net Revenue | `net_revenue` column description: "Primary KPI numerator" + "KEY MEASURE" |
| Gross Margin % | `cm_i` ("KEY MEASURE") ÷ `net_revenue` ("KEY MEASURE") — margin ratio pattern |
| Net Contribution Margin % | `cm_ii` ("Primary segment profitability metric") ÷ `net_revenue` |
| Sales Deduction Rate | `sales_deductions` ÷ `gross_revenue` — deduction monitoring pattern |
| Freight Cost % | `freight_cost` ("KEY MEASURE for CM II analysis") ÷ `net_revenue` |

**Additional KPIs the assistant may suggest (valid but not pre-defined):**
- Volume Units trend (`volume_units` column)
- Average Selling Price (`net_revenue` ÷ `volume_units`)
- CM I per Unit (`cm_i` ÷ `volume_units`)

These are reasonable suggestions. The onboarding test should accept them without failing.

**Test assertion:**
```python
suggestions = await kpi_assistant.suggest(
    data_product_id="meridian_copa",
    client_id="meridian"
)
suggested_names = [s.name for s in suggestions.kpis]
assert "Net Revenue" in suggested_names
assert "Gross Margin %" in suggested_names or "CM I %" in suggested_names
assert "Net Contribution Margin %" in suggested_names or "CM II %" in suggested_names
assert len(suggestions.kpis) >= 5
```

### Step 5 — Business Process Mapping

Register the following business processes for `client_id = "meridian"` in the `business_processes` Supabase table. These are required for the accountability interview (Phase 11B) and org-first onboarding (Phase 12B):

```python
MERIDIAN_BUSINESS_PROCESSES = [
    BusinessProcess(
        id="revenue_management",
        client_id="meridian",
        name="Revenue & Pricing Management",
        description="Management of net revenue, pricing decisions, discount authority, and deduction policy across customer segments and channels.",
        owner_role="CFO",
        kpi_ids=["net_revenue", "sales_deduction_rate"]
    ),
    BusinessProcess(
        id="product_profitability",
        client_id="meridian",
        name="Product Portfolio Profitability",
        description="Gross margin management by product division and sub-category. Covers standard costing, product mix decisions, and new product introduction.",
        owner_role="CFO",
        kpi_ids=["cm_i_pct"]
    ),
    BusinessProcess(
        id="customer_profitability",
        client_id="meridian",
        name="Customer & Channel Profitability",
        description="Net contribution margin management by customer group, industry, and distribution channel. Includes freight allocation and commission policy.",
        owner_role="CFO",
        kpi_ids=["cm_ii_pct", "freight_cost_pct"]
    ),
    BusinessProcess(
        id="supply_chain_cost",
        client_id="meridian",
        name="Supply Chain & Logistics Cost",
        description="Outbound freight costs, plant efficiency, and logistics network optimisation. Shared accountability between Finance and Operations.",
        owner_role="COO",
        kpi_ids=["freight_cost_pct"]
    ),
]
```

### Step 6 — Principal Profiles

Two template principals for `client_id = "meridian"`. No email at seed time (`status = "template"`):

```python
MERIDIAN_PRINCIPALS = [
    PrincipalProfile(
        id="meridian_cfo",
        client_id="meridian",
        name="Sarah Mitchell",
        role="CFO",
        status="template",
        email=None,                          # entered by admin at promotion
        business_processes=["revenue_management", "product_profitability", "customer_profitability"],
        kpi_line_preference="summary",
        altitude="strategic",
    ),
    PrincipalProfile(
        id="meridian_coo",
        client_id="meridian",
        name="James Okonkwo",
        role="COO",
        status="template",
        email=None,
        business_processes=["supply_chain_cost"],
        kpi_line_preference="detail",
        altitude="operational",
    ),
]
```

### Step 7 — KPI Accountability Assignments

```python
MERIDIAN_ACCOUNTABILITY = [
    KPIAccountability(kpi_id="net_revenue",          client_id="meridian", principal_id="meridian_cfo", role="accountable"),
    KPIAccountability(kpi_id="cm_i_pct",             client_id="meridian", principal_id="meridian_cfo", role="accountable"),
    KPIAccountability(kpi_id="cm_ii_pct",            client_id="meridian", principal_id="meridian_cfo", role="accountable"),
    KPIAccountability(kpi_id="sales_deduction_rate", client_id="meridian", principal_id="meridian_cfo", role="accountable"),
    KPIAccountability(kpi_id="freight_cost_pct",     client_id="meridian", principal_id="meridian_cfo", role="accountable"),
    KPIAccountability(kpi_id="freight_cost_pct",     client_id="meridian", principal_id="meridian_coo", role="responsible"),
]
```

### Step 8 — QA (End-to-End Assessment Test)

Run a full enterprise assessment for `client_id = "meridian"` after seeding. Expected outcomes:

```bash
python run_enterprise_assessment.py --client meridian --dry-run
```

**Expected output:**
```
✓ Data product meridian_copa: pipeline_status=healthy, cadence=daily_batch
✓ KPIs evaluated: 5
✓ Situations detected: 3
  - cm_i_pct: WARNING (−2.6pp YoY, threshold −2pp)
  - cm_ii_pct: WARNING (−2.7pp YoY, threshold −1.5pp)
  - freight_cost_pct: WARNING (+0.7pp YoY, threshold +0.5pp)
✓ DA queued for background execution (scheduled mode, 21 dimensions — no cap)
✓ EDA profile loaded: order_type ranked #1, customer_group #2, product_hierarchy_l1 #3
✓ PIB: 2 principals with accountability — CFO (3 KPIs), COO (1 KPI)
```

### Phase 12A — KPI Template Generator Test

The Meridian company profile enables testing the Phase 12A KPI Template Generator end-to-end with a realistic company profile:

**Input:**
```json
{
    "company_name": "Meridian Flow Systems",
    "industry_hint": "industrial pump, valve, and flow control equipment manufacturer"
}
```

**Expected MA agent research findings:**
- Industry: Industrial Pumps & Flow Control Equipment (NAICS 333914)
- Peer companies: Xylem, Flowserve, IDEX Corporation, Roper Technologies (public comps for benchmarks)
- Key CFO metrics from proxy/10-K analogues: gross margin 35-47%, aftermarket revenue mix 30-45%, EBITDA margin 15-22%

**Expected generated KPI templates (minimum):**

| Template KPI | Benchmark Source | Should align with our KPI |
|---|---|---|
| Gross Margin % | Industry peers 35-47% | `cm_i_pct` ✓ |
| Net Revenue Growth | Industry peers 5-10% | `net_revenue` ✓ |
| Aftermarket Revenue Mix % | Xylem/Flowserve disclose 35-45% aftermarket | maps to `order_type=AFTERMARKET_PARTS` share |
| Freight Cost as % Revenue | Industry 3.5-5.5% range | `freight_cost_pct` ✓ |
| Backlog Book-to-Bill Ratio | ETO manufacturers disclose; proxy for order health | not pre-defined (valid addition) |

The test passes if `cm_i_pct`, `net_revenue`, and `freight_cost_pct` equivalents appear in the generated templates with benchmark ranges credible for the industrial equipment sector. The aftermarket mix suggestion is a bonus signal — the MA agent should surface it from Xylem/Flowserve disclosures without being prompted.

---

## 11. File Locations

```
scripts/
  clients/
    meridian.py                         # seed script (new)

tests/
  fixtures/
    da_background_runs_seed.json        # Scenario D pre-computed DA result (new)
  unit/
    test_phase_11k_cadence_sensing.py   # Phase 11K unit tests
    test_phase_11l_eda_profiling.py     # Phase 11L unit tests — asserts ranking
    test_phase_11m_change_detection.py  # Phase 11M unit tests — all 4 signal types
    test_phase_11n_da_state.py          # Phase 11N unit tests

docs/
  testing/
    copa_synthetic_data_spec.md         # this document
```

---

## 12. Demo Narrative

Once the data is seeded and Phases 11K–11N are built, the demo arc for a CFO prospect — a pump or industrial equipment manufacturer with SAP:

> **"Meridian Flow Systems — gross margin down 2.6pp, net contribution down 2.7pp in the first half of 2026. Revenue was up 8%. Something changed inside the numbers.**
>
> **Decision Studio ran overnight across all 21 dimensions of your SAP CO-PA data in BigQuery. Three situation cards fired this morning.**
>
> **The root cause isn't materials cost or pricing. It's order type mix. Your engineered-to-order projects slipped — customers pushed commissioning to Q3. That shifted 11 points of volume from engineered orders at 46% gross margin to catalog standard at 32% gross margin. Your factory ran the same products but earned 14pp less on every dollar of catalog revenue it substituted in. The P&L averaged it out and made it invisible.**
>
> **The PLANT_TEXAS ETO facility ran at 61% utilisation against a 78% target — fixed overhead absorbed across fewer units added another 1.2pp to the COGS pressure.**
>
> **Freight in the Northeast ran 0.7pp above prior year on utility site deliveries — catching the threshold.**
>
> **The system also flagged four early signals in your data: a new customer group — digital-native OEMs — appearing in your distribution mix for the first time. The water and wastewater utility concentration softening as one large framework contract drifts toward rebid. Patterns that haven't crossed thresholds yet but are moving in a direction your finance team would want to discuss before Q3 closes.**
>
> **Your CFO brief was in your inbox at 6:14am. Order type mix is on page one. The full 21-dimension analysis is in the accordion below."**

This narrative covers the full Phase 11K–11N value proposition:
- **11K:** Data product confirmed `daily_batch / healthy` — analysis ran on last night's extract, not stale data
- **11L:** All 21 dimensions profiled overnight; EDA ranked `order_type` as #1 driver (23pp CM I spread)
- **11M:** Background DA ran without the 5-dimension interactive cap; all 21 dimensions run in parallel via `asyncio.gather()`; change detection found 4 signals including the new DIGITAL_NATIVE_OEM customer group
- **11N:** PIB fired at 06:14 because top-3 IS dimension/key pairs changed materially from last run; CFO received the brief without requesting it

**Why pumps land with CFO audiences:** The order type story is not abstract. Every pump company CFO knows their ETO business earns more — but they cannot see it cleanly in their SAP P&L because it's blended with catalog volume. Decision Studio surfacing it in a named dimension with a 23pp spread is the moment the system earns credibility. The COO follow-up (PLANT_TEXAS utilisation) keeps Operations in the narrative.

The FY2026 full-year data ensures the "this morning" framing holds at any demo date throughout 2026 without requiring data refreshes.
