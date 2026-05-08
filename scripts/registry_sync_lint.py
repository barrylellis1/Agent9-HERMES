"""
Registry Sync Lint — pre-push hook.

Detects when scripts/clients/*.py files are being pushed and warns that
production Supabase registry data may be out of sync with the committed changes.

This is a WARNING only — non-blocking. It prints a reminder checklist and exits 0.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLIENT_DIR = REPO_ROOT / "scripts" / "clients"


def get_pushed_files() -> list[str]:
    """Get files that differ between local HEAD and the remote tracking branch."""
    try:
        # Files changed in commits about to be pushed (HEAD vs origin/master)
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/master...HEAD"],
            capture_output=True, text=True, cwd=REPO_ROOT
        )
        if result.returncode != 0:
            # Fallback: files changed in last commit
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                capture_output=True, text=True, cwd=REPO_ROOT
            )
        return result.stdout.strip().splitlines()
    except Exception:
        return []


def get_changed_clients(changed_files: list[str]) -> list[str]:
    """Return client IDs whose seed files changed."""
    clients = []
    for f in changed_files:
        path = Path(f)
        if path.parts[0:2] == ("scripts", "clients") and path.suffix == ".py" and path.stem != "__init__":
            clients.append(path.stem)
    return clients


def get_changed_migrations(changed_files: list[str]) -> list[str]:
    """Return migration files that changed."""
    return [f for f in changed_files if f.startswith("supabase/migrations/") and f.endswith(".sql")]


def main() -> int:
    changed_files = get_pushed_files()
    changed_clients = get_changed_clients(changed_files)
    changed_migrations = get_changed_migrations(changed_files)

    if not changed_clients and not changed_migrations:
        return 0  # Nothing registry-related changed

    print("\n" + "=" * 65)
    print("  REGISTRY SYNC REMINDER")
    print("=" * 65)

    if changed_clients:
        print(f"\n  Client seed file(s) changed: {', '.join(changed_clients)}")
        print("  Production Supabase registry data may be out of sync.\n")
        print("  Run after this push lands on Railway:")
        for client in changed_clients:
            print(f"    python scripts/onboard_client.py --client {client} --env production --dry-run")
            print(f"    python scripts/onboard_client.py --client {client} --env production")
        print()
        print("  Then verify:")
        print("    python scripts/verify_prod_registry.py --client " + " --client ".join(changed_clients))

    if changed_migrations:
        print(f"\n  Migration file(s) changed: {len(changed_migrations)} file(s)")
        print("  Apply to production Supabase if not already applied:")
        print("    supabase db push --linked")
        print("  Or apply manually via the Supabase dashboard SQL editor.")

    print("\n  This is a reminder only — push is NOT blocked.")
    print("=" * 65 + "\n")

    return 0  # Non-blocking


if __name__ == "__main__":
    sys.exit(main())
