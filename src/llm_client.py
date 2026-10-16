from __future__ import annotations
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

class LLMError(RuntimeError):
    pass

def configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())

def _request(text: str, prompt: str, json_mode: bool = False) -> str:
    """Call an OpenAI-compatible endpoint after an explicit user action."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise LLMError("Configure o provedor de IA no arquivo .env para usar a análise por IA.")
    model = os.getenv("OPENAI_MODEL", "o4-mini").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    timeout = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "120"))
    payload = {
        "model": model, "temperature": 0.2,
        "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}],
    }
    is_local = base_url.startswith(("http://localhost:", "http://127.0.0.1:"))
    is_qwen3 = model.lower().startswith("qwen3")
    if is_local:
        payload["max_tokens"] = int(os.getenv("OPENAI_MAX_TOKENS", "3000"))
        if is_qwen3:
            # Qwen3 otherwise spends its output budget on <think> and can return no final answer.
            payload["reasoning_effort"] = "none"
            payload["messages"][-1]["content"] += "\n/no_think"
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    request = Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        choice = result["choices"][0]
        content = choice["message"]["content"]
        if not isinstance(content, str):
            raise LLMError("O provedor retornou uma resposta sem texto. Confira o modelo e o endpoint configurados.")
        if is_local and is_qwen3:
            end_thinking = content.rfind("</think>")
            if end_thinking >= 0:
                content = content[end_thinking + len("</think>"):].strip()
            elif "<think>" in content:
                raise LLMError(
                    "O Qwen3 atingiu o limite de geração antes da resposta final. Tente reduzir o tamanho do trecho amostrado em .env."
                )
        if not content.strip():
            raise LLMError("O modelo terminou sem gerar uma resposta final. Tente novamente com um trecho menor.")
        return content
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise LLMError(f"Provedor de IA retornou HTTP {exc.code}: {detail}") from exc
    except TimeoutError as exc:
        raise LLMError(
            f"A análise excedeu o limite de {timeout} segundos. Tente reduzir os trechos amostrados ou o tamanho do trecho em .env."
        ) from exc
    except (URLError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        if isinstance(getattr(exc, "reason", None), TimeoutError):
            raise LLMError(
                f"A análise excedeu o limite de {timeout} segundos. Tente reduzir os trechos amostrados ou o tamanho do trecho em .env."
            ) from exc
        raise LLMError(f"Não foi possível concluir a análise por IA: {exc}") from exc

def analyze_text(text: str, prompt: str) -> str:
    return _request(text, prompt)

def analyze_json(text: str, prompt: str) -> dict:
    raw = _request(text, prompt, json_mode=True).strip()
    fence = chr(96) * 3
    if raw.startswith(fence):
        raw = raw.split("\n", 1)[-1]
        if raw.rstrip().endswith(fence):
            raw = raw.rstrip()[:-len(fence)].strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMError(f"O modelo retornou JSON inválido: {exc}") from exc
    if not isinstance(result, dict):
        raise LLMError("O modelo retornou um formato inesperado; era esperado um objeto JSON.")
    return result

