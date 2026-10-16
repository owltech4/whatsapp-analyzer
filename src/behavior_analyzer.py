from __future__ import annotations
from .chunker import render_chunk
from .conflict_detector import ConflictEpisode
from .llm_client import analyze_text

BEHAVIOR_PROMPT = """Analise este episódio de conversa de forma equilibrada. Considere o contexto de todas as mensagens fornecidas.
Responda em português e organize em:
1. Sequência observável: quem parece iniciar o desacordo, escalada, reações e tentativas de reparação. Iniciar a conversa difícil não significa estar errado.
2. Avaliação separada por participante: sinais de desrespeito ou agressividade, contribuição para a escalada,
   abertura para ouvir/reparar e comportamento que ajudou ou dificultou a resolução.
3. Sentimentos e tom aparentes em cada etapa (por exemplo, frustração, raiva, tristeza ou carinho), sempre como leitura provável da linguagem, nunca como estado interno comprovado.
4. Coerência dos argumentos: aponte mudanças de versão ou contradições apenas quando duas mensagens específicas sustentarem essa leitura.
5. Para cada afirmação importante, cite a linha e o participante. Não invente citações; use apenas evidência presente.
6. Se usar notas de 0 a 10 para desrespeito, escalada ou disposição para resolver, rotule como estimativa subjetiva
   deste episódio e explique a evidência e a incerteza. Não trate a nota como medida científica.
7. Diga o que não é possível concluir, incluindo intenção interna, contexto fora do chat e quem está globalmente certo.
Evite diagnosticar pessoas. Distingua fato textual, interpretação e hipótese. Uma reação inadequada não apaga eventual provocação anterior."""

def analyze_episode(episode: ConflictEpisode) -> str:
    return analyze_text(render_chunk(episode.messages), BEHAVIOR_PROMPT)

def summarize_episodes(episode_analyses: list[str]) -> str:
    prompt = (
        "Faça um balanço comparativo, em português, apenas dos episódios analisados abaixo. "
        "Compare a contribuição observável de cada participante para iniciar ou escalar conflitos, "
        "sinais de desrespeito e tentativas de reparação. Aponte padrões recorrentes somente se "
        "aparecerem em mais de um episódio. Cite as linhas e evidências já fornecidas; não acrescente "
        "citações. Separe fatos, interpretações e hipóteses. Diga explicitamente que a conclusão é "
        "limitada aos episódios selecionados, não à conversa inteira ou à personalidade das pessoas."
    )
    evidence = "\n\n".join(
        f"EPISÓDIO ANALISADO {index}:\n{text}"
        for index, text in enumerate(episode_analyses, 1)
    )
    return analyze_text(evidence, prompt)

