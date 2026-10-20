# arch-allow-direct-agent-construction
"""The briefing email shows the months behind each situation under its sentence (Phase 26,
owner ruling C), read from the situation the dashboard scan saved."""
from src.agents.models.pib_models import BriefingContent, SituationBriefingItem
from src.agents.new.a9_pib_agent import A9_PIB_Agent


def _content(months):
    return BriefingContent(
        principal_id="cfo_001", principal_name="Sarah Chen", principal_role="CFO",
        client_id="lubricants", client_name="Lubricants", assessment_run_id="run-1",
        new_situations=[SituationBriefingItem(
            situation_id="s1", kpi_assessment_id="a1", kpi_name="Gross Margin %", severity="critical",
            severity_score=0.9, description="Gross Margin % decreased by 4.5 points (13.0%), YTD vs PYTD",
            deviation_summary="", period_months=months,
        )],
    )


def test_the_months_follow_the_sentence():
    agent = A9_PIB_Agent.__new__(A9_PIB_Agent)
    html = agent._render_template(_content("Jan–Sep 2026 vs Jan–Sep 2025"))
    sentence = html.index("Gross Margin % decreased by 4.5 points (13.0%), YTD vs PYTD")
    assert html.index("Jan–Sep 2026 vs Jan–Sep 2025") > sentence
    text = agent._plain_text_fallback(_content("Jan–Sep 2026 vs Jan–Sep 2025"))
    assert "Jan–Sep 2026 vs Jan–Sep 2025" in text


def test_a_situation_from_an_older_scan_has_no_months_line():
    agent = A9_PIB_Agent.__new__(A9_PIB_Agent)
    assert "Jan–Sep" not in agent._render_template(_content(None))
