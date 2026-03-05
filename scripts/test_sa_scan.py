"""
Quick test: call the Agent9 situations API directly and show the full result.
Mirrors exactly what the Decision Studio UI does for Rachel Kim / Lubricants / YTD.

Usage:
    python scripts/test_sa_scan.py
    python scripts/test_sa_scan.py --principal coo_001 --client lubricants --timeframe year_to_date
    python scripts/test_sa_scan.py --principal coo_001 --client lubricants --timeframe last_quarter
"""

import argparse
import json
import time
import sys
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000/api/v1/workflows"
POLL_INTERVAL = 1.5   # seconds between status checks
POLL_TIMEOUT  = 60    # seconds before giving up


def post_json(url: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req  = urllib.request.Request(url, data=data,
                                  headers={"Content-Type": "application/json"},
                                  method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser(description="Test Agent9 situation-awareness scan")
    parser.add_argument("--principal",  default="coo_001",      help="principal_id (default: coo_001 = Rachel Kim COO)")
    parser.add_argument("--client",     default="lubricants",   help="client_id    (default: lubricants)")
    parser.add_argument("--timeframe",  default="year_to_date", help="timeframe    (default: year_to_date)")
    parser.add_argument("--comparison", default="yoy",          help="comparison_type (default: yoy)")
    args = parser.parse_args()

    payload = {
        "principal_id":   args.principal,
        "client_id":      args.client,
        "timeframe":      args.timeframe,
        "comparison_type": args.comparison,
    }

    print("=" * 60)
    print("Agent9 Situation Awareness — API Test")
    print("=" * 60)
    print(f"  Principal : {args.principal}")
    print(f"  Client    : {args.client}")
    print(f"  Timeframe : {args.timeframe}")
    print(f"  Comparison: {args.comparison}")
    print()

    # ── 1. Submit scan ───────────────────────────────────────────
    print("POST /situations/run ...", end=" ", flush=True)
    try:
        submit = post_json(f"{BASE}/situations/run", payload)
    except urllib.error.URLError as e:
        print(f"\nERROR: Cannot reach backend at {BASE}")
        print(f"  {e}")
        sys.exit(1)

    request_id = submit.get("data", {}).get("request_id")
    if not request_id:
        print(f"\nUnexpected response:\n{json.dumps(submit, indent=2)}")
        sys.exit(1)
    print(f"accepted  (request_id: {request_id})")

    # ── 2. Poll for completion ────────────────────────────────────
    deadline = time.time() + POLL_TIMEOUT
    state    = "pending"
    result   = None

    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        status_resp = get_json(f"{BASE}/situations/{request_id}/status")
        record = status_resp.get("data", {})
        state  = record.get("state", "unknown")
        print(f"  state: {state}", flush=True)
        if state in ("completed", "failed"):
            result = record
            break

    print()

    # ── 3. Show result ────────────────────────────────────────────
    if state == "failed":
        print("SCAN FAILED")
        print(f"  Error: {result.get('error')}")
        sys.exit(1)

    if state != "completed":
        print(f"TIMED OUT after {POLL_TIMEOUT}s (last state: {state})")
        sys.exit(1)

    inner  = result.get("result", {}) or {}
    wrapper = inner.get("situations", {}) or {}

    # The response can be nested as situations.situations (list) or situations directly
    situations = (
        wrapper.get("situations")
        or (wrapper if isinstance(wrapper, list) else None)
        or inner.get("situations")
        or []
    )

    kpis_evaluated = wrapper.get("kpis_evaluated") or inner.get("kpis_evaluated") or 0
    error_msg      = wrapper.get("error") or inner.get("error")

    print(f"KPIs evaluated : {kpis_evaluated}")
    print(f"Situations found: {len(situations)}")
    if error_msg:
        print(f"Error in result : {error_msg}")
    print()

    if situations:
        print("-" * 60)
        for i, s in enumerate(situations, 1):
            print(f"[{i}] {s.get('title') or s.get('name') or 'Situation'}")
            print(f"    KPI      : {s.get('kpi_name') or s.get('kpi_id') or '?'}")
            print(f"    Severity : {s.get('severity') or '?'}")
            print(f"    Change   : {s.get('percent_change') or s.get('change') or '?'}")
            print(f"    Current  : {s.get('current_value') or '?'}")
            print(f"    Previous : {s.get('previous_value') or '?'}")
        print()
    else:
        print("No situations detected.")
        print()
        print("Full result payload (for debugging):")
        print(json.dumps(inner, indent=2, default=str))


if __name__ == "__main__":
    main()
