from __future__ import annotations
import re
from collections import Counter
from datetime import date
import pandas as pd
from .parser import Message, is_system

STOPWORDS = set(
    "a ao aos aquela aquelas aquele aqueles aquilo as até com como da das de dela "
    "delas dele deles depois do dos e ela elas ele eles em entre era essa essas esse "
    "esses esta estas este estes eu foi foram há isso isto já lhe lhes mais mas me "
    "mesmo meu meus minha minhas muito na nas nem no nos nossa nossas nosso nossos "
    "num numa o os ou para pela pelas pelo pelos por porque quando que quem se sem "
    "ser seu seus sua suas também te tem temos ter teu teus tua tuas um uma umas uns "
    "você vocês vos".split()
)

def messages_frame(messages: list[Message]) -> pd.DataFrame:
    frame = pd.DataFrame([{
        "data": m.timestamp, "participante": m.author, "mensagem": m.text,
        "linha": m.line, "sistema": is_system(m),
    } for m in messages])
    frame["data"] = pd.to_datetime(frame["data"], errors="coerce")
    return frame

def word_counts(messages: list[Message]) -> Counter:
    words = re.findall(r"[\wÀ-ÿ']+", " ".join(m.text.lower() for m in messages if not is_system(m)))
    return Counter(w for w in words if len(w) > 2 and w not in STOPWORDS)

def participant_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    people = frame[(~frame["sistema"]) & (frame["participante"] != "(sistema)")]
    records = []
    for name, group in people.groupby("participante"):
        texts = group["mensagem"].fillna("")
        records.append({
            "Participante": name, "Mensagens": len(group),
            "Caracteres por mensagem (mediana)": int(texts.str.len().median()),
            "Perguntas (?)": int(texts.str.count(r"\?").sum()),
            "Mensagens com mídia": int(texts.str.contains(
                r"<mídia oculta>|<media omitted>", case=False, regex=True
            ).sum()),
            "Primeira mensagem": group["data"].min(), "Última mensagem": group["data"].max(),
        })
    return pd.DataFrame(records)

def activity_by_day(frame: pd.DataFrame) -> pd.DataFrame:
    dated = frame[(~frame["sistema"]) & frame["data"].notna()].copy()
    if dated.empty:
        return pd.DataFrame(columns=["Mensagens"])
    dated["dia"] = dated["data"].dt.date
    return dated.groupby("dia").size().rename("Mensagens").to_frame()

def activity_by_hour(frame: pd.DataFrame) -> pd.DataFrame:
    dated = frame[(~frame["sistema"]) & frame["data"].notna()].copy()
    if dated.empty:
        return pd.DataFrame({"Mensagens": []}, index=pd.Index([], name="hora"))
    dated["hora"] = dated["data"].dt.hour
    return dated.groupby("hora").size().reindex(range(24), fill_value=0).rename("Mensagens").to_frame()

def filter_by_date_range(
    frame: pd.DataFrame, start_date: date, end_date: date, include_undated: bool = False
) -> pd.DataFrame:
    dated = frame["data"].notna()
    in_range = dated & frame["data"].dt.date.between(start_date, end_date)
    if include_undated:
        in_range |= ~dated
    return frame[in_range].copy()

