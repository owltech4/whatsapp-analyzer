from __future__ import annotations
import hashlib
import re
import os
from pathlib import Path
import pandas as pd
import streamlit as st
from src.analyzer import analyze_conversation
from src.chunker import chunk_messages_with_overlap
from src.conflict_detector import detect_conflicts
from src.conflict_report import build_conflict_report, episode_label, render_episode_analysis, render_relationship_analysis
from src.episode_analyzer import analyze_episode
from src.llm_client import LLMError, configured
from src.document_loader import SUPPORTED_EXTENSIONS, load_document
from src.report import build_markdown_report, frame_to_csv
from src.relationship_analyzer import summarize_relationship
from src.statistics import activity_by_day, activity_by_hour, filter_by_date_range, messages_frame, participant_statistics, word_counts

def load_local_env() -> None:
    # Resolve relative to this file so Streamlit can be launched from any working directory.
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and (key not in os.environ or not os.environ[key].strip()):
            os.environ[key] = value

load_local_env()
st.set_page_config(page_title="Analisador de conversas e documentos", page_icon="💬", layout="wide")
st.title("💬 Analisador de conversas e documentos")
st.caption("Estatísticas e evidências são calculadas localmente. A análise por IA é opcional e só envia trechos ao provedor configurado quando você solicitar.")

@st.cache_data(show_spinner="Lendo e organizando a conversa...")
def cached_load_document(data: bytes, filename: str, use_day_first: bool):
    return load_document(data, filename, use_day_first)

with st.sidebar:
    st.header("Arquivo e opções")
    upload = st.file_uploader("Selecione uma conversa ou documento", type=sorted(ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS))
    day_first = st.toggle("Interpretar datas como dia/mês", value=True)
    include_system = st.toggle("Incluir eventos do sistema nas evidências", value=False)

if not upload:
    st.info("Envie um arquivo de conversa ou documento para começar.")
    st.markdown("Formatos aceitos: TXT, Markdown, CSV, JSON, HTML, PDF, DOCX, XLSX e PPTX. Exportações de conversa com data, hora e participante são reconhecidas; outros documentos são analisados como texto com referências às linhas extraídas.")
    st.stop()

upload_bytes = upload.getvalue()
try:
    messages, total_lines, source_format, is_chat = cached_load_document(upload_bytes, upload.name, day_first)
except Exception as exc:
    st.error(f"Não foi possível ler este arquivo: {exc}")
    st.stop()
if not messages:
    st.error("O arquivo foi aberto, mas não contém texto legível para analisar.")
    st.stop()

if not is_chat:
    st.info("Não encontrei uma estrutura de conversa com data e participante. Vou tratar o conteúdo como documento; estatísticas por pessoa e período podem não se aplicar.")

frame = messages_frame(messages)
human = frame[(~frame["sistema"]) & (frame["participante"] != "(sistema)")]
evidence_frame = frame if include_system else frame[~frame["sistema"]]
people = sorted(human["participante"].dropna().unique().tolist())
valid_dates = frame["data"].dropna()
undated_count = int(frame["data"].isna().sum())
first_date = valid_dates.min() if len(valid_dates) else None
last_date = valid_dates.max() if len(valid_dates) else None

if first_date is not None:
    min_day, max_day = first_date.date(), last_date.date()
    range_key = hashlib.sha256(upload_bytes).hexdigest()[:12]
    with st.sidebar:
        st.divider()
        st.subheader("Período da análise")
        period_start = st.date_input(
            "Início", value=min_day, min_value=min_day, max_value=max_day,
            key=f"period_start_{range_key}",
        )
        period_end = st.date_input(
            "Fim", value=max_day, min_value=min_day, max_value=max_day,
            key=f"period_end_{range_key}",
        )
    if period_start > period_end:
        st.sidebar.error("A data de início precisa ser anterior ou igual à data final.")
        st.stop()
    whole_period = period_start == min_day and period_end == max_day
    filtered_frame = filter_by_date_range(frame, period_start, period_end, include_undated=whole_period)
    period_id = f"{upload.name}:{upload.size}:{period_start}:{period_end}"
    if not whole_period and undated_count:
        st.sidebar.caption(f"{undated_count} mensagens sem data ficarão fora do período filtrado.")
else:
    period_start = period_end = None
    whole_period = True
    filtered_frame = frame.copy()
    period_id = f"{upload.name}:{upload.size}:all"

filtered_lines = set(filtered_frame["linha"])
filtered_messages = [m for m in messages if m.line in filtered_lines]
human = filtered_frame[(~filtered_frame["sistema"]) & (filtered_frame["participante"] != "(sistema)")]
period_people = sorted(human["participante"].dropna().unique().tolist())
evidence_frame = filtered_frame if include_system else filtered_frame[~filtered_frame["sistema"]]
period_undated = int(filtered_frame["data"].isna().sum())

st.subheader(upload.name)
if is_chat and period_start is not None:
    st.caption(f"Formato: {source_format.upper()} · Período exibido: {period_start:%d/%m/%Y} a {period_end:%d/%m/%Y}")
elif is_chat:
    st.caption(f"Formato: {source_format.upper()} · Conversa reconhecida, mas sem datas para filtrar")
else:
    st.caption(f"Formato: {source_format.upper()} · Documento sem datas de conversa reconhecidas")
a, b, c, d = st.columns(4)
a.metric("Mensagens no período" if is_chat else "Linhas de texto", f"{len(filtered_frame):,}".replace(",", "."))
b.metric("Participantes no período" if is_chat else "Formato", len(period_people) if is_chat else source_format.upper())
c.metric("Período", f"{first_date:%d/%m/%y} – {last_date:%d/%m/%y}" if is_chat and first_date is not None else "sem datas" if is_chat else "não aplicável")
d.metric("Mensagens sem data" if is_chat else "Linhas no arquivo", undated_count if is_chat else total_lines)
tabs = st.tabs(["Visão geral", "Participantes", "Ritmo", "Evidências", "Análise por IA", "Interações", "Relatório"])

with tabs[0]:
    if is_chat:
        st.markdown("### Atividade por participante")
        counts = human["participante"].value_counts().rename_axis("Participante").reset_index(name="Mensagens")
    else:
        counts = pd.DataFrame()
        st.info("Este arquivo foi lido como documento, sem participantes identificáveis; estatísticas de conversa não se aplicam.")
    if is_chat and not counts.empty:
        total_conversation_messages = max(1, int(((~frame["sistema"]) & (frame["participante"] != "(sistema)")).sum()))
        total_period_messages = max(1, int(counts["Mensagens"].sum()))
        counts["% da conversa"] = (counts["Mensagens"] / total_conversation_messages * 100).round(1)
        counts["% no período"] = (counts["Mensagens"] / total_period_messages * 100).round(1)
        left, right = st.columns(2)
        with left:
            st.markdown("#### Quantidade")
            st.bar_chart(counts.set_index("Participante")["Mensagens"])
        with right:
            st.markdown("#### Participação no período")
            st.bar_chart(counts.set_index("Participante")["% no período"])
        st.dataframe(counts, use_container_width=True, hide_index=True)
        st.caption("% da conversa usa todas as mensagens de participantes do arquivo como denominador. % no período reflete somente as datas selecionadas; avisos do sistema não entram nesses percentuais.")
    st.markdown("### Frequência de palavras")
    st.dataframe(pd.DataFrame(word_counts(filtered_messages).most_common(20), columns=["Palavra", "Ocorrências"]), use_container_width=True, hide_index=True)
    st.caption("Frequências ajudam a localizar temas; não demonstram intenção ou sentimento.")

with tabs[1]:
    if is_chat:
        stats = participant_statistics(filtered_frame)
        st.dataframe(stats, use_container_width=True, hide_index=True)
    else:
        st.info("O documento não contém participantes identificáveis.")

with tabs[2]:
    daily = activity_by_day(filtered_frame) if is_chat else pd.DataFrame()
    if not is_chat:
        st.info("O documento não contém datas de conversa reconhecidas para calcular ritmo.")
    elif not daily.empty:
        st.markdown("### Mensagens por dia")
        st.line_chart(daily)
        st.markdown("### Distribuição por hora")
        st.bar_chart(activity_by_hour(filtered_frame))
        ordered = human.dropna(subset=["data"]).sort_values("data")
        if len(ordered) > 1:
            gaps = ordered["data"].diff().dt.total_seconds().div(3600).dropna()
            st.metric("Intervalo mediano entre mensagens", f"{gaps.median():.1f} h")
    else:
        st.info("Não há datas reconhecidas para calcular ritmo.")

with tabs[3]:
    query = st.text_input("Busque uma palavra ou expressão")
    author = st.selectbox("Filtrar participante", ["Todos", *period_people], key="evidence_author")
    evidence = evidence_frame.copy()
    if author != "Todos":
        evidence = evidence[evidence["participante"] == author]
    if query.strip():
        evidence = evidence[evidence["mensagem"].str.contains(re.escape(query.strip()), case=False, na=False)]
    st.caption(f"{len(evidence)} trecho(s) encontrado(s); a linha indica a posição no arquivo de origem.")
    for _, row in evidence.head(300).iterrows():
        with st.container(border=True):
            date = row["data"].strftime("%d/%m/%Y %H:%M") if pd.notna(row["data"]) else "data não reconhecida"
            st.markdown(f"**{row['participante']}** · {date} · linha {row['linha']}")
            st.write(row["mensagem"])
    if len(evidence) > 300:
        st.warning("Exibindo os primeiros 300 resultados; refine a busca para ver menos trechos.")
    st.download_button("Baixar evidências filtradas em CSV", frame_to_csv(evidence), file_name="evidencias_arquivo.csv", mime="text/csv")

with tabs[4]:
    st.markdown("### Análise contextual assistida por IA")
    st.warning("Ao solicitar, o texto dos trechos selecionados será enviado ao provedor configurado na chave de API. Não envie conteúdo que não queira compartilhar com esse provedor.")
    if not configured():
        st.info("Análise por IA desativada. Confira a configuração do provedor de IA no arquivo .env.")
    chunks = st.slider("Quantidade de trechos amostrados", 1, 8, 4)
    if st.button("Solicitar análise por IA", disabled=not configured(), type="primary"):
        try:
            with st.spinner("Analisando amostras da conversa. No Ollama local, isso pode levar alguns minutos..."):
                sample_max_chars = int(os.getenv("OPENAI_CHUNK_MAX_CHARS", "12000"))
                st.session_state["ai_sections"] = analyze_conversation(
                    filtered_messages, max_chunks=chunks, max_chars=sample_max_chars
                )
                st.session_state["ai_period"] = period_id
        except LLMError as exc:
            st.error(str(exc))
    ai_sections = st.session_state.get("ai_sections", []) if st.session_state.get("ai_period") == period_id else []
    for index, section in enumerate(ai_sections, 1):
        st.markdown(f"#### Amostra {index}")
        st.markdown(section)
    if ai_sections and st.button("Limpar análise da sessão"):
        st.session_state.pop("ai_sections", None)
        st.session_state.pop("ai_period", None)
        st.rerun()

with tabs[5]:
    st.markdown("### Análise contextual de interações")
    st.caption("A IA examina o texto e o contexto cronológico. Não há pré-seleção por palavras-chave; a triagem pode ainda confundir tons ambíguos, por isso cada episódio vem com linhas e citações verificáveis.")
    detection_chunks = chunk_messages_with_overlap(filtered_messages)
    st.info(
        f"Período: {len(filtered_messages):,} mensagens em {len(detection_chunks)} blocos com sobreposição. "
        f"A detecção completa fará até {len(detection_chunks)} chamadas ao provedor.".replace(",", ".")
    )
    st.warning("Ao iniciar, o conteúdo do período selecionado será enviado ao provedor configurado. O custo depende do modelo e do tamanho do arquivo.")
    if not configured():
        st.info("Confira a configuração do provedor de IA no arquivo .env para habilitar a detecção contextual.")
    if st.button("Detectar episódios com IA", disabled=not configured() or not detection_chunks, type="primary"):
        progress = st.progress(0)
        status = st.empty()
        st.session_state.pop("detection_period", None)
        try:
            def update_progress(done: int, total: int) -> None:
                progress.progress(done / total)
                status.write(f"Analisando bloco {done} de {total}...")
            with st.spinner("A IA está examinando o período completo..."):
                episodes = detect_conflicts(filtered_messages, progress_callback=update_progress)
            st.session_state["detected_episodes"] = episodes
            st.session_state["detection_period"] = period_id
            st.session_state["conflict_analyses"] = {}
            st.session_state["conflict_period"] = period_id
            st.session_state.pop("relationship_result", None)
            st.session_state.pop("relationship_period", None)
        except LLMError as exc:
            st.error(str(exc))
    detection_ready = st.session_state.get("detection_period") == period_id
    episodes = st.session_state.get("detected_episodes", []) if detection_ready else []
    if detection_ready and not episodes:
        st.success("A IA não identificou episódios de conflito no período selecionado.")
    elif episodes:
        st.write(f"{len(episodes)} episódio(s) identificado(s) pela IA.")
        labels = [episode_label(ep) for ep in episodes]
        selected_label = st.selectbox("Escolha um episódio", labels)
        selected_episode = episodes[labels.index(selected_label)]
        st.markdown(build_conflict_report(selected_episode))
        with st.expander("Revisar mensagens e evidências do episódio"):
            for message in selected_episode.messages:
                timestamp = message.timestamp.strftime("%d/%m/%Y %H:%M") if message.timestamp else "data não reconhecida"
                st.markdown(f"**{message.author}** · {timestamp} · linha {message.line}")
                st.write(message.text)
            st.markdown("#### Citações usadas para identificar o episódio")
            for item in selected_episode.evidence:
                st.markdown(f"- Linha {item['line']}: “{item['quote']}” — {item.get('supports', '')} ✓")
        if st.button("Avaliar condutas deste episódio", disabled=not configured()):
            try:
                with st.spinner("Avaliando a sequência, as condutas e as evidências..."):
                    key = f"{period_id}:{selected_episode.first_line}"
                    st.session_state.setdefault("conflict_analyses", {})[key] = analyze_episode(selected_episode)
                    st.session_state["conflict_period"] = period_id
                    st.session_state.pop("relationship_result", None)
                    st.session_state.pop("relationship_period", None)
            except LLMError as exc:
                st.error(str(exc))
        conflict_map = st.session_state.get("conflict_analyses", {}) if st.session_state.get("conflict_period") == period_id else {}
        analysis = conflict_map.get(f"{period_id}:{selected_episode.first_line}")
        if analysis:
            st.markdown(render_episode_analysis(analysis))
        if conflict_map:
            st.divider()
            st.markdown("### Padrões entre os episódios avaliados")
            st.caption("A síntese usa somente episódios que você avaliou individualmente, no máximo os oito mais recentes.")
            if len(conflict_map) < 2:
                st.info("Avalie ao menos dois episódios para procurar padrões entre eles.")
            if st.button("Consolidar padrões com IA", disabled=not configured() or len(conflict_map) < 2):
                try:
                    with st.spinner("Comparando os episódios e validando as citações..."):
                        result = summarize_relationship(list(conflict_map.values())[-8:], filtered_messages)
                        st.session_state["relationship_result"] = result
                        st.session_state["relationship_period"] = period_id
                except LLMError as exc:
                    st.error(str(exc))
            if st.session_state.get("relationship_period") == period_id:
                st.markdown(render_relationship_analysis(st.session_state["relationship_result"]))

with tabs[6]:
    st.markdown("### Cobertura e limites")
    st.write(f"Linhas: {total_lines:,} · mensagens no período: {len(filtered_frame):,} · eventos do sistema: {int(filtered_frame['sistema'].sum()):,}".replace(",", "."))
    if period_undated:
        st.warning(f"{period_undated} mensagem(ns) sem data interpretada.")
    st.write("Mídias e mensagens ausentes não são avaliadas. Métricas e respostas de IA não estabelecem intenção, diagnóstico ou veracidade.")
    ai_sections = st.session_state.get("ai_sections", []) if st.session_state.get("ai_period") == period_id else []
    conflict_map = st.session_state.get("conflict_analyses", {}) if st.session_state.get("conflict_period") == period_id else {}
    all_sections = ai_sections + [
        f"Análise de conflito (linha {key.rsplit(':', 1)[-1]}):\n{render_episode_analysis(value)}"
        for key, value in conflict_map.items()
    ]
    if st.session_state.get("relationship_period") == period_id:
        all_sections.append(render_relationship_analysis(st.session_state["relationship_result"]))
    report = build_markdown_report(upload.name, len(filtered_frame), len(period_people), period_undated, all_sections)
    st.download_button("Baixar relatório em Markdown", report.encode("utf-8"), file_name="relatorio_arquivo.md", mime="text/markdown")

