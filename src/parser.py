from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Message:
    timestamp: Optional[datetime]
    author: str
    text: str
    line: int

# Includes the bracketed timestamp format used by the provided export.
HEADER = re.compile(
    r"^(?:\[)?(?P<date>\d{1,4}[./-]\d{1,2}[./-]\d{2,4}),?\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM|am|pm)?)"
    r"(?:\])?\s*(?:[-–]\s*)?(?P<body>.*)$"
)
SYSTEM_MARKERS = (
    "<mídia oculta>", "<media omitted>", "mensagem apagada",
    "this message was deleted", "alterou o assunto", "mudou o assunto",
    "criou o grupo", "adicionou", "saiu do grupo",
)

def decode_upload(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")

def parse_datetime(date_s: str, time_s: str, day_first: bool = True) -> Optional[datetime]:
    time_s = re.sub(r"\s+", " ", time_s.strip().upper())
    date_s = date_s.replace(".", "/").replace("-", "/")
    date_formats = ("%d/%m/%y", "%d/%m/%Y") if day_first else ("%m/%d/%y", "%m/%d/%Y")
    time_formats = ("%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p")
    for date_format in date_formats:
        for time_format in time_formats:
            try:
                return datetime.strptime(f"{date_s} {time_s}", f"{date_format} {time_format}")
            except ValueError:
                continue
    return None

def parse_chat(raw: str, day_first: bool = True) -> tuple[list[Message], int]:
    messages: list[Message] = []
    current: Optional[Message] = None
    lines = raw.splitlines()
    for line_no, line in enumerate(lines, 1):
        match = HEADER.match(line)
        if match:
            if current:
                messages.append(current)
            body = match.group("body")
            if ": " in body:
                author, text = body.split(": ", 1)
            else:
                author, text = "(sistema)", body
            current = Message(
                parse_datetime(match.group("date"), match.group("time"), day_first),
                author.strip(), text.strip(), line_no,
            )
        elif current:
            current.text += "\n" + line
    if current:
        messages.append(current)
    return messages, len(lines)

def is_system(message: Message) -> bool:
    text = message.text.lower()
    return message.author == "(sistema)" or any(marker in text for marker in SYSTEM_MARKERS)

