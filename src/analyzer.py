from __future__ import annotations
from .chunker import chunk_messages, render_chunk
from .llm_client import analyze_text
from .parser import Message

SYSTEM_PROMPT = """Responda sempre em português. Analise o material fornecido com cuidado e neutralidade; ele pode ser
uma conversa, transcrição ou documento. Entregue somente a resposta final, sem narrar seu processo,
sem rascunhos e sem explicar raciocínio. Seja conciso e organize a resposta em tipo de material, temas,
padrões observáveis, mudanças relevantes e dúvidas de contexto, quando aplicável. Diferencie fatos de
interpretações; cite linhas e autores somente se estiverem disponíveis. Não diagnostique pessoas, não
afirme intenção como fato e não invente contexto. Considere que o arquivo pode estar incompleto."""

def analyze_conversation(
    messages: list[Message], max_chunks: int = 4, max_chars: int = 12_000
) -> list[str]:
    all_chunks = chunk_messages(messages, max_chars=max_chars)
    if len(all_chunks) > max_chunks:
        indexes = sorted({
            round(i * (len(all_chunks) - 1) / max(1, max_chunks - 1))
            for i in range(max_chunks)
        })
        chunks = [all_chunks[index] for index in indexes]
    else:
        chunks = all_chunks
    results = []
    for index, chunk in enumerate(chunks, 1):
        task = (
            f"Analise este trecho ({index}/{len(chunks)}). Identifique o tipo de material; resuma "
            "temas, padrões observáveis, mudanças relevantes e dúvidas de contexto. Cite linhas e "
            "autores apenas se estiverem disponíveis. Não conclua sobre o material completo se recebeu "
            "apenas parte dele.\n\n" + render_chunk(chunk)
        )
        results.append(analyze_text(task, SYSTEM_PROMPT))
    return results

