"""
Robust parsing of JSON responses from LLMs, with diagnostics that survive failure.

WHY THIS EXISTS
---------------
Solution Finder was silently returning a hardcoded stub ("Tighten spend
controls") in roughly 1 run in 6, under `status="success"`, with no error
anywhere. Investigation of two captured failures (2026-08-06) showed the model's
output was **complete and well-formed**:

    head: ```json\\n{\\n  "problem_reframe": {...
    tail: ...\\n  }\\n}\\n```
    len:  27,529 chars / 21,175 output tokens — nowhere near the token budget

Not truncation. Not a refusal. The response parsed to `{"raw_response": ...}`,
the caller found no `options` key, and fell back to the stub.

The reason we could not say WHICH character `json.loads` rejected is that the
`JSONDecodeError` was caught and discarded. So this module does two things:

1. **Preserves the error.** Message, position, line/column, and a window of the
   surrounding text. A failure is now self-explaining rather than requiring a
   13-minute live run to reproduce.
2. **Attempts conservative repair** of the failure modes LLMs actually exhibit,
   in increasing order of intervention, stopping at the first success.

Repairs are deliberately narrow. Anything that could change the *meaning* of a
valid document is out of scope — a wrong answer that parses is worse than an
honest failure.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# A comma immediately before a closing brace/bracket. Legal in JavaScript, not in
# JSON, and a common LLM slip on long generated documents.
_TRAILING_COMMA = re.compile(r",(\s*[}\]])")

# Literal newlines/tabs inside a quoted string. JSON requires \n / \t escapes.
_CONTROL_IN_STRING = re.compile(r'(?<!\\)([\n\r\t])')


def _strip_code_fence(text: str) -> str:
    """Remove a leading ```json / ``` fence and its closing counterpart."""
    raw = text.strip()
    if not raw.startswith("```"):
        return raw
    raw = raw[raw.index("\n") + 1:] if "\n" in raw else raw
    if raw.rstrip().endswith("```"):
        raw = raw[: raw.rstrip().rfind("```")].rstrip()
    return raw


def _outermost_object(text: str) -> Optional[str]:
    """The substring from the first '{' to the last '}'.

    Handles the model prefacing its JSON with prose ("Here is the analysis:"),
    trailing commentary after the closing brace, or a code fence this parser did
    not recognise. Uses first/last rather than brace-counting on purpose: a
    counter walks into escaped braces inside strings and is easy to get subtly
    wrong, whereas first/last is exact whenever the document is a single object,
    which every prompt in this codebase asks for.
    """
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = text[start:end + 1]
    return candidate if candidate != text else None


def _escape_control_chars_in_strings(text: str) -> Optional[str]:
    """Escape raw newlines/tabs that appear inside quoted strings.

    Walks the document tracking whether we are inside a string literal, so
    formatting whitespace BETWEEN tokens is left alone and only characters that
    are actually illegal get escaped.
    """
    out, in_string, escaped, changed = [], False, False, False
    for ch in text:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\":
            out.append(ch)
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ch in "\n\r\t":
            out.append({"\n": "\\n", "\r": "\\r", "\t": "\\t"}[ch])
            changed = True
            continue
        out.append(ch)
    return "".join(out) if changed else None


def parse_llm_json(content: Optional[str]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Parse an LLM JSON response. Returns (parsed_dict, error_info).

    Exactly one of the two is non-None. Never raises — callers are on a response
    path where an exception would lose the model's work entirely.

    `error_info` carries the decode error plus the text around the offending
    position, which is what makes a failure diagnosable after the fact instead of
    needing an expensive live reproduction.
    """
    if not content or not isinstance(content, str):
        return None, {"error": "empty_or_non_string_response", "type": type(content).__name__}

    base = _strip_code_fence(content)

    # Ordered least-invasive first; stop at the first that parses.
    attempts = [("direct", base)]
    inner = _outermost_object(base)
    if inner:
        attempts.append(("outermost_object", inner))
    attempts.append(("strip_trailing_commas", _TRAILING_COMMA.sub(r"\1", inner or base)))
    escaped = _escape_control_chars_in_strings(inner or base)
    if escaped:
        attempts.append(("escape_control_chars", escaped))

    first_error: Optional[json.JSONDecodeError] = None
    first_text = base
    for method, candidate in attempts:
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as e:
            if first_error is None:
                first_error, first_text = e, candidate
            continue
        if not isinstance(parsed, dict):
            continue
        if method != "direct":
            # Worth surfacing: a repair working means the model emitted invalid
            # JSON, which is a prompt/model signal even though we recovered.
            logger.warning("[LLM-JSON] recovered via %s repair (len=%d)", method, len(candidate))
            parsed.setdefault("_parse_repair", method)
        return parsed, None

    err: Dict[str, Any] = {"error": "json_decode_failed", "length": len(base)}
    if first_error is not None:
        pos = first_error.pos
        err.update({
            "msg": first_error.msg,
            "pos": pos,
            "lineno": first_error.lineno,
            "colno": first_error.colno,
            # The actual bytes that broke it — the whole point of this module.
            "context": first_text[max(0, pos - 150):pos + 150],
        })
    logger.error("[LLM-JSON] unparseable after all repairs: %s", err.get("msg"))
    return None, err
