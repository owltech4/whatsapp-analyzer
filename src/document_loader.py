from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

from .parser import Message, decode_upload, parse_chat

SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".html", ".htm", ".pdf", ".docx", ".xlsx", ".pptx"}


def extract_text(data: bytes, filename: str) -> str:
    """Extract readable text from common document and conversation exports."""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Formato não suportado: {suffix or 'sem extensão'}.")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ValueError("Para ler PDF, instale as dependências do projeto com pip install -r requirements.txt.") from exc
        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(f"[Página {number}]\n{text}" for number, text in enumerate(pages, 1))
    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise ValueError("Para ler DOCX, instale as dependências do projeto com pip install -r requirements.txt.") from exc
        doc = Document(BytesIO(data))
        paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                paragraphs.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(paragraphs)
    if suffix == ".xlsx":
        try:
            from openpyxl import load_workbook
        except ImportError as exc:
            raise ValueError("Para ler XLSX, instale as dependências do projeto com pip install -r requirements.txt.") from exc
        workbook = load_workbook(BytesIO(data), read_only=True, data_only=True)
        rows = []
        for sheet in workbook.worksheets:
            rows.append(f"[Planilha: {sheet.title}]")
            for row in sheet.iter_rows(values_only=True):
                values = [str(value) for value in row if value is not None]
                if values:
                    rows.append(" | ".join(values))
        return "\n".join(rows)
    if suffix == ".pptx":
        try:
            from pptx import Presentation
        except ImportError as exc:
            raise ValueError("Para ler PPTX, instale as dependências do projeto com pip install -r requirements.txt.") from exc
        presentation = Presentation(BytesIO(data))
        slides = []
        for number, slide in enumerate(presentation.slides, 1):
            paragraphs = [shape.text for shape in slide.shapes if getattr(shape, "has_text_frame", False) and shape.text.strip()]
            slides.append(f"[Slide {number}]\n" + "\n".join(paragraphs))
        return "\n\n".join(slides)
    text = decode_upload(data)
    if suffix in {".html", ".htm"}:
        text = re.sub(r"(?is)<(script|style)\b.*?>.*?</\1>", " ", text)
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        text = re.sub(r"&nbsp;", " ", text, flags=re.I)
        text = re.sub(r"&amp;", "&", text, flags=re.I)
        text = re.sub(r"&lt;", "<", text, flags=re.I)
        text = re.sub(r"&gt;", ">", text, flags=re.I)
    return text


def load_document(data: bytes, filename: str, day_first: bool = True) -> tuple[list[Message], int, str, bool]:
    """Load a supported file and report whether a timestamped chat was recognized.

    Chat exports retain their native message parsing. Other readable documents are
    represented as source-lined text so citations continue to point to stable lines.
    """
    text = extract_text(data, filename)
    parsed, line_count = parse_chat(text, day_first)
    if parsed:
        return parsed, line_count, Path(filename).suffix.lower(), True
    lines = text.splitlines()
    speaker_pattern = re.compile(r"^([^:\n]{1,80}):\s+(.*)$")
    tagged = [(index, speaker_pattern.match(line)) for index, line in enumerate(lines, 1)]
    tagged_lines = [(index, match) for index, match in tagged if match and match.group(1).strip()]
    speakers = {match.group(1).strip() for _, match in tagged_lines}
    if len(speakers) >= 2 and len(tagged_lines) >= 2 and len(tagged_lines) / max(1, sum(bool(line.strip()) for line in lines)) >= 0.6:
        messages = [Message(None, match.group(1).strip(), match.group(2).strip(), index)
                    for index, match in tagged_lines if match.group(2).strip()]
        return messages, len(lines), Path(filename).suffix.lower(), True
    messages = [Message(None, "Documento", line.strip(), index)
                for index, line in enumerate(lines, 1) if line.strip()]
    return messages, len(lines), Path(filename).suffix.lower(), False
