"""A data product's period settings, and when a reading may raise a card (Phase 26).

Owner rulings (2026-10-15/17, decision record: docs/architecture/period_comparisons_decisions.md):

- Every data product is FINANCIAL or OPERATIONAL. Financial products are read on the year to date
  against the same months last year; operational products on the last 12 complete months against
  the 12 before. An unmarked data product is financial.
- A card needs at least two complete months. When a financial product's year so far holds fewer,
  it is read on the last 12 months instead (the February fallback), judged against its
  year-to-date targets.
- Quarter comparisons are a per-product option (same quarter last year); month comparisons never
  raise a card by default.
- The settings live on the data product only. No per-KPI exceptions.

Stored with no schema change, all optional beyond the kind:

  data product  metadata["period_settings"] = {"kind": "financial" | "operational",
                                               "reading": ..., "card_comparisons": [...],
                                               "min_card_months": 2}
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Literal, Mapping, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from src.analysis.period_comparisons import (
    COMPARISONS, ComparisonSpans, Span, canonical, complete_months,
)

KINDS = ("financial", "operational")
_KIND_DEFAULTS = {
    "financial": {"reading": "ytd_vs_pytd", "card_comparisons": ["ytd_vs_pytd"]},
    "operational": {"reading": "ltm_vs_prior_ltm", "card_comparisons": ["ltm_vs_prior_ltm"]},
}
DEFAULT_READING = _KIND_DEFAULTS["financial"]["reading"]
DEFAULT_CARD_COMPARISONS = tuple(_KIND_DEFAULTS["financial"]["card_comparisons"])
DEFAULT_MIN_CARD_MONTHS = 2
# The February fallback: what a financial year-to-date reading becomes while it holds too few
# complete months, and the threshold row the fallback is judged against.
FALLBACK_COMPARISON = "ltm_vs_prior_ltm"
FALLBACK_FROM = "ytd_vs_pytd"

_MONTH_TO_DATE = ("mtd_vs_prev_mtd", "mtd_vs_py_mtd")
_ONE_MONTH = _MONTH_TO_DATE + ("month_vs_prev_month", "month_vs_py_month")


def _named_comparison(name: Any) -> str:
    c = canonical(name)
    if c not in COMPARISONS:
        raise ValueError(f"{name!r} is not a period comparison; expected one of {', '.join(COMPARISONS)}")
    return c


class PeriodSettings(BaseModel):
    """A data product's settings, with its kind's defaults filled in."""

    kind: Literal["financial", "operational"] = Field("financial", description="Financial or operational data product.")
    reading: Optional[str] = Field(None, description="The comparison a tile and a scan use unless asked for another.")
    card_comparisons: Optional[List[str]] = Field(
        None, description="The comparisons whose threshold breach may raise a card.",
    )
    min_card_months: int = Field(
        DEFAULT_MIN_CARD_MONTHS, ge=1, le=12,
        description="Complete months the current span must hold before it may raise a card.",
    )

    @field_validator("reading", mode="before")
    @classmethod
    def _reading(cls, v: Any) -> Optional[str]:
        return None if v is None else _named_comparison(v)

    @field_validator("card_comparisons", mode="before")
    @classmethod
    def _cards(cls, v: Any) -> Optional[List[str]]:
        if v is None:
            return None
        if isinstance(v, str):
            v = [v]
        out: List[str] = []
        for name in v or []:
            c = _named_comparison(name)
            if c not in out:
                out.append(c)
        return out

    @model_validator(mode="after")
    def _defaults_and_consistency(self) -> "PeriodSettings":
        defaults = _KIND_DEFAULTS[self.kind]
        if self.reading is None:
            self.reading = defaults["reading"]
        if self.card_comparisons is None:
            self.card_comparisons = list(defaults["card_comparisons"])
        # A month comparison holds one month. With a higher floor it could never raise a card,
        # which would look like a setting that works and does nothing.
        month_cards = [c for c in self.card_comparisons if c in _ONE_MONTH]
        if month_cards and self.min_card_months > 1:
            raise ValueError(
                f"{', '.join(month_cards)} hold one month, so they can raise a card only when "
                f"min_card_months is 1 (it is {self.min_card_months})"
            )
        return self


def settings_for(data_product_metadata: Optional[Mapping[str, Any]], period_keyed: Optional[bool] = None) -> PeriodSettings:
    """A data product's settings. Raises ValueError when a stored setting is not valid, so a
    mistake in the registry is seen, not quietly replaced by a default. With `period_keyed` True,
    month to date is refused: on period-keyed data it has no meaning."""
    settings = PeriodSettings(**dict((data_product_metadata or {}).get("period_settings") or {}))
    if period_keyed:
        bad = [c for c in [settings.reading, *settings.card_comparisons] if c in _MONTH_TO_DATE]
        if bad:
            raise ValueError(
                f"{', '.join(dict.fromkeys(bad))}: month to date has no meaning for data keyed by period"
            )
    return settings


def fallback_comparison(settings: PeriodSettings, comparison: str, current: Span) -> Optional[str]:
    """The February fallback (owner ruling 2): a financial product's year-to-date reading holding
    fewer than the minimum complete months is read on the last 12 months instead. None otherwise."""
    if settings.kind == "financial" and comparison == FALLBACK_FROM and complete_months(current) < settings.min_card_months:
        return FALLBACK_COMPARISON
    return None


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
            f"{label} holds {held} ({current.describe()}); a card needs {settings.min_card_months}.",
        )
    return CardDecision(True, "")


def card_decision(spans: ComparisonSpans, settings: PeriodSettings, fallback_from: Optional[str] = None) -> CardDecision:
    """Whether a breach on this reading may raise a card. A February-fallback reading counts as
    the comparison it stands in for (`fallback_from`)."""
    counted_as = fallback_from or spans.comparison
    if counted_as not in settings.card_comparisons:
        return CardDecision(False, f"{spans.label} is shown for context; it does not raise cards here.")
    return has_card_evidence(spans.current, settings, spans.label)
