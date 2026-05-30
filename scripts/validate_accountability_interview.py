"""
validate_accountability_interview.py

End-to-end validation of the Phase 11B accountability interview pipeline.

Strategy: follow the agent's suggested responses to drive the conversation
forward naturally, then verify structural correctness and DB writes.
This mirrors realistic admin use: the agent leads, admin confirms.

Usage:
    python scripts/validate_accountability_interview.py [--base-url URL] [--dry-run]

    --dry-run   Run the interview but skip the confirm step (no DB writes)
    --base-url  Defaults to http://localhost:8000
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error

# Windows terminal may be cp1252; force UTF-8 for agent message output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://localhost:8000"
CLIENT_ID = "lubricants"

EXPECTED_PRINCIPALS = {"ceo_001", "cfo_001", "coo_001", "finance_001"}
EXPECTED_KPI_COUNT = 15
MAX_TURNS = 12


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _post(path: str, body: dict) -> dict:
    url = f"{BASE_URL}/api/v1{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        print(f"  HTTP {e.code} from {path}: {body_text[:400]}")
        raise


def _get(path: str) -> dict:
    url = f"{BASE_URL}/api/v1{path}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        print(f"  HTTP {e.code} from {path}: {body_text[:400]}")
        raise


# ── Assertion helpers ─────────────────────────────────────────────────────────

def _check(condition: bool, message: str) -> bool:
    if condition:
        print(f"  [OK]  {message}")
    else:
        print(f"  [FAIL] {message}")
    return condition


def _section(title: str):
    print(f"\n{'-' * 60}")
    print(f"  {title}")
    print(f"{'-' * 60}")


# ── Conversation driver ───────────────────────────────────────────────────────

def _pick_response(state: dict, turn: int) -> str:
    """
    Pick the next message to send. Uses the agent's first suggested response
    when available. Falls back to a generic acceptance per phase.
    """
    suggestions = state.get("suggested_responses", [])
    phase = state.get("phase", "process_suggestion")

    if suggestions:
        # Use first suggestion — typically the most accepting option
        return suggestions[0]

    # Fallbacks by phase when no suggestions returned
    if phase == "process_suggestion":
        return "Yes, confirm all proposed assignments for this principal."
    if phase == "gap_resolution":
        return "Assign all remaining KPIs to the CFO as accountable enterprise-wide."
    if phase == "review":
        return "Looks good, no conflicts to resolve."
    return "Please continue."


# ── Main validation ───────────────────────────────────────────────────────────

def run(dry_run: bool = False) -> bool:
    all_passed = True

    # ── Step 1: Start interview ───────────────────────────────────────────────
    _section("STEP 1 - Start interview")
    print(f"  POST /accountability/interview/start  client={CLIENT_ID}")
    resp = _post("/accountability/interview/start", {"client_id": CLIENT_ID})

    session_id = resp.get("session_id")
    all_passed &= _check(bool(session_id), "session_id returned")
    all_passed &= _check(resp.get("phase") == "process_suggestion", "phase = process_suggestion")
    all_passed &= _check(resp.get("coverage_pct", -1) == 0.0, "coverage starts at 0%")
    all_passed &= _check(len(resp.get("suggested_responses", [])) > 0, "opening has suggested responses")

    msg = resp.get("agent_message", "")
    all_passed &= _check(
        any(name in msg for name in ["David", "Sarah", "Rachel", "Marcus"]),
        "opening message names a principal",
    )
    print(f"\n  Opening snippet: {msg[:180].replace(chr(10), ' ')}")

    if not session_id:
        print("\n  Cannot continue without session_id — aborting.")
        return False

    # ── Step 2: Run interview turns until complete or max turns ──────────────
    _section("STEP 2 - Interview turns (agent-led)")
    current = resp
    turn = 0

    while not current.get("interview_complete") and turn < MAX_TURNS:
        turn += 1
        message = _pick_response(current, turn)
        phase = current.get("phase", "")
        proposals_before = len(current.get("proposed_assignments", []))

        print(f"\n  Turn {turn} [{phase}]: sending \"{message[:70]}{'...' if len(message) > 70 else ''}\"")
        time.sleep(1)

        current = _post("/accountability/interview/chat", {
            "session_id": session_id,
            "client_id": CLIENT_ID,
            "message": message,
        })

        n = len(current.get("proposed_assignments", []))
        coverage = round(current.get("coverage_pct", 0) * 100)
        new_phase = current.get("phase", "")
        agent_snippet = current.get("agent_message", "")[:100].replace(chr(10), " ")

        print(f"    proposals={n} (+{n - proposals_before})  coverage={coverage}%  phase={new_phase}")
        print(f"    agent: {agent_snippet}")

        all_passed &= _check(
            isinstance(current.get("proposed_assignments"), list),
            f"turn {turn}: proposed_assignments is a list",
        )

    if current.get("interview_complete"):
        print(f"\n  Interview completed in {turn} turns.")
    else:
        print(f"\n  Reached max turns ({MAX_TURNS}) — interview still in progress.")

    # ── Step 3: Structural checks on proposals ────────────────────────────────
    _section("STEP 3 - Validate proposed assignments")
    proposals = current.get("proposed_assignments", [])

    required_fields = {"kpi_id", "kpi_name", "principal_id", "principal_name", "role", "suggestion_source", "status"}
    malformed = [p for p in proposals if not required_fields.issubset(p.keys())]
    all_passed &= _check(not malformed, f"all {len(proposals)} proposals have required fields")
    all_passed &= _check(len(proposals) > 0, "at least one proposal generated")

    principals_in_proposals = {p["principal_id"] for p in proposals}
    all_passed &= _check(
        len(principals_in_proposals) > 1,
        f"proposals span multiple principals ({len(principals_in_proposals)} found: {sorted(principals_in_proposals)})",
    )

    roles = {p["role"] for p in proposals}
    all_passed &= _check(
        "accountable" in roles,
        "at least one accountable assignment proposed",
    )

    sources = {p["suggestion_source"] for p in proposals}
    process_sourced = [s for s in sources if s.startswith("process:")]
    all_passed &= _check(
        len(process_sourced) > 0,
        f"at least one process-derived suggestion (found: {sources})",
    )

    coverage_pct = round(current.get("coverage_pct", 0) * 100)
    all_passed &= _check(
        coverage_pct > 50,
        f"interview coverage > 50% (got {coverage_pct}%)",
    )

    # Print summary table
    confirmed = [p for p in proposals if p["status"] in ("confirmed", "modified")]
    rejected  = [p for p in proposals if p["status"] == "rejected"]
    print(f"\n  Total: {len(proposals)}  |  Confirmed/modified: {len(confirmed)}  |  Rejected: {len(rejected)}")
    for p in proposals:
        scope = f"{p['scope_dimension']}={p['scope_value']}" if p.get("scope_dimension") else "global"
        print(f"    [{p['status']:10}] {p['principal_name']:22} -> {p['kpi_name']:30} {scope}  [{p['role']}]")

    # ── Step 4: Confirm assignments ───────────────────────────────────────────
    _section("STEP 4 - Confirm assignments")

    # Treat all non-rejected proposals as approved for the seed
    to_approve = [p for p in proposals if p.get("status") != "rejected"]
    # Force status to "confirmed" so the endpoint writes them
    for p in to_approve:
        if p["status"] not in ("confirmed", "modified"):
            p["status"] = "confirmed"

    if dry_run:
        print(f"  DRY RUN - skipping confirm ({len(to_approve)} rows would be written)")
    else:
        print(f"  POST /accountability/interview/confirm  ({len(to_approve)} rows)")
        confirm_resp = _post("/accountability/interview/confirm", {
            "client_id": CLIENT_ID,
            "approved": to_approve,
        })
        rows_written = confirm_resp.get("rows_written", 0)
        all_passed &= _check(rows_written > 0, f"rows_written = {rows_written}")
        expected_writes = len([p for p in to_approve if p["status"] in ("confirmed", "modified")])
        all_passed &= _check(
            rows_written == expected_writes,
            f"rows_written ({rows_written}) == confirmed+modified count ({expected_writes})",
        )
        print(f"  Wrote {rows_written} rows to kpi_accountability table.")

    # ── Step 5: Coverage endpoint ─────────────────────────────────────────────
    _section("STEP 5 - Coverage endpoint")
    if dry_run:
        print("  DRY RUN - skipping coverage check (no rows written)")
    else:
        cov = _get(f"/accountability/coverage/{CLIENT_ID}")
        covered    = cov.get("covered_kpis", 0)
        total      = cov.get("total_kpis", 0)
        cov_pct    = cov.get("coverage_pct", 0)
        unassigned = cov.get("unassigned_kpis", [])
        conflicts  = cov.get("conflicts", [])

        print(f"  Covered: {covered}/{total}  ({round(cov_pct * 100)}%)")
        all_passed &= _check(total == EXPECTED_KPI_COUNT, f"total_kpis = {EXPECTED_KPI_COUNT} (got {total})")
        all_passed &= _check(covered > 0, f"covered_kpis > 0 (got {covered})")
        all_passed &= _check(cov_pct > 0.5, f"coverage > 50% (got {round(cov_pct * 100)}%)")

        if unassigned:
            print(f"  Unassigned ({len(unassigned)}): {[k['name'] for k in unassigned]}")
        if conflicts:
            print(f"  Conflicts ({len(conflicts)}): {conflicts}")

    # ── Result ────────────────────────────────────────────────────────────────
    _section("RESULT")
    if all_passed:
        print("  ALL CHECKS PASSED")
    else:
        print("  SOME CHECKS FAILED - review output above")
    return all_passed


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate accountability interview pipeline")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--dry-run", action="store_true", help="Skip confirm step (no DB writes)")
    args = parser.parse_args()

    BASE_URL = args.base_url

    try:
        _get("/registry/kpis?client_id=lubricants")
    except Exception as e:
        print(f"ERROR: Cannot reach backend at {BASE_URL} — {e}")
        sys.exit(1)

    passed = run(dry_run=args.dry_run)
    sys.exit(0 if passed else 1)
