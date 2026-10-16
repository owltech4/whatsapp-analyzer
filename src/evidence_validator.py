from __future__ import annotations
import re
import unicodedata
from typing import Any
from .parser import Message

def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFC", value).casefold()
    return re.sub(r"\s+", " ", value).strip()

def validate_evidence_items(
    items: Any, messages: list[Message]
) -> tuple[list[dict], list[dict]]:
    """Keep only line/quote pairs that match the extracted source text."""
    by_line = {message.line: message for message in messages}
    valid: list[dict] = []
    rejected: list[dict] = []
    if not isinstance(items, list):
        return valid, rejected
    for item in items:
        if not isinstance(item, dict):
            rejected.append({"reason": "evidence was not an object"})
            continue
        try:
            line = int(item.get("line"))
        except (TypeError, ValueError):
            rejected.append({"reason": "missing or invalid line number"})
            continue
        quote = str(item.get("quote", "")).strip()
        source = by_line.get(line)
        if source is None or not quote or _normalise(quote) not in _normalise(source.text):
            rejected.append({"line": line, "quote": quote, "reason": "quote or line did not match the source"})
            continue
        valid.append({**item, "line": line, "quote": quote, "verified": True})
    return valid, rejected

def validate_evidence_tree(value: Any, messages: list[Message]) -> tuple[Any, int, int]:
    """Recursively remove unverifiable evidence objects from structured results."""
    if isinstance(value, dict):
        if "line" in value and "quote" in value:
            valid, rejected = validate_evidence_items([value], messages)
            return (valid[0], 0, 1) if valid else (None, 1, 0)
        result = {}
        rejected_total = valid_total = 0
        for key, child in value.items():
            cleaned, rejected, valid = validate_evidence_tree(child, messages)
            result[key] = cleaned
            rejected_total += rejected
            valid_total += valid
        return result, rejected_total, valid_total
    if isinstance(value, list):
        cleaned_items = []
        rejected_total = valid_total = 0
        for child in value:
            cleaned, rejected, valid = validate_evidence_tree(child, messages)
            if cleaned is not None:
                cleaned_items.append(cleaned)
            rejected_total += rejected
            valid_total += valid
        return cleaned_items, rejected_total, valid_total
    return value, 0, 0
