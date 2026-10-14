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


def disagreement_tension(recommended: Any, model_pick: Any) -> Dict[str, Any]:
    """The unresolved tension shown to the reader when the analysis preferred another option."""
    rec_title = str(getattr(recommended, "title", "") or "the recommended option")
    pick_title = str(getattr(model_pick, "title", "") or "another option")
    return {
        "tension": (
            f"The analysis favoured \"{pick_title}\", but \"{rec_title}\" ranks first on the business's "
            f"stated weighting of impact, cost and risk, so it is the recommendation."
        ),
        "options_affected": [str(getattr(recommended, "id", "")), str(getattr(model_pick, "id", ""))],
        "requires": (
            f"Decision owner to confirm \"{rec_title}\" or choose \"{pick_title}\" instead at approval."
        ),
    }


def fallback_rationale(recommended: Any) -> str:
    """Used when the rationale cannot be rewritten: never the draft that argued for another option."""
    title = str(getattr(recommended, "title", "") or "This option")
    return (
        f"\"{title}\" ranks first on the business's stated weighting of impact, cost and risk. "
        f"See the options for its expected effect and the tensions below for what remains open."
    )
