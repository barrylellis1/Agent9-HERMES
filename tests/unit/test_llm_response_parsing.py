"""
Robust LLM JSON parsing + failure diagnostics (2026-08-06).

Motivated by a real defect: Solution Finder returned its hardcoded stub
("Tighten spend controls") in ~1 run in 6 under status="success". Two captured
failures showed the model's output was COMPLETE and well-formed at both ends
(27k+ chars, proper closing brace, inside a ```json fence, far under the token
budget) — yet json.loads rejected it, and the error was discarded so nobody
could say why.

These tests pin both halves of the fix: the repairs recover the invalid-JSON
patterns LLMs actually emit, and genuine failures now carry the decode error
plus surrounding text.
"""
from __future__ import annotations

import json

import pytest

from src.llm_services.response_parsing import parse_llm_json

VALID = {"options": [{"id": "opt_1", "title": "Do the thing"}], "recommendation": {"id": "opt_1"}}


class TestHappyPath:
    def test_plain_json(self):
        parsed, err = parse_llm_json(json.dumps(VALID))
        assert err is None and parsed["options"][0]["id"] == "opt_1"
        assert "_parse_repair" not in parsed, "clean input must not be marked as repaired"

    def test_json_code_fence(self):
        parsed, err = parse_llm_json("```json\n" + json.dumps(VALID) + "\n```")
        assert err is None and parsed["recommendation"]["id"] == "opt_1"

    def test_bare_code_fence(self):
        parsed, err = parse_llm_json("```\n" + json.dumps(VALID) + "\n```")
        assert err is None and parsed["options"]

    def test_fence_with_trailing_whitespace_after_close(self):
        parsed, err = parse_llm_json("```json\n" + json.dumps(VALID) + "\n```   \n\n")
        assert err is None and parsed["options"]


class TestRepairs:
    """Each repair targets a pattern LLMs actually produce on long documents."""

    def test_prose_before_and_after_json(self):
        text = "Here is the analysis you requested:\n" + json.dumps(VALID) + "\nLet me know if you need more."
        parsed, err = parse_llm_json(text)
        assert err is None
        assert parsed["options"][0]["title"] == "Do the thing"
        assert parsed["_parse_repair"] == "outermost_object"

    def test_trailing_comma_before_brace(self):
        parsed, err = parse_llm_json('{"a": 1, "b": [1, 2,], }')
        assert err is None and parsed["a"] == 1
        assert parsed["_parse_repair"] == "strip_trailing_commas"

    def test_raw_newline_inside_string(self):
        # A literal newline inside a quoted value — illegal JSON, common in
        # generated prose fields like `rationale`.
        parsed, err = parse_llm_json('{"rationale": "line one\nline two", "id": "x"}')
        assert err is None
        assert parsed["rationale"] == "line one\nline two"
        assert parsed["_parse_repair"] == "escape_control_chars"

    def test_repair_marker_records_which_repair_ran(self):
        parsed, _ = parse_llm_json("preamble " + json.dumps(VALID))
        assert parsed["_parse_repair"] == "outermost_object"

    def test_escaped_newline_already_valid_is_untouched(self):
        parsed, err = parse_llm_json('{"rationale": "line one\\nline two"}')
        assert err is None
        assert parsed["rationale"] == "line one\nline two"
        assert "_parse_repair" not in parsed


class TestDiagnosticsSurviveFailure:
    """The half that was missing entirely: an unparseable response must explain itself."""

    def test_genuine_failure_reports_position_and_context(self):
        broken = '{"options": [{"id": "opt_1", "impact": 18.5-26.3}]}'  # unquoted range
        parsed, err = parse_llm_json(broken)
        assert parsed is None
        assert err["error"] == "json_decode_failed"
        assert "msg" in err and isinstance(err["pos"], int)
        assert "lineno" in err and "colno" in err
        assert "18.5" in err["context"], "context window must show the offending text"

    def test_length_recorded_so_truncation_is_distinguishable(self):
        parsed, err = parse_llm_json("{" + '"a": 1,' * 200)  # long and broken
        assert parsed is None and err["length"] > 1000

    def test_empty_and_non_string_inputs(self):
        for bad in (None, "", 12345, [], {}):
            parsed, err = parse_llm_json(bad)
            assert parsed is None
            assert err["error"] in ("empty_or_non_string_response", "json_decode_failed")

    def test_non_dict_json_is_not_accepted(self):
        # A bare list parses as JSON but is not a valid analysis payload; callers
        # index it by key, so accepting it would fail later and less legibly.
        parsed, err = parse_llm_json("[1, 2, 3]")
        assert parsed is None and err is not None

    def test_prose_only_response_fails_cleanly(self):
        parsed, err = parse_llm_json("I cannot complete this request.")
        assert parsed is None and err["error"] in ("json_decode_failed",)


class TestRealisticSFShape:
    def test_large_fenced_document_with_prose_and_trailing_comma(self):
        """The shape of the observed failures: fenced, long, generated prose."""
        doc = {
            "problem_reframe": {"situation": "Gross Margin % declined", "complication": "base oil"},
            "options": [{"id": f"opt_{i}", "title": f"Option {i}",
                         "rationale": "Targets the confirmed COGS edge. " * 40} for i in (1, 2, 3)],
            "recommendation": {"id": "opt_1"},
            "moderator_grades": {"opt_1": {"constraint_survival": "pass"}},
        }
        text = "```json\n" + json.dumps(doc, indent=2) + "\n```"
        parsed, err = parse_llm_json(text)
        assert err is None
        assert len(parsed["options"]) == 3
        assert parsed["moderator_grades"]["opt_1"]["constraint_survival"] == "pass"

    def test_options_key_survives_repair(self):
        """The specific downstream condition: SF stubs when `options` is absent."""
        text = "Here you go:\n```json\n" + json.dumps(VALID) + "\n```\nHope that helps!"
        parsed, err = parse_llm_json(text)
        assert err is None and "options" in parsed
