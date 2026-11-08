from __future__ import annotations

import os
from pathlib import Path
import sys

# Make the modules loaded dynamically by Streamlit visible to PyInstaller's
# static import analysis.
import src.analyzer
import src.chunker
import src.conflict_detector
import src.conflict_report
import src.document_loader
import src.episode_analyzer
import src.llm_client
import src.parser
import src.relationship_analyzer
import src.report
import src.statistics
import pypdf
import docx
import openpyxl
import pptx


def _bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def _load_external_env() -> None:
    """Load an optional .env beside the executable without bundling secrets."""
    if getattr(sys, "frozen", False):
        env_path = Path(sys.executable).resolve().parent / ".env"
    else:
        env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and not os.environ.get(key, "").strip():
            os.environ[key] = value


def main() -> None:
    _load_external_env()
    app_path = _bundle_root() / "app.py"
    if not app_path.exists():
        raise FileNotFoundError(f"Não encontrei o aplicativo: {app_path}")

    # Keep the server bound to this computer. The executable opens the local app
    # in the browser and does not expose the uploaded conversation on the network.
    headless = os.environ.get("WHATSAPP_ANALYZER_HEADLESS", "false").strip().lower() == "true"
    port = os.environ.get("WHATSAPP_ANALYZER_PORT", "8501").strip()
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        raise ValueError("WHATSAPP_ANALYZER_PORT precisa ser uma porta entre 1 e 65535.")
    sys.argv = [
        "streamlit", "run", str(app_path),
        "--server.address=127.0.0.1",
        f"--server.headless={str(headless).lower()}",
        f"--server.port={port}",
        "--global.developmentMode=false",
        "--browser.gatherUsageStats=false",
    ]
    from streamlit.web.cli import main as streamlit_main

    streamlit_main()


if __name__ == "__main__":
    main()

