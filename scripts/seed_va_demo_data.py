"""
Seed the seven demo Value Assurance decisions from the warehouse's own values.

Run: .venv/Scripts/python scripts/seed_va_demo_data.py --dry-run
     .venv/Scripts/python scripts/seed_va_demo_data.py
     .venv/Scripts/python scripts/seed_va_demo_data.py --env production --dry-run
     .venv/Scripts/python scripts/seed_va_demo_data.py --env production

WHY IT WAS REWRITTEN (2026-10-15)
---------------------------------
The old seed hard-coded every number: baselines on the wrong scale (Gross Margin 45.2% against
~30% in the warehouse, Premium Mix 38% against ~13%), invented actual lines, and fixed verdicts.
No value was recorded at approval, so under the measurement rules introduced 2026-10-13 none of
them could be evaluated, yet production's Portfolio showed one validated, one partial and one
failed decision that were never measured.

WHAT IT DOES NOW
----------------
For each decision only the business content is fixed: what was decided, for which KPI, when,
how long its measurement window is, and the size of the expected effect as a share of the KPI's
value at approval. Everything else is measured or computed by the same code real decisions use:

1. The KPI's monthly values are read from the warehouse (closed months only).
2. The value recorded at approval is the last complete month before the approval date, and the
   No Action slope is the recent trend before it (`monthly_series.recent_trend_slope`).
3. The No Action and Solution lines are drawn by the agent's own `projection_lines()`.
4. Rows are upserted under fixed ids (so a re-run replaces them) with status MEASURING.
5. For each decision whose measurement window has closed, the target backend's evaluate
   endpoint is called. It reads the actual values from the warehouse and reaches the verdict
   from the three lines, exactly as for a real decision. The verdict is whatever the data says.

The three older decisions (January 2026) have closed windows and get real verdicts. The four
in-progress decisions are dated recently enough that their windows are genuinely still open.
"""
import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

import httpx

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

CLIENT_ID = "lubricants"
PRINCIPAL_ID = "cfo_001"
BACKENDS = {"local": "http://localhost:8000", "production": "https://agent9-hermes-production.up.railway.app"}

# Business content only. Expected effect is a share of the value at approval: the same
# ambition the original demo expressed, applied to the real value instead of an invented one.
DECISIONS = [
    {"id": "a0000001-0001-0001-0001-000000000001", "situation_id": "sit-gm-001", "kpi_id": "gross_margin_pct",
     "approved_at": "2026-10-06T14:00:00Z", "go_live_at": None, "window_days": 90, "phase": "APPROVED",
     "effect": (0.033, 0.071),
     "description": "Renegotiate base oil supply contracts with top 3 vendors to lock in next-quarter pricing before the seasonal spike. Consolidate orders across divisions for volume leverage."},
    {"id": "a0000001-0001-0001-0001-000000000002", "situation_id": "sit-rev-001", "kpi_id": "net_revenue",
     "approved_at": "2026-09-22T09:30:00Z", "go_live_at": None, "window_days": 120, "phase": "IMPLEMENTING",
     "effect": (0.069, 0.177),
     "description": "Launch premium synthetic product bundle for B2B direct accounts. Pilot with top 20 accounts offering 12-month contracts with volume-tiered pricing."},
    {"id": "a0000001-0001-0001-0001-000000000003", "situation_id": "sit-pmix-001", "kpi_id": "premium_mix_pct",
     "approved_at": "2026-08-18T11:00:00Z", "go_live_at": "2026-08-28T08:00:00Z", "window_days": 90, "phase": "LIVE",
     "effect": (0.13, 0.32),
     "description": "Reposition shelf space allocation in retail division to prioritize synthetic and premium-blend SKUs. Redeploy co-op marketing budget from conventional to premium products."},
    {"id": "a0000001-0001-0001-0001-000000000004", "situation_id": "sit-cogs-001", "kpi_id": "cogs",
     "approved_at": "2026-07-10T10:00:00Z", "go_live_at": "2026-07-20T08:00:00Z", "window_days": 120, "phase": "MEASURING",
     "effect": (0.022, 0.055),
     "description": "Consolidate distribution routes and renegotiate freight contracts. Implement just-in-time inventory for top 50 SKUs to reduce warehousing overhead."},
    {"id": "a0000001-0001-0001-0001-000000000005", "situation_id": "sit-ecom-001", "kpi_id": "ecommerce_revenue",
     "approved_at": "2026-01-15T09:00:00Z", "go_live_at": "2026-01-25T08:00:00Z", "window_days": 60, "phase": "COMPLETE",
     "effect": (0.267, 0.65),
     "description": "Launch direct-to-consumer e-commerce channel with subscription model for recurring oil change customers. Bundle with loyalty program and free shipping over threshold."},
    {"id": "a0000001-0001-0001-0001-000000000006", "situation_id": "sit-sga-001", "kpi_id": "sga_expense",
     "approved_at": "2026-01-20T10:00:00Z", "go_live_at": "2026-02-01T08:00:00Z", "window_days": 60, "phase": "COMPLETE",
     "effect": (0.032, 0.074),
     "description": "Rationalize trade show spending and redirect 40% of print advertising budget to digital demand-gen channels with measurable ROI attribution."},
    {"id": "a0000001-0001-0001-0001-000000000007", "situation_id": "sit-b2b-001", "kpi_id": "b2b_revenue",
     "approved_at": "2026-01-10T08:00:00Z", "go_live_at": "2026-01-20T08:00:00Z", "window_days": 60, "phase": "COMPLETE",
     "effect": (0.071, 0.17),
     "description": "Aggressive price matching program for B2B direct accounts to counter competitor undercutting. Offer retroactive rebates on Q1 volumes."},
]


def _load_env_file(path: str) -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ (stdlib only, existing values win)."""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except FileNotFoundError:
        pass


def _supabase(env: str):
    """Supabase REST base and headers for the target environment."""
    keys = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
    saved = {k: os.environ.pop(k, None) for k in keys}  # target env's values must win
    _load_env_file(str(_PROJECT_ROOT / (".env.production" if env == "production" else ".env")))
    base = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    for k, v in saved.items():
        if v is not None and not os.environ.get(k):
            os.environ[k] = v
    if not base or not key:
        sys.exit(f"ERROR: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set for {env}")
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    return base, headers


def _kpi_definition(base: str, headers: dict, kpi_id: str) -> dict:
    r = httpx.get(f"{base}/rest/v1/kpis", headers=headers,
                  params={"client_id": f"eq.{CLIENT_ID}", "id": f"eq.{kpi_id}", "select": "*"}, timeout=30)
    r.raise_for_status()
    rows = json.loads(r.content)
    if not rows:
        sys.exit(f"ERROR: KPI {kpi_id} not found for {CLIENT_ID}")
    return rows[0]


def _lower_is_better(kpi: dict) -> bool:
    th = kpi.get("thresholds")
    if isinstance(th, str):
        try:
            th = json.loads(th)
        except ValueError:
            th = None
    rows = th if isinstance(th, list) else []
    return any(isinstance(t, dict) and t.get("inverse_logic") is True for t in rows)


def _monthly_values(kpi: dict) -> list:
    """The KPI's closed monthly values from the warehouse, oldest first: [{period, value}]."""
    from google.cloud import bigquery
    from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
    from src.analysis.monthly_series import closed_months_only

    sa = A9_Situation_Awareness_Agent.__new__(A9_Situation_Awareness_Agent)
    sa.logger = __import__("logging").getLogger("seed")
    base_sql = kpi.get("sql_query") or kpi.get("calculation") or ""
    md = kpi.get("metadata") if isinstance(kpi.get("metadata"), dict) else {}
    sql = sa._bq_monthly_series_sql(base_sql, date_col=md.get("date_column", "transaction_date"), num_months=40)
    if not sql:
        sys.exit(f"ERROR: could not build a monthly series for {kpi.get('id')}")
    rows = [{"period": str(r[0]), "value": float(r[1])} for r in bigquery.Client().query(sql).result() if r[1] is not None]
    return closed_months_only(rows, keep=40)


def _build_row(d: dict, kpi: dict, months: list) -> dict:
    from src.agents.new.a9_value_assurance_agent import projection_lines
    from src.analysis.monthly_series import complete_months_before, recent_trend_slope

    approval_month = d["approved_at"][:7]
    before = complete_months_before(months, approval_month)
    if not before:
        sys.exit(f"ERROR: no complete month before {approval_month} for {d['kpi_id']}")
    period, baseline = before[-1]
    slope = recent_trend_slope(before) or 0.0
    lower_better = _lower_is_better(kpi)
    lo, hi = (round(abs(baseline) * f, 4) for f in d["effect"])
    inaction, expected, horizon = projection_lines(baseline, slope, d["window_days"], lo, hi, lower_better)
    snapshot = {
        "captured_at": d["approved_at"],
        "principal_role": "CFO",
        "data_product_id": kpi.get("data_product_id"),
        "key_assumptions": [],
        "strategic_rationale": None,
        "principal_priorities": ["Gross Margin", "Revenue Growth"],
        "business_context_name": CLIENT_ID,
        "business_process_domain": "finance",
        "kpi_threshold_at_approval": 0.0,
        "kpi_value_at_approval": baseline,
        "kpi_value_period": period,
        "kpi_lower_is_better": lower_better,
    }
    row = {
        "id": d["id"], "client_id": CLIENT_ID, "situation_id": d["situation_id"], "kpi_id": d["kpi_id"],
        "principal_id": PRINCIPAL_ID, "approved_at": d["approved_at"], "go_live_at": d["go_live_at"],
        "completed_at": None, "solution_description": d["description"],
        "expected_impact_lower": lo, "expected_impact_upper": hi, "measurement_window_days": d["window_days"],
        "status": "MEASURING", "phase": d["phase"],
        "inaction_trend": inaction, "expected_trend": expected, "inaction_horizon_months": horizon,
        "actual_trend": [baseline], "actual_trend_dates": [d["approved_at"]],
        "baseline_kpi_value": baseline, "pre_approval_slope": slope, "strategy_snapshot": snapshot,
    }
    return row


def _window_closed(d: dict, today: dt.date) -> bool:
    approved = dt.date.fromisoformat(d["approved_at"][:10])
    return (today - approved).days >= d["window_days"]


def main():
    p = argparse.ArgumentParser(description="Seed the demo VA decisions from warehouse values.")
    p.add_argument("--env", choices=["local", "production"], default="local")
    p.add_argument("--dry-run", action="store_true", help="Compute and print; write nothing")
    args = p.parse_args()

    _load_env_file(str(_PROJECT_ROOT / ".env"))  # warehouse credentials (BigQuery) come from the local .env
    base, headers = _supabase(args.env)
    backend = BACKENDS[args.env]
    today = dt.date.today()

    print(f"Target: {args.env} ({base}) | evaluate via {backend}")
    rows = []
    for d in DECISIONS:
        kpi = _kpi_definition(base, headers, d["kpi_id"])
        months = _monthly_values(kpi)
        row = _build_row(d, kpi, months)
        rows.append((d, row))
        snap = row["strategy_snapshot"]
        print(f"  {d['kpi_id']:18} approved {d['approved_at'][:10]} | value at approval {snap['kpi_value_at_approval']:,.2f} "
              f"({snap['kpi_value_period']}) | slope {row['pre_approval_slope']:,.2f}/month | expected "
              f"{row['expected_impact_lower']:,.2f} to {row['expected_impact_upper']:,.2f} | lower is better: "
              f"{snap['kpi_lower_is_better']} | window {'closed' if _window_closed(d, today) else 'open'}")
    if args.dry_run:
        print("DRY RUN: nothing written.")
        return

    if args.env == "production":
        print("WARNING: about to replace the seven demo decisions in PRODUCTION and evaluate the closed ones.")
        if input("  Type 'yes' to continue: ").strip().lower() != "yes":
            sys.exit("Aborted.")

    up = {**headers, "Prefer": "resolution=merge-duplicates,return=minimal"}
    with httpx.Client(timeout=60.0) as c:
        # Evaluations of the old rows describe numbers that no longer exist: remove them first.
        ids = ",".join(d["id"] for d in DECISIONS)
        r = c.delete(f"{base}/rest/v1/value_assurance_evaluations", headers=headers, params={"solution_id": f"in.({ids})"})
        print(f"  old evaluations removed: HTTP {r.status_code}")
        for d, row in rows:
            r = c.post(f"{base}/rest/v1/value_assurance_solutions", headers=up, json=row)
            print(f"  {'OK ' if r.status_code in (200, 201, 204) else 'ERR'} upsert {d['kpi_id']} {r.status_code} {r.text[:120]}")

        # Load the rows into the backend, then evaluate those whose window has closed.
        c.get(f"{backend}/api/v1/value-assurance/portfolio/{PRINCIPAL_ID}", params={"client_id": CLIENT_ID}).raise_for_status()
        for d, _row in rows:
            if not _window_closed(d, today):
                continue
            r = c.post(f"{backend}/api/v1/value-assurance/solutions/{d['id']}/evaluate", json={
                "request_id": f"seed-{d['id'][-4:]}", "principal_id": PRINCIPAL_ID, "solution_id": d["id"]}, timeout=180)
            body = json.loads(r.content) if r.content else {}
            ev = body.get("evaluation") or {}
            print(f"  evaluate {d['kpi_id']:18} -> HTTP {r.status_code} | verdict {ev.get('verdict') or body.get('detail')} "
                  f"| confidence {ev.get('confidence')} | counts toward ROI {ev.get('include_in_roi')}")
    print("Done.")


if __name__ == "__main__":
    main()
