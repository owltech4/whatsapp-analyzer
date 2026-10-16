from __future__ import annotations
from .parser import Message, is_system

def chunk_messages(
    messages: list[Message], max_chars: int = 12_000, include_system: bool = False
) -> list[list[Message]]:
    """Group messages while preserving timestamp, author, and source line."""
    chunks: list[list[Message]] = []
    current: list[Message] = []
    size = 0
    for message in messages:
        if not include_system and is_system(message):
            continue
        rendered_size = len(message.text) + len(message.author) + 40
        if current and size + rendered_size > max_chars:
            chunks.append(current)
            current, size = [], 0
        current.append(message)
        size += rendered_size
    if current:
        chunks.append(current)
    return chunks

def chunk_messages_with_overlap(
    messages: list[Message], max_chars: int = 28_000,
    overlap_messages: int = 8, include_system: bool = False,
) -> list[list[Message]]:
    """Split the full timeline into bounded chunks with message overlap."""
    source = [m for m in messages if include_system or not is_system(m)]
    chunks: list[list[Message]] = []
    start = 0
    while start < len(source):
        end = start
        size = 0
        while end < len(source):
            item_size = len(source[end].text) + len(source[end].author) + 48
            if end > start and size + item_size > max_chars:
                break
            size += item_size
            end += 1
        chunks.append(source[start:end])
        if end >= len(source):
            break
        start = max(start + 1, end - overlap_messages)
    return chunks

def render_chunk(messages: list[Message]) -> str:
    return "\n".join(
        f"[linha {m.line} | {m.timestamp or 'data não reconhecida'}] {m.author}: {m.text}"
        for m in messages
    )

