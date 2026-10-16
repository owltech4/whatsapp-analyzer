from __future__ import annotations
from typing import Any
from .conflict_detector import ConflictEpisode

def episode_label(episode: ConflictEpisode) -> str:
    start = episode.first_time.strftime("%d/%m/%Y %H:%M") if episode.first_time else "sem data"
    end = episode.last_time.strftime("%d/%m/%Y %H:%M") if episode.last_time else "sem data"
    return f"Episódio {episode.number} · {start}–{end} · linhas {episode.first_line}–{episode.last_line}"

def build_conflict_report(episode: ConflictEpisode) -> str:
    return (
        f"## {episode_label(episode)}\n\n"
        f"**Classificação:** {episode.classification} · **Confiança indicada pelo modelo:** {episode.confidence}\n\n"
        f"{episode.summary}\n\n"
        f"**Partes analisadas pela IA:** {len(episode.chunk_indices)} bloco(s), com sobreposição para reduzir cortes no meio de um episódio."
    )

def _evidence(items: list[dict]) -> str:
    if not isinstance(items, list):
        return ""
    return "\n".join(
        f"- Linha {item.get('line')}, «{item.get('quote')}» — {item.get('supports', '')}"
        for item in items if item.get("verified")
    )

def render_episode_analysis(result: dict[str, Any]) -> str:
    sections = ["### Leitura do episódio", str(result.get("summary", "Sem síntese."))]
    initiator = result.get("initiated_by")
    if initiator:
        sections.extend(["", f"**Quem introduziu o desacordo:** {initiator}"])
        if result.get("initiation_basis"):
            sections.append(str(result["initiation_basis"]))
        quotes = _evidence(result.get("initiation_basis_evidence", []))
        if quotes:
            sections.append(quotes)
    sequence = result.get("sequence", [])
    if sequence:
        sections.extend(["", "### Sequência e contexto"])
        for item in sequence:
            if not isinstance(item, dict):
                continue
            sections.append(f"- Linha {item.get('line', '?')}: {item.get('observation', '')}")
            if item.get("interpretation"):
                sections.append(f"  Interpretação possível: {item['interpretation']}")
            quotes = _evidence(item.get("evidence", []))
            if quotes:
                sections.append(quotes)
    participants = result.get("participants", [])
    if participants:
        sections.extend(["", "### Avaliação por participante"])
        for participant in participants:
            if not isinstance(participant, dict):
                continue
            sections.append(f"**{participant.get('name', 'Participante')}**")
            ratings = participant.get("ratings", {})
            if isinstance(ratings, dict):
                labels = {
                    "initiation": "Início", "provocation": "Provocação", "disrespect": "Desrespeito",
                    "escalation": "Escalada", "argumentation": "Argumentação",
                    "reciprocity": "Reciprocidade", "repair": "Reparação",
                }
                sections.append(" · ".join(
                    f"{labels.get(key, key)}: {value}/10" if value is not None
                    else f"{labels.get(key, key)}: sem base suficiente"
                    for key, value in ratings.items()
                ))
            actions = participant.get("actions", [])
            if not isinstance(actions, list):
                actions = []
            for action in actions:
                if isinstance(action, dict):
                    sections.append(f"- {action.get('observation', '')}")
                    quote_text = _evidence(action.get("evidence", []))
                    if quote_text:
                        sections.append(quote_text)
            if participant.get("confidence"):
                sections.append(f"Confiança: {participant['confidence']}")
    tones = result.get("emotional_tone", [])
    if tones:
        sections.extend(["", "### Tom emocional aparente"])
        for tone in tones:
            if isinstance(tone, dict):
                sections.append(f"- {tone.get('participant', 'Participante')}: {tone.get('tone', '')} ({tone.get('confidence', 'incerto')})")
                quote_text = _evidence(tone.get("evidence", []))
                if quote_text:
                    sections.append(quote_text)
    for heading, key in (
        ("Leituras alternativas", "alternative_interpretations"),
        ("Limites", "limits"),
    ):
        values = result.get(key, [])
        if values:
            sections.extend(["", f"### {heading}"])
            sections.extend(f"- {value}" for value in values)
    validation = result.get("evidence_validation", {})
    sections.extend([
        "", f"**Citações verificadas no arquivo:** {validation.get('verified_quotes', 0)} · "
        f"**citações rejeitadas:** {validation.get('rejected_quotes', 0)}."
    ])
    return "\n".join(sections)

def render_relationship_analysis(result: dict[str, Any]) -> str:
    sections = ["## Balanço dos episódios analisados"]
    for key, title in (
        ("patterns", "Padrões recorrentes"),
        ("changes_over_time", "Mudanças ao longo do tempo"),
        ("repair_and_reciprocity", "Reparação e reciprocidade"),
    ):
        entries = result.get(key, [])
        if entries:
            sections.extend(["", f"### {title}"])
            for item in entries:
                if isinstance(item, dict):
                    sections.append(f"- {item.get('pattern', item.get('observation', ''))}")
                    quotes = _evidence(item.get("evidence", []))
                    if quotes:
                        sections.append(quotes)
    for key, title in (("alternative_readings", "Leituras alternativas"), ("limits", "Limites")):
        entries = result.get(key, [])
        if entries:
            sections.extend(["", f"### {title}"])
            sections.extend(f"- {entry}" for entry in entries)
    validation = result.get("evidence_validation", {})
    sections.extend([
        "", f"**Citações verificadas no arquivo:** {validation.get('verified_quotes', 0)} · "
        f"**citações rejeitadas:** {validation.get('rejected_quotes', 0)}."
    ])
    return "\n".join(sections)
