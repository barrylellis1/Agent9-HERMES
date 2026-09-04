"""
Pydantic JSON Schema → OpenAI strict `json_schema` adapter.

OpenAI's structured-output `strict: true` mode guarantees the response matches
the schema, which is the whole point of using it: it removes the
truncation-mid-JSON and format-drift failure modes that prompt-based JSON plus
regex parsing suffers from. But strict mode accepts a narrower schema dialect
than `BaseModel.model_json_schema()` emits, so the schema must be adapted.

Constraints verified against the live API on 2026-09-04 (gpt-5.6-luna):

| Construct                                   | strict: true          |
|---------------------------------------------|-----------------------|
| property absent from `required`              | 400 — every key must be listed |
| optional as `anyOf: [T, {"type":"null"}]` **in** `required` | accepted |
| `additionalProperties: {<schema>}` (open dict) | 400 |
| `additionalProperties: false`                | required on every object |
| `$defs` / `$ref`                             | accepted |
| `default`, `title`                           | tolerated (ignored)   |

The open-dict case is the interesting one. `Dict[str, Model]` cannot be
expressed in strict mode at all, and dropping strictness for the whole schema
to accommodate one field would defeat the purpose — worse, in a model
comparison it would silently make OpenAI's output *unguaranteed* while
Anthropic's forced tool-use stays guaranteed, so any difference in schema
adherence would be an artifact of this adapter rather than of the models.

So open dicts are rewritten on the wire as an array of {key, value} pairs and
restored to dict shape after the response is parsed. Callers see the original
shape and never learn this happened.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple

# Marks an array-of-pairs that was an open dict on the way in.
_PAIR_KEY = "key"
_PAIR_VALUE = "value"


class UnsupportedSchemaError(ValueError):
    """Raised for schemas that cannot be represented in strict mode at all."""


def _is_open_dict(node: Dict[str, Any]) -> bool:
    """A `Dict[str, X]` — an object whose value schema is declared via
    additionalProperties rather than named properties."""
    return (
        node.get("type") == "object"
        and isinstance(node.get("additionalProperties"), dict)
        and not node.get("properties")
    )


def _pairs_array(value_schema: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "array",
        "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                _PAIR_KEY: {"type": "string"},
                _PAIR_VALUE: value_schema,
            },
            "required": [_PAIR_KEY, _PAIR_VALUE],
        },
    }


def _convert(node: Any) -> Any:
    """Structurally rewrite one schema node for strict mode."""
    if isinstance(node, list):
        return [_convert(n) for n in node]
    if not isinstance(node, dict):
        return node

    if _is_open_dict(node):
        return _pairs_array(_convert(node["additionalProperties"]))

    out: Dict[str, Any] = {}
    for k, v in node.items():
        # `default` is meaningless under strict (the model must emit every key)
        # and only adds noise to the wire payload.
        if k == "default":
            continue
        out[k] = _convert(v)

    if out.get("type") == "object" and isinstance(out.get("properties"), dict):
        out["additionalProperties"] = False
        props = out["properties"]
        required = list(out.get("required") or [])
        for name, sub in props.items():
            if name in required:
                continue
            # Strict mode demands every property be required. Preserve the
            # field's optionality by making it explicitly nullable instead.
            if not _accepts_null(sub):
                props[name] = {"anyOf": [sub, {"type": "null"}]}
            required.append(name)
        out["required"] = [n for n in props if n in set(required)]

    return out


def _accepts_null(sub: Dict[str, Any]) -> bool:
    if not isinstance(sub, dict):
        return False
    if sub.get("type") == "null":
        return True
    branches = sub.get("anyOf") or sub.get("oneOf") or []
    return any(isinstance(b, dict) and b.get("type") == "null" for b in branches)


def _open_dict_paths(schema: Dict[str, Any]) -> List[str]:
    """Data-space paths of every open dict, e.g. "cross_review" or
    "options[].lens_views". `$ref`s are resolved so a shared definition is
    reported at each place it is actually used."""
    defs = schema.get("$defs") or {}
    found: List[str] = []

    def walk(node: Any, path: str, seen: Tuple[str, ...]) -> None:
        if isinstance(node, list):
            for n in node:
                walk(n, path, seen)
            return
        if not isinstance(node, dict):
            return

        ref = node.get("$ref")
        if isinstance(ref, str):
            name = ref.rsplit("/", 1)[-1]
            if name in seen:
                raise UnsupportedSchemaError(
                    f"recursive schema definition {name!r} cannot be converted for "
                    f"OpenAI strict mode"
                )
            target = defs.get(name)
            if isinstance(target, dict):
                walk(target, path, seen + (name,))
            return

        if _is_open_dict(node):
            found.append(path)
            walk(node["additionalProperties"], f"{path}[].{_PAIR_VALUE}", seen)
            return

        for name, sub in (node.get("properties") or {}).items():
            walk(sub, f"{path}.{name}" if path else name, seen)
        if "items" in node:
            walk(node["items"], f"{path}[]", seen)
        for key in ("anyOf", "oneOf", "allOf"):
            for branch in node.get(key) or []:
                walk(branch, path, seen)

    walk(schema, "", ())
    return found


def to_openai_strict_schema(schema: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Adapt a Pydantic JSON schema for OpenAI `strict: true`.

    Returns `(wire_schema, open_dict_paths)`. Pass the paths to
    `restore_open_dicts()` on the parsed response to undo the pairs rewrite.

    Raises UnsupportedSchemaError for recursive schemas.
    """
    if not isinstance(schema, dict) or schema.get("type") != "object":
        raise UnsupportedSchemaError(
            "OpenAI strict mode requires an object at the schema root"
        )
    paths = _open_dict_paths(schema)  # before conversion, while open dicts exist
    return _convert(copy.deepcopy(schema)), paths


def restore_open_dicts(data: Any, paths: List[str]) -> Any:
    """Turn pairs-arrays back into dicts at each recorded path."""
    for path in sorted(paths, key=lambda p: p.count("[]")):
        data = _restore_one(data, [seg for seg in path.split(".") if seg])
    return data


def _restore_one(node: Any, segments: List[str]) -> Any:
    if node is None:
        return node
    if not segments:
        # Arrived at the pairs-array itself.
        if isinstance(node, list):
            out: Dict[str, Any] = {}
            for entry in node:
                if isinstance(entry, dict) and _PAIR_KEY in entry:
                    out[str(entry[_PAIR_KEY])] = entry.get(_PAIR_VALUE)
            return out
        return node

    head, rest = segments[0], segments[1:]
    if head.endswith("[]"):
        name = head[:-2]
        target = node.get(name) if isinstance(node, dict) else None
        if isinstance(target, list):
            node[name] = [_restore_one(item, rest) for item in target]
        return node
    if isinstance(node, dict) and head in node:
        node[head] = _restore_one(node[head], rest)
    return node
