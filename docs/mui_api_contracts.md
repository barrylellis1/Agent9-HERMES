# Agent9 Narrative UI – API Contract Draft

This document captures the REST contracts required in **Phase 1** to support the narrative-first Agent9 MUI experience. All endpoints follow REST conventions under `/api/v1/` and return JSON with standard error envelopes:

```json
{
  "status": "ok",
  "data": { ... }
}
```

Errors use HTTP status codes with body:

```json
{
  "status": "error",
  "error": {
    "code": "validation_error",
    "message": "Description",
    "details": {}
  }
}
```

## Shared considerations
- Authentication/authorization TBD (Phase 1 assumption: local dev usage; extendable).
- All write operations require `Content-Type: application/json`.
- `metadata` fields echo Agent9 models and allow arbitrary key/value extensions.
- Pagination (if needed) uses `page`, `page_size`, `next_cursor` query params; default page size 50.
- Example payloads below use bracketed placeholders (e.g., `<kpi_id>`, `<iso_timestamp>`). Replace with environment-specific values per registry content.

---

## 1. Registry CRUD APIs

### 1.1 KPI Registry (`/api/v1/registry/kpis`)
| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/v1/registry/kpis` | List KPIs (supports filters `domain`, `owner_role`, `tag`). |
| GET | `/api/v1/registry/kpis/{kpi_id}` | Retrieve KPI by `id`. |
| POST | `/api/v1/registry/kpis` | Create new KPI. |
| PUT | `/api/v1/registry/kpis/{kpi_id}` | Replace entire KPI. |
| PATCH | `/api/v1/registry/kpis/{kpi_id}` | Partial update (metadata, thresholds, etc.). |
| DELETE | `/api/v1/registry/kpis/{kpi_id}` | Remove KPI (logical delete – marked inactive). |

**KPI resource** mirrors `src/registry/models/kpi.py`.

```json
{
  "id": "<kpi_id>",
  "name": "<kpi_name>",
  "domain": "<domain>",
  "description": "<kpi_description>",
  "unit": "<unit>",
  "data_product_id": "<data_product_id>",
  "business_process_ids": ["<business_process_id>"]
  "sql_query": "SELECT ...",
  "thresholds": [
    {
      "comparison_type": "yoy",
      "green_threshold": 5.0,
      "yellow_threshold": 0.0,
      "red_threshold": -5.0,
      "inverse_logic": false
    }
  ],
  "dimensions": [
    {"name": "<dimension_name>", "field": "<field_name>", "values": ["<value_a>", "<value_b>"], "description": "<dimension_description>"}
  ],
  "tags": ["<tag>"],
  "owner_role": "<owner_role>",
  "stakeholder_roles": ["<stakeholder_role>"],
  "metadata": {"top_dimensions": "<comma_separated_dimensions>"}
}
```

### 1.2 Principal Profiles (`/api/v1/registry/principals`)
- Model: `PrincipalProfile` from `src/registry/models/principal.py`.
- Endpoints mirror KPI registry (GET collection/item, POST, PUT, PATCH, DELETE).
- Request bodies include nested `time_frame`, `communication` objects. Example:

```json
{
  "id": "<principal_id>",
  "name": "<principal_name>",
  "title": "<title>",
  "business_processes": ["<business_process_id>"]
  "kpis": ["<kpi_id>"]
  "responsibilities": ["<responsibility>"]
  "default_filters": {"region": ["ALL"]},
  "time_frame": {
    "default_period": "QTD",
    "historical_periods": 4,
    "forward_looking_periods": 2
  },
  "communication": {
    "detail_level": "high",
    "format_preference": ["text", "visual"],
    "emphasis": ["anomalies"]
  },
  "metadata": {}
}
```

### 1.3 Data Products (`/api/v1/registry/data-products`)
- Model: `DataProduct` (`src/registry/models/data_product.py`).
- Additional query params: `domain`, `tag`, `business_process_id`.
- `tables`/`views` fields support nested objects; `PUT` replaces entire structure while `PATCH` allows targeted updates (e.g., add `views.FI_Star_View`).

### 1.4 Business Processes (`/api/v1/registry/business-processes`)
- Model: `BusinessProcess` (`src/registry/models/business_process.py`).
- Useful filters: `domain`, `owner_role`, `tag`.

### 1.5 Business Glossary (`/api/v1/registry/glossary`)
- Data model: lightweight entries from YAML provider (term, definition, synonyms, related_kpis).
- Example entry:

```json
{
  "id": "<glossary_id>",
  "term": "<term>",
  "definition": "<definition>",
  "synonyms": ["<synonym>"]
  "related_kpis": ["<kpi_id>"]
  "metadata": {"last_reviewed": "<iso_date>"}
}
```

---

## 2. Workflow Trigger APIs

Workflow endpoints call orchestrated agents (see `src/api/main.py`). Each request returns a `request_id` and initial status; clients poll `/status` endpoints or receive WebSocket updates (Phase 1 fallback: polling).

### 2.1 Situation Awareness Workflow
- **POST** `/api/v1/workflows/situations/run`
  - **Body**:
    ```json
    {
      "principal_id": "<principal_id>",
      "filters": {"domain": "<domain>", "time_period": "<time_period>"},
      "kpi_ids": ["<kpi_id_a>", "<kpi_id_b>"],
      "include_annotations": true
    }
    ```
  - **Response**:
    ```json
    {
      "status": "ok",
      "data": {
        "request_id": "<situation_request_id>",
        "state": "pending"
      }
    }
    ```
- **GET** `/api/v1/workflows/situations/{request_id}/status`
  - Returns the stored workflow record. `data.state` reflects the lifecycle (`pending`, `completed`, `failed`) and the resolved payload is exposed under `data.result`:
    ```json
    {
      "status": "ok",
      "data": {
        "request_id": "<situation_request_id>",
        "workflow_type": "situations",
        "state": "completed",
        "result": {
          "situations": [
            {
              "situation_id": "<situation_id>",
              "kpi_id": "<kpi_id>",
              "delta": -3.7,
              "status": "yellow",
              "recognized_at": "<iso_timestamp>"
            }
          ]
        },
        "annotations": [],
        "error": null,
        "created_at": "<iso_timestamp>",
        "updated_at": "<iso_timestamp>"
      }
    }
    ```

### 2.2 Deep Analysis Workflow
- **POST** `/api/v1/workflows/deep-analysis/run`
  - Body includes context from Situation or manual request:
    ```json
    {
      "principal_id": "<principal_id>",
      "situation_id": "<situation_id>",
      "scope": {
        "kpi_id": "<kpi_id>",
        "time_range": {"start": "<iso_date>", "end": "<iso_date>"}
      },
      "hypotheses": ["<hypothesis>"]
      "include_supporting_evidence": true
    }
    ```
- **GET** `/api/v1/workflows/deep-analysis/{request_id}/status`
  - Follows the same envelope pattern. The execution output is stored at `data.result.execution` and the planned steps at `data.result.plan`:
    ```json
    {
      "status": "ok",
      "data": {
        "request_id": "<analysis_request_id>",
        "workflow_type": "deep_analysis",
        "state": "completed",
        "result": {
          "plan": {"kpi_name": "<kpi_id>", "dimensions": ["Customer"]},
          "execution": {
            "summary": "<analysis_summary>",
            "change_points": []
          }
        },
        "actions": [],
        "error": null
      }
    }
    ```

### 2.3 Solution Finder Workflow
- **POST** `/api/v1/workflows/solutions/run`
  - Body:
    ```json
    {
      "principal_id": "<principal_id>",
      "analysis_request_id": "<analysis_request_id>",
      "problem_statement": "<problem_statement>",
      "constraints": {
        "budget": "<constraint_budget>",
        "timeline": "<constraint_timeline>"
      }
    }
    ```
- **GET** `/api/v1/workflows/solutions/{request_id}/status`
  - Returns the workflow record with recommendation data under `data.result.solutions`:
    ```json
    {
      "status": "ok",
      "data": {
        "request_id": "<solution_request_id>",
        "workflow_type": "solutions",
        "state": "completed",
        "result": {
          "solutions": [
            {
              "solution_id": "<solution_id>",
              "title": "<solution_title>",
              "confidence": 0.78
            }
          ]
        },
        "actions": [
          {"action": "approve", "timestamp": "<iso_timestamp>"}
        ],
        "error": null
      }
    }
    ```

### 2.4 Action Endpoints
- Situations: `POST /api/v1/workflows/situations/{request_id}/annotations`
  - `{ "note": "Escalated to Deep Analysis." }`
- Deep Analysis feedback: `POST /api/v1/workflows/deep-analysis/{request_id}/actions/request-revision`
  - `{ "comment": "Include supplier breakdown by SKU." }`
- Solution approvals: `POST /api/v1/workflows/solutions/{request_id}/actions/approve`
  - `{ "solution_id": "sol-20251015-001", "comment": "Proceed with procurement." }`

---

## 3. Export & Evidence APIs (Optional Stretch)
- `GET /api/v1/export/analysis/{request_id}/report` → downloads Markdown/PDF summary.
- `GET /api/v1/export/solutions/{request_id}/decision-log` → structured audit.

---

## 4. Next Steps
1. Validate contracts with backend (ensure orchestrator adapters support inputs/outputs).
2. Generate OpenAPI spec (FastAPI routers) based on this draft.
3. Implement integration tests covering CRUD + workflows.
4. Keep this document updated as endpoints evolve.
