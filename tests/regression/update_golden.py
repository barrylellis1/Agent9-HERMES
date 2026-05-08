"""
Capture golden baseline files for SA regression tests.

Run after any legitimate data change (new period loaded, threshold adjusted):

    python tests/regression/update_golden.py [--client lubricants] [--all]

With no arguments, updates all three clients.
Results are written to tests/regression/golden/<client_id>.json and should
be committed to the repo so future test runs compare against them.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Add project root to path so _sa_runner imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.regression._sa_runner import BASE_URL, CLIENTS, TIMEFRAME, COMPARISON_TYPE, run_sa_scan

GOLDEN_DIR = Path(__file__).parent / "golden"


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def capture(client_id: str) -> None:
    cfg = next((c for c in CLIENTS if c["client_id"] == client_id), None)
    if cfg is None:
        print(f"  ERROR: unknown client '{client_id}'. Options: {[c['client_id'] for c in CLIENTS]}")
        return

    print(f"  Scanning {client_id} ({cfg['backend']}, principal={cfg['principal_id']}) ...", flush=True)

    with httpx.Client(base_url=BASE_URL, timeout=180) as http:
        try:
            if cfg.get("warmup"):
                import time as _t
                print(f"  Warming up {cfg['backend']} warehouse ...", flush=True)
                run_sa_scan(http, cfg["client_id"], cfg["principal_id"])
                wait = cfg.get("warmup_wait", 40)
                print(f"  Waiting {wait}s for warehouse to be fully live ...", flush=True)
                _t.sleep(wait)
            result = run_sa_scan(http, cfg["client_id"], cfg["principal_id"])
        except Exception as exc:
            print(f"  FAILED: {exc}")
            return

    n_sit = len(result["situations"])
    n_opp = len(result["opportunities"])
    print(f"  -> {n_sit} situation(s), {n_opp} opportunity(ies)")

    golden = {
        "_meta": {
            "client_id":      client_id,
            "principal_id":   cfg["principal_id"],
            "backend":        cfg["backend"],
            "timeframe":      TIMEFRAME,
            "comparison_type": COMPARISON_TYPE,
            "captured_at":    datetime.now(timezone.utc).isoformat(),
            "git_commit":     _git_commit(),
            "situation_count":    n_sit,
            "opportunity_count":  n_opp,
        },
        "situations":    result["situations"],
        "opportunities": result["opportunities"],
    }

    out_path = GOLDEN_DIR / f"{client_id}.json"
    GOLDEN_DIR.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(golden, indent=2, default=str))
    print(f"  Saved -> {out_path.relative_to(Path(__file__).parent.parent.parent)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture SA golden baseline files")
    parser.add_argument("--client", help="Capture a single client by client_id")
    args = parser.parse_args()

    targets = [args.client] if args.client else [c["client_id"] for c in CLIENTS]

    print(f"\nCapturing SA golden baselines - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Server: {BASE_URL}")
    print(f"Clients: {targets}\n")

    for cid in targets:
        capture(cid)

    print("\nDone. Commit the updated golden/*.json files to lock in the new baseline.")


if __name__ == "__main__":
    main()
