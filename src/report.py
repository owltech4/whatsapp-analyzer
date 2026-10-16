from __future__ import annotations
import pandas as pd

def build_markdown_report(
    file_name: str, message_count: int, participant_count: int,
    undated_count: int, ai_sections: list[str] | None = None,
) -> str:
    sections = [
        "# Relatório de análise de conversa", "",
        f"- Arquivo: {file_name}",
        f"- Mensagens reconhecidas: {message_count}",
        f"- Participantes: {participant_count}",
        f"- Mensagens sem data interpretada: {undated_count}", "",
        "## Limites",
        "As métricas descrevem o conteúdo exportado. Elas não determinam sentimentos, "
        "intenção, veracidade ou responsabilidade. A análise por IA, quando solicitada, "
        "usa apenas os trechos enviados e pode errar; confira as evidências no arquivo original.",
    ]
    if ai_sections:
        sections.extend(["", "## Análise assistida por IA"])
        for index, text in enumerate(ai_sections, 1):
            sections.extend(["", f"### Trecho {index}", "", text])
    return "\n".join(sections) + "\n"

def frame_to_csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8-sig")

