"""
Unit tests for `src.llm_services.openai_schema`.

The adapter rewrites a Pydantic JSON schema into the narrower dialect OpenAI's
`strict: true` structured-output mode accepts. Every constraint asserted here
was verified against the live API on 2026-09-04 (gpt-5.6-luna) before being
encoded — these are not assumptions about the contract.

The open-dict round trip gets the most attention: it is the only transformation
that changes the shape of the data on the wire, so it is the only one that can
silently corrupt a caller's payload.
"""

import pytest

from src.llm_services.openai_schema import (
    UnsupportedSchemaError,
    restore_open_dicts,
    to_openai_strict_schema,
)


def _obj(props, required=None, **extra):
    d = {"type": "object", "properties": props}
    if required is not None:
        d["required"] = required
    d.update(extra)
    return d


class TestStrictConversion:
    def test_every_property_becomes_required(self):
        # Live API: "'required' is required to be supplied and to be an array
        # including every key in properties."
        out, _ = to_openai_strict_schema(
            _obj({"a": {"type": "string"}, "b": {"type": "string"}}, ["a"])
        )
        assert set(out["required"]) == {"a", "b"}

    def test_optional_property_becomes_nullable(self):
        # Optionality is preserved as anyOf[T, null] rather than lost.
        out, _ = to_openai_strict_schema(
            _obj({"a": {"type": "string"}, "b": {"type": "string"}}, ["a"])
        )
        assert out["properties"]["b"] == {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        }
        # An already-required property is left alone.
        assert out["properties"]["a"] == {"type": "string"}

    def test_already_nullable_property_is_not_double_wrapped(self):
        schema = _obj(
            {"a": {"anyOf": [{"type": "string"}, {"type": "null"}]}}, []
        )
        out, _ = to_openai_strict_schema(schema)
        assert out["properties"]["a"] == {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        }

    def test_additional_properties_false_added_to_every_object(self):
        schema = _obj(
            {"nested": _obj({"x": {"type": "string"}}, ["x"])}, ["nested"]
        )
        out, _ = to_openai_strict_schema(schema)
        assert out["additionalProperties"] is False
        assert out["properties"]["nested"]["additionalProperties"] is False

    def test_defaults_are_stripped(self):
        out, _ = to_openai_strict_schema(
            _obj({"a": {"type": "string", "default": "x"}}, ["a"])
        )
        assert "default" not in out["properties"]["a"]

    def test_defs_are_converted_too(self):
        schema = {
            "$defs": {"Item": _obj({"k": {"type": "string"}, "v": {"type": "string"}}, ["k"])},
            "type": "object",
            "properties": {"items": {"type": "array", "items": {"$ref": "#/$defs/Item"}}},
            "required": ["items"],
        }
        out, _ = to_openai_strict_schema(schema)
        item = out["$defs"]["Item"]
        assert item["additionalProperties"] is False
        assert set(item["required"]) == {"k", "v"}

    def test_non_object_root_rejected(self):
        with pytest.raises(UnsupportedSchemaError):
            to_openai_strict_schema({"type": "array", "items": {"type": "string"}})

    def test_recursive_schema_rejected_loudly(self):
        # Better to fail than to emit a schema that silently omits a branch.
        schema = {
            "$defs": {"Node": _obj({"child": {"$ref": "#/$defs/Node"}}, ["child"])},
            "type": "object",
            "properties": {"root": {"$ref": "#/$defs/Node"}},
            "required": ["root"],
        }
        with pytest.raises(UnsupportedSchemaError):
            to_openai_strict_schema(schema)


class TestOpenDictRewrite:
    def test_open_dict_becomes_pairs_array(self):
        # additionalProperties-as-schema is a 400 under strict mode.
        schema = _obj({"m": {"type": "object", "additionalProperties": {"type": "string"}}}, ["m"])
        out, paths = to_openai_strict_schema(schema)
        assert paths == ["m"]
        assert out["properties"]["m"]["type"] == "array"
        item = out["properties"]["m"]["items"]
        assert set(item["required"]) == {"key", "value"}
        assert item["properties"]["value"] == {"type": "string"}

    def test_round_trip_restores_original_shape(self):
        schema = _obj({"m": {"type": "object", "additionalProperties": {"type": "string"}}}, ["m"])
        _, paths = to_openai_strict_schema(schema)
        wire = {"m": [{"key": "a", "value": "1"}, {"key": "b", "value": "2"}]}
        assert restore_open_dicts(wire, paths) == {"m": {"a": "1", "b": "2"}}

    def test_round_trip_of_empty_dict(self):
        schema = _obj({"m": {"type": "object", "additionalProperties": {"type": "string"}}}, ["m"])
        _, paths = to_openai_strict_schema(schema)
        assert restore_open_dicts({"m": []}, paths) == {"m": {}}

    def test_open_dict_nested_in_array_items(self):
        schema = _obj(
            {
                "rows": {
                    "type": "array",
                    "items": _obj(
                        {"tags": {"type": "object", "additionalProperties": {"type": "string"}}},
                        ["tags"],
                    ),
                }
            },
            ["rows"],
        )
        _, paths = to_openai_strict_schema(schema)
        assert paths == ["rows[].tags"]
        data = {"rows": [{"tags": [{"key": "k", "value": "v"}]}, {"tags": []}]}
        assert restore_open_dicts(data, paths) == {
            "rows": [{"tags": {"k": "v"}}, {"tags": {}}]
        }

    def test_restore_tolerates_null_optional_dict(self):
        # cross_review is optional, so the model may legitimately emit null.
        schema = _obj({"m": {"type": "object", "additionalProperties": {"type": "string"}}}, [])
        _, paths = to_openai_strict_schema(schema)
        assert restore_open_dicts({"m": None}, paths) == {"m": None}

    def test_schema_without_open_dicts_reports_no_paths(self):
        _, paths = to_openai_strict_schema(_obj({"a": {"type": "string"}}, ["a"]))
        assert paths == []
        assert restore_open_dicts({"a": "x"}, paths) == {"a": "x"}


class TestRealSFSynthesisSchema:
    """The actual schema the Solution Finder passes for synthesis — the whole
    reason this adapter exists."""

    def test_sf_synthesis_schema_converts(self):
        from src.agents.models.solution_finder_models import SFSynthesisSchema

        out, paths = to_openai_strict_schema(SFSynthesisSchema.model_json_schema())

        # cross_review is Dict[str, CrossReviewEntry] — the one open dict.
        assert "cross_review" in paths

        def check(node, where="root"):
            if isinstance(node, dict):
                if node.get("type") == "object" and "properties" in node:
                    assert node.get("additionalProperties") is False, where
                    assert set(node["required"]) == set(node["properties"]), where
                for k, v in node.items():
                    check(v, f"{where}.{k}")
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    check(v, f"{where}[{i}]")

        check(out)

    def test_sf_cross_review_round_trips(self):
        from src.agents.models.solution_finder_models import SFSynthesisSchema

        _, paths = to_openai_strict_schema(SFSynthesisSchema.model_json_schema())
        wire = {
            "cross_review": [
                {"key": "analytical", "value": {"critiques": [], "endorsements": []}},
                {"key": "visionary", "value": {"critiques": [], "endorsements": []}},
            ]
        }
        restored = restore_open_dicts(wire, paths)
        assert set(restored["cross_review"]) == {"analytical", "visionary"}
        assert restored["cross_review"]["analytical"] == {
            "critiques": [],
            "endorsements": [],
        }
