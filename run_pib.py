"""
Principal Intelligence Briefing (PIB) — CLI entry point.

Composes and sends the PIB email for a given principal + client,
drawing from the latest Situation Monitor run.

Usage:
    python run_pib.py --principal cfo_001 --client lubricants --email sarah@example.com
    python run_pib.py --principal cfo_001 --client lubricants --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


async def main(
    principal_id: str,
    client_id: str,
    email_to: str | None,
    dry_run: bool,
    format: str,
) -> int:
    from src.api.runtime import AgentRuntime
    from src.agents.models.pib_models import BriefingConfig, BriefingFormat
    from src.agents.new.a9_pib_agent import A9_PIB_Agent

    logger.info("Initializing runtime...")
    runtime = AgentRuntime()
    await runtime.initialize()
    orchestrator = runtime.get_orchestrator()

    pib_agent = await A9_PIB_Agent.create({"orchestrator": orchestrator})

    config = BriefingConfig(
        principal_id=principal_id,
        client_id=client_id,
        email_to=email_to,
        format=BriefingFormat(format),
        dry_run=dry_run,
    )

    briefing_run = await pib_agent.generate_and_send(config)
    logger.info(
        "PIB complete — status=%s new_situations=%d",
        briefing_run.status.value,
        briefing_run.new_situation_count,
    )
    return 0 if briefing_run.status.value in ("sent", "pending") else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Principal Intelligence Briefing — compose and send PIB email."
    )
    parser.add_argument("--principal", metavar="PRINCIPAL_ID", required=True)
    parser.add_argument("--client", metavar="CLIENT_ID", required=True)
    parser.add_argument("--email", metavar="EMAIL", default=None,
                        help="Override recipient email (uses principal profile email by default).")
    parser.add_argument("--format", choices=["detailed", "digest"], default="detailed")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Compose but do not send. Logs HTML preview length.")
    args = parser.parse_args()

    exit_code = asyncio.run(
        main(
            principal_id=args.principal,
            client_id=args.client,
            email_to=args.email,
            dry_run=args.dry_run,
            format=args.format,
        )
    )
    sys.exit(exit_code)
