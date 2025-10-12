# Agent9 Shared Registries PRD

This document standardizes the role, structure, and precedence of the shared registries used across Agent9 agents. It ensures deterministic attribute resolution, avoids duplication, and enables CI validation.

## Goals
- Establish single sources of truth for business labels, synonyms, and KPI dimensionality.
- Define a clear precedence policy and runtime resolution behavior.
- Document schemas and expected locations for each registry.
- Provide validation checks to prevent drift across artifacts.

## In-Scope Registries
- Data Contract (Data Product contract for the FI star view)
- Business Glossary (terms + synonyms → technical labels)
- KPI Registry (KPI definitions + dimensions)
- Principal Registry (principal profiles + preferences)
- (Optional) Data Product Registry metadata used by providers

---

## 1) Data Contract
- Path: `src/contracts/fi_star_schema.yaml`
- View: `views[].name == "FI_Star_View"`
- Authoritative business-facing labels:
  - `views[*].llm_profile.exposed_columns`
- Canonical candidate dimensions for grouping:
  - `views[*].llm_profile.dimension_semantics`
- Also provides sample NL→SQL examples and base table/relationship metadata for schema binding.

### Contract Responsibilities
- Define only the exposed (public) columns that may be referenced by agents.
- Provide dimension semantics and (optionally) drill families (e.g., product/customer/profit center) through curated groupings.
- Avoid embedding synonyms; synonyms live in the Business Glossary.

---

## 2) Business Glossary
- Path: `src/registry/data/business_glossary.yaml`
- Provider: `src/registry/providers/business_glossary_provider.py`

### Glossary Responsibilities
- Canonical terms and their synonyms (e.g., Product, SKU, Item, Product Name).
- Technical mappings by system (here, `duckdb`) that must map to contract-exposed labels for the target view.
- No structural/relationship info; purely terminology and mapping.

### Glossary Constraints
- All `technical_mappings.duckdb` must point to labels that exist in the contract’s `exposed_columns` for the relevant view (e.g., `FI_Star_View`).
- Do not duplicate contract semantics (no data types, joins, etc.).

---

## 3) KPI Registry
- Path: `src/registry/kpi/kpi_registry.yaml`
- Provider: `src/registry/providers/kpi_provider.py` (by registry factory; implementation may vary)

### KPI Registry Responsibilities
- Defines KPIs (id, name, description, ownership, tags).
- May include default filters (e.g., Version = Actual for FI star), and suggested/allowed dimensions.
- Must refer to dimensions using either:
  - Contract-exposed labels directly, or
  - Terms that resolve via the Business Glossary to contract labels.

### KPI Registry Constraints
- Avoid ambiguous fields (e.g., lowercase snake_case names that do not match contract labels). Prefer the contract label (e.g., "Profit Center Name").
- Any dimension not matching an exposed label must resolve via the glossary.

#### Temporary KPI Enrichment (MVP)
- **Purpose**: Persist the “top most valuable dimensions” discovered via exploratory analysis without mutating the governed registry file.
- **Location**: Sidecar file at `src/registry/kpi/kpi_enrichment.yaml`.
- **Load/Merge Behavior**: On startup, `KPIProvider` (`src/registry/providers/kpi_provider.py`) loads the main registry `kpi_registry.yaml` and, if present, merges enrichment into each `KPI.metadata`.
  - Merged keys:
    - `metadata["top_dimensions"]` as a comma-separated string (e.g., `"Profit Center Name, Customer Type Name"`).
    - `metadata["dimension_scores"]` as a JSON string (mapping of dimension → score).

- **Computation**: `A9_Data_Governance_Agent.compute_and_persist_top_dimensions()` (`src/agents/new/a9_data_governance_agent.py`)
  - Uses `A9_Data_Product_Agent.generate_sql_for_kpi(..., breakdown=True, override_group_by=[dim])` to execute grouped aggregates for candidate dimensions (contract `dimension_semantics` + KPI-defined dimensions).
  - Scores each dimension by a simple “top-3 share” metric: `sum(top 3 groups) / sum(all groups)`.
  - Writes non-destructively to `kpi_enrichment.yaml`.

- **Schema (enrichment file)**
  ```yaml
  top_dimensions:
    <KPI Name>: "Dim A, Dim B, Dim C"
  dimension_scores:
    <KPI Name>: "{\"Dim A\": 0.62, \"Dim B\": 0.55}"
  ```

- **Environment Handling**
  - Sidecar enables env-specific results (dev/test/prod) without modifying the curated registry.
  - Teams may choose to promote stable values into the primary registry via a reviewed PR later.

- **Rationale**
  - Keeps the registry authoritative and human-curated, while allowing automated discovery to inform deep analysis.
  - Minimizes merge conflicts and governance churn in `kpi_registry.yaml`.

- **Deprecation / Promotion Path**
  - When enrichment results are validated and stable, promote into `kpi_registry.yaml` (e.g., under `KPI.metadata.top_dimensions`) via normal review.
  - The enrichment sidecar can then be regenerated periodically or retired if the registry embeds the final values.

- **Validation & Tests**
  - Ensure merged `top_dimensions` values correspond to contract-exposed labels or resolve via glossary.
  - Add unit tests to verify merge behavior and scoring logic.

---

## 4) Principal Registry
- Models: `src/registry/models/principal.py` (Pydantic)
- Provider: `src/registry/providers/principal_provider.py`
- YAML Sources (optional):
  - `src/registry/principal/principal_registry.yaml`
  - `src/registry/principal/principal_registry_simplified.yaml`

### Principal Registry Responsibilities
- Define principal profiles (e.g., CFO, Finance Manager) with:
  - `id`, `name`, `title`, `description`
  - `business_processes`: list of business process IDs (e.g., finance_revenue_growth_analysis)
  - `kpis`: KPI IDs monitored
  - `default_filters`: e.g., Version, Region, Product
  - `time_frame`: defaults (period, history/forward windows)
  - `communication`: preferences (detail level, formats, emphasis)
  - `metadata`: extensions

### Example (abbreviated)
```yaml
principals:
  - id: cfo_001
    name: CFO
    title: Chief Financial Officer
    business_processes: ["finance_revenue_growth_analysis", "finance_profitability_analysis"]
    kpis: ["gross_margin", "revenue_growth_rate"]
    default_filters:
      Version: ["Actual"]
    time_frame:
      default_period: QTD
      historical_periods: 4
      forward_looking_periods: 2
    communication:
      detail_level: high
      format_preference: ["visual", "text", "table"]
      emphasis: ["trends", "anomalies", "forecasts"]
```

### Principal Registry Constraints
- Keep business process and KPI references aligned with the KPI Registry.
- Default filters should be compatible with contract-exposed labels and DPA resolution.

---

## 5) Precedence & Resolution Policy (Authoritative Rules)

- **[P1 Contract (labels)]** Contract `exposed_columns` are authoritative per view. Agents should only project/filter on these labels.
- **[P2 Glossary (terms/synonyms)]** The glossary is authoritative for business terms/synonyms and must map to contract labels (by system: `duckdb`).
- **[P3 KPI Registry (dimensions)]** KPI dimensions must be either (a) direct contract labels or (b) terms resolvable via the glossary to contract labels.

### Runtime Resolution (Data Product Agent)
- Location: `src/agents/new/a9_data_product_agent.py` `A9_Data_Product_Agent._resolve_attribute_name()`
- Behavior:
  - If the incoming attribute exactly matches a contract-exposed label for the resolved view, return it unchanged (label-first short-circuit).
  - Otherwise, attempt glossary mapping (business term/synonym → contract label).
  - As a last resort, safe-quote the raw attribute.

---

## 6) Agent Responsibilities
- **Data Product Agent (DPA)**: Single source of SQL generation and attribute resolution. Honors precedence policy during `_resolve_attribute_name()`.
- **Deep Analysis Agent (DA)**: Enumerates dimensions from the contract (`dimension_semantics`), builds steps, executes via DPA, and populates KT outputs.
- **Data Governance Agent (optional)**: Resolves KPI → view name, if configured.
- **Principal Context Agent (optional)**: Loads principal profiles; provides default filters/timeframe/communication preferences.

All changes MUST comply with the Agent9 Agent Design Standards and the Code/Config Sync Rule.

---

## 7) Validation & CI (Drift Prevention)
- **[T1 Glossary→Contract]** For each glossary entry, `technical_mappings.duckdb` must exist in the resolved view’s `exposed_columns`.
- **[T2 KPI→Contract]** For each KPI dimension, assert it is (a) a contract label, or (b) a term that resolves via the glossary to a contract label.
- **[T3 DPA Resolution]** Unit tests for `_resolve_attribute_name()`:
  - Exact label remains unchanged (e.g., `"Product Name"`).
  - Term (e.g., `Product`) resolves to the correct label (e.g., `"Product Name"`).
- **[T4 Principal Defaults]** Principal default filters (e.g., `Version`) resolve to contract labels via DPA.

### Runtime governance validation (dev/test)
- Entrypoint: `A9_Data_Governance_Agent.validate_registry_integrity(view_name="FI_Star_View")`
- Returns: `{ success, issues, summary, view_name, label_count }`
- Use in development to quickly diagnose drift across Contract, Glossary, KPI, and Principal registries.

Integrate tests into pre-commit/CI to gate merges.

---

## 8) Change Management
- **Ownership**: Assign owners for Contract, Glossary, KPI Registry, Principal Registry.
- **Versioning**: Semantic contract/registry changes require a minor/major bump with migration notes.
- **Review Checklist**:
  - Adheres to precedence rules (P1–P3).
  - Passes validations (T1–T4).
  - Any agent behavior updates follow Agent9 standards and update cards/config models when necessary.

---

## 9) Examples & Conventions
- **Dimension naming**: Prefer human-readable labels (e.g., `"Product Name"`, `"Customer Type Name"`).
- **Glossary mapping**: Map generic terms (Product, SKU, Item) → `"Product Name"` (duckdb).
- **Drill families**: Represented implicitly by contract dimension groupings; used by DA for progressive drill planning when enabled.

---

## 10) Open Questions / Future Work
- Should we externalize drill path definitions (e.g., explicit hierarchy metadata) in the contract for richer exploration?
- Do we need a separate Data Product Registry file for view metadata beyond the contract?
- Add optional progressive drill config in DA (thresholds, top-k) and document it here when enabled.
