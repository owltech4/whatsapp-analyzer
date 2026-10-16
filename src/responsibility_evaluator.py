from __future__ import annotations
from typing import Any
from .evidence_validator import validate_evidence_tree
from .parser import Message

CRITERIA = (
    "início do desacordo, provocação, desrespeito, escalada, argumentação, reciprocidade e reparação"
)

def validate_responsibility_result(
    result: dict[str, Any], messages: list[Message]
) -> dict[str, Any]:
    """Sanitize citations and normalize subjective ratings from an episode result."""
    cleaned, rejected, valid = validate_evidence_tree(result, messages)
    if not isinstance(cleaned, dict):
        cleaned = {}
    participants = cleaned.get("participants", [])
    if not isinstance(participants, list):
        participants = []
        cleaned["participants"] = participants
    for participant in participants:
        if not isinstance(participant, dict):
            continue
        ratings = participant.get("ratings")
        if not isinstance(ratings, dict):
            continue
        for dimension, score in list(ratings.items()):
            if score is None:
                continue
            try:
                ratings[dimension] = max(0, min(10, int(score)))
            except (TypeError, ValueError):
                ratings[dimension] = None
    cleaned["evidence_validation"] = {
        "verified_quotes": valid,
        "rejected_quotes": rejected,
        "note": "Citações não verificadas foram removidas.",
    }
    return cleaned
