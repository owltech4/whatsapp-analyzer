from __future__ import annotations
from .evidence_validator import validate_evidence_tree
from .llm_client import analyze_json
from .parser import Message

RELATIONSHIP_PROMPT = """Faça uma síntese transversal, em português, dos episódios individuais já analisados.
Retorne somente JSON com:
patterns: lista de {pattern, participants, evidence:[{line,quote,supports}], confidence};
changes_over_time: lista de {observation,evidence:[...]};
repair_and_reciprocity: lista de {observation,evidence:[...]};
alternative_readings: lista;
limits: lista.
Só chame algo de recorrente se houver evidência em mais de um episódio. Cite linhas e trechos exatos
já presentes no material; não invente nem parafraseie como se fosse citação. Diferencie observação de
interpretação, indique incerteza e limite a conclusão aos episódios fornecidos. Não conclua sobre
personalidade, diagnóstico, intenção interna ou a relação inteira."""

def summarize_relationship(
    analyses: list[dict], source_messages: list[Message]
) -> dict:
    text = "\n\n".join(
        f"EPISÓDIO {index}:\n{analysis}"
        for index, analysis in enumerate(analyses, 1)
    )
    result = analyze_json(text, RELATIONSHIP_PROMPT)
    cleaned, rejected, valid = validate_evidence_tree(result, source_messages)
    cleaned["evidence_validation"] = {
        "verified_quotes": valid,
        "rejected_quotes": rejected,
        "note": "Citações não verificadas foram removidas.",
    }
    return cleaned
