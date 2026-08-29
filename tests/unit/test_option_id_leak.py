"""Tests for src.analysis.option_id_leak — the deterministic backstop for
internal option IDs (opt_1/opt_2/opt_3) leaking into reader-facing prose.

Real case found live 2026-08-24: decision_ask.decision_text rendered
"...diagnostic under opt_1." and immediate_actions[*].why_it_matters carried
the same leak twice more.
"""
from src.analysis.option_id_leak import find_option_id_leaks, as_audit_event


class TestFindOptionIdLeaks:
    def test_clean_fields_produce_no_findings(self):
        fields = {
            "decision_ask.decision_text": "Approve the pricing diagnostic.",
            "immediate_actions[0].why_it_matters": "Confirms the pricing hypothesis before spend.",
        }
        assert find_option_id_leaks(fields) == []

    def test_the_real_live_leak_is_caught(self):
        fields = {
            "decision_ask.decision_text": (
                "Approve immediate launch of the 30-day Base Oil & Additives "
                "cost-and-pricing diagnostic under opt_1."
            ),
        }
        findings = find_option_id_leaks(fields)
        assert len(findings) == 1
        assert findings[0]["field"] == "decision_ask.decision_text"
        assert findings[0]["ids_found"] == ["opt_1"]

    def test_multiple_ids_in_one_field_all_captured(self):
        fields = {
            "immediate_actions[1].why_it_matters": (
                "Resolves the tension between opt_1's pricing hypothesis and "
                "opt_2's structural cost hypothesis before resources are committed."
            ),
        }
        findings = find_option_id_leaks(fields)
        assert len(findings) == 1
        assert findings[0]["ids_found"] == ["opt_1", "opt_2"]

    def test_multiple_offending_fields_each_reported(self):
        fields = {
            "decision_ask.decision_text": "...under opt_1.",
            "immediate_actions[0].why_it_matters": "...opt_2's thesis.",
            "immediate_actions[0].action_text": "Clean text, no leak here.",
        }
        findings = find_option_id_leaks(fields)
        assert len(findings) == 2
        fields_flagged = {f["field"] for f in findings}
        assert fields_flagged == {"decision_ask.decision_text", "immediate_actions[0].why_it_matters"}

    def test_none_and_empty_values_are_skipped(self):
        fields = {"a": None, "b": "", "c": "opt_3 present"}
        findings = find_option_id_leaks(fields)
        assert len(findings) == 1
        assert findings[0]["field"] == "c"

    def test_does_not_false_positive_on_similar_words(self):
        # "option_1", "opt1" (no underscore before digit), "adopt_1" as a
        # substring of a longer identifier should not match \bopt_\d+\b —
        # opt_ must be a whole word boundary.
        fields = {"a": "See option_1 and opt1 for context."}
        assert find_option_id_leaks(fields) == []


class TestAsAuditEvent:
    def test_absent_when_clean(self):
        assert as_audit_event([]) is None

    def test_present_when_findings_exist(self):
        findings = [{"field": "x", "text": "opt_1", "ids_found": ["opt_1"]}]
        event = as_audit_event(findings)
        assert event is not None
        assert event["event"] == "option_id_leak"
        assert event["findings"] == findings
