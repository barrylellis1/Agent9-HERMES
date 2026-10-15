"""Which option is recommended, and whether the analysis agreed.

The business's stated trade-off weights choose the recommended option (Stage J): the
option that ranks first on weighted impact, cost and risk. The model that wrote the
options also names the one it prefers, and writes the rationale. Until 2026-10-14 the two
were never compared, so a production briefing badged one option while its rationale argued
for another. The owner chose (2026-10-14) to keep the weights deciding, with the human
approving: the rationale is rewritten for the weighted choice, and a disagreement is shown
to the reader as an unresolved tension, not hidden.

A check (an option whose main action is a diagnostic, not an operational change) may be
offered but is never recommended on its own: when the weighted ranking puts one first, the
next option that is not a check is recommended. If every option is a check, the first one
stands.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _is_check(option: Any) -> bool:
    return bool(getattr(option, "is_check", False))


def choose(ranked: List[Any], model_pick_id: Optional[str]) -> Dict[str, Any]:
    """-> {"recommended", "score_top", "skipped_checks", "model_pick", "disagrees"}.

    `ranked` is the weighted ranking, best first. `model_pick_id` is the id the model named.
    `disagrees` is True when the model named a different, existing option.
    """
    if not ranked:
        return {"recommended": None, "score_top": None, "skipped_checks": [], "model_pick": None, "disagrees": False}
    recommended = next((o for o in ranked if not _is_check(o)), ranked[0])
    skipped = [o for o in ranked[: ranked.index(recommended)] if _is_check(o)]
    by_id = {str(getattr(o, "id", "")): o for o in ranked}
    model_pick = by_id.get(str(model_pick_id)) if model_pick_id else None
    disagrees = model_pick is not None and model_pick is not recommended
    return {
        "recommended": recommended,
        "score_top": ranked[0],
        "skipped_checks": skipped,
        "model_pick": model_pick,
        "disagrees": disagrees,
    }


def disagreement_tension(recommended: Any, model_pick: Any, check_skipped: bool = False) -> Dict[str, Any]:
    """The unresolved tension shown to the reader when the analysis preferred another option.

    The reason given must be the true one. When the weighted ranking put a check first and it
    was skipped, the recommendation is the highest-ranked option that acts, not "first on the
    weighting" (the first wording said so wrongly, seen in production 2026-10-15).
    """
    rec_title = str(getattr(recommended, "title", "") or "the recommended option")
    pick_title = str(getattr(model_pick, "title", "") or "another option")
    if check_skipped and _is_check(model_pick):
        reason = (
            f"The analysis favoured \"{pick_title}\", a check on the cause. A check is offered but not "
            f"recommended on its own, so \"{rec_title}\", the highest-ranked option that acts on the "
            f"business's stated weighting of impact, cost and risk, is the recommendation."
        )
    elif check_skipped:
        reason = (
            f"The analysis favoured \"{pick_title}\", but \"{rec_title}\" is the highest-ranked option "
            f"that acts on the business's stated weighting of impact, cost and risk (a check ranked above "
            f"it and is not recommended on its own), so it is the recommendation."
        )
    else:
        reason = (
            f"The analysis favoured \"{pick_title}\", but \"{rec_title}\" ranks first on the business's "
            f"stated weighting of impact, cost and risk, so it is the recommendation."
        )
    return {
        "tension": reason,
        "options_affected": [str(getattr(recommended, "id", "")), str(getattr(model_pick, "id", ""))],
        "requires": (
            f"Decision owner to confirm \"{rec_title}\" or choose \"{pick_title}\" instead at approval."
        ),
    }


def fallback_rationale(recommended: Any, check_skipped: bool = False) -> str:
    """Used when the rationale cannot be rewritten: never the draft that argued for another option."""
    title = str(getattr(recommended, "title", "") or "This option")
    rank = ("is the highest-ranked option that acts" if check_skipped else "ranks first")
    return (
        f"\"{title}\" {rank} on the business's stated weighting of impact, cost and risk. "
        f"See the options for its expected effect and the tensions below for what remains open."
    )
