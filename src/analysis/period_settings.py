"""A data product's period settings, and when a reading may raise a card (Phase 26, step 2).

The owner, 2026-10-15: "a corrective solution would require more than one month of evidence to
confirm a meaningful shift has occurred. So month level no. Quarter perhaps, yoy for sure." And:
"These are all tuning adjustments based on the clients business dynamics."

So which comparisons may raise a card, and how many complete months a card needs, are settings
on the data product, with the owner's view as the default. A comparison that may not raise a card
is still read and shown, as context.

Stored with no schema change:

  data product    metadata["period_settings"] = {"reading": ..., "card_comparisons": [...],
                                                 "min_card_months": 2}
  KPI             metadata["period_comparison"] = "<one of the ten>"   overrides the reading
  threshold row   "raises_card": true | false                          a per-KPI exception

Nothing applies these at run time yet; step 3 does.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Mapping, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from src.analysis.period_comparisons import (
    COMPARISONS, ComparisonSpans, Span, canonical, complete_months,
)

DEFAULT_READING = "ytd_vs_pytd"
DEFAULT_CARD_COMPARISONS = ("ytd_vs_pytd", "year_vs_prev_year")
DEFAULT_MIN_CARD_MONTHS = 2

_MONTH_TO_DATE = ("mtd_vs_prev_mtd", "mtd_vs_py_mtd")
_ONE_MONTH = _MONTH_TO_DATE + ("month_vs_prev_month", "month_vs_py_month")


def _one_of_the_ten(name: Any) -> str:
    c = canonical(name)
    if c not in COMPARISONS:
        raise ValueError(f"{name!r} is not a period comparison; expected one of {', '.join(COMPARISONS)}")
    return c


class PeriodSettings(BaseModel):
    """The settings in force for one KPI: its data product's, with the KPI's reading override."""

    reading: str = Field(DEFAULT_READING, description="The comparison a tile and a scan use unless asked for another.")
    card_comparisons: List[str] = Field(
        default_factory=lambda: list(DEFAULT_CARD_COMPARISONS),
        description="The comparisons whose threshold breach may raise a card.",
    )
    min_card_months: int = Field(
        DEFAULT_MIN_CARD_MONTHS, ge=1, le=12,
        description="Complete months the current span must hold before it may raise a card.",
    )

    @field_validator("reading", mode="before")
    @classmethod
    def _reading(cls, v: Any) -> str:
        return _one_of_the_ten(v)

    @field_validator("card_comparisons", mode="before")
    @classmethod
    def _cards(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v = [v]
        out: List[str] = []
        for name in v or []:
            c = _one_of_the_ten(name)
            if c not in out:
                out.append(c)
        return out

    @model_validator(mode="after")
    def _month_cards_need_a_one_month_floor(self) -> "PeriodSettings":
        # A month comparison holds one month. With a higher floor it could never raise a card,
        # which would look like a setting that works and does nothing.
        month_cards = [c for c in self.card_comparisons if c in _ONE_MONTH]
        if month_cards and self.min_card_months > 1:
            raise ValueError(
                f"{', '.join(month_cards)} hold one month, so they can raise a card only when "
                f"min_card_months is 1 (it is {self.min_card_months})"
            )
        return self


def settings_for(
    data_product_metadata: Optional[Mapping[str, Any]],
    kpi_metadata: Optional[Mapping[str, Any]] = None,
    period_keyed: Optional[bool] = None,
) -> PeriodSettings:
    """The settings for a KPI: defaults, then its data product's, then its own reading.

    Raises ValueError when a stored setting is not valid, so a mistake in the registry is
    seen, not quietly replaced by a default. With `period_keyed` True, month to date is refused:
    on period-keyed data it has no meaning (period_comparisons.available).
    """
    raw = dict((data_product_metadata or {}).get("period_settings") or {})
    override = (kpi_metadata or {}).get("period_comparison")
    if override:
        raw["reading"] = override
    settings = PeriodSettings(**raw)
    if period_keyed:
        bad = [c for c in [settings.reading, *settings.card_comparisons] if c in _MONTH_TO_DATE]
        if bad:
            raise ValueError(
                f"{', '.join(dict.fromkeys(bad))}: month to date has no meaning for data keyed by period"
            )
    return settings


@dataclass(frozen=True)
class CardDecision:
    may_raise: bool
    reason: str  # why not, in words a reader can use; empty when a card may be raised


def has_card_evidence(current: Span, settings: PeriodSettings, label: str = "This reading") -> CardDecision:
    """Enough complete months to support a card. Applies to every card a reading can raise,
    including actual against plan over the same span."""
    months = complete_months(current)
    if months < settings.min_card_months:
        held = "no complete month" if months == 0 else f"{months} complete month{'s' if months != 1 else ''}"
        return CardDecision(
            False,
            f"{label} holds {held} ({current.describe()}); a card needs "
            f"{settings.min_card_months}.",
        )
    return CardDecision(True, "")


def card_decision(
    spans: ComparisonSpans, settings: PeriodSettings, raises_card: Optional[bool] = None
) -> CardDecision:
    """Whether a breach on this comparison may raise a card.

    `raises_card` is the threshold row's own setting: None follows the data product. The
    evidence floor applies either way.
    """
    allowed = spans.comparison in settings.card_comparisons if raises_card is None else bool(raises_card)
    if not allowed:
        return CardDecision(False, f"{spans.label} is shown for context; it does not raise cards here.")
    return has_card_evidence(spans.current, settings, spans.label)
