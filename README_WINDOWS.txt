ANALISADOR DE CONVERSAS — WINDOWS

1. Extraia a pasta inteira do ZIP. Não mova o arquivo .exe para fora dela.
2. Abra WhatsAppAnalyzer.exe. Uma janela de terminal acompanha o servidor local; feche-a para encerrar o app.
3. A configuração inicial usa Ollama em http://localhost:11434/v1 e o modelo gemma3:4b.
4. Instale o Ollama e baixe o modelo separadamente. O executável não inclui o modelo de IA.
5. Para trocar o modelo ou configurar outro provedor, edite o arquivo .env ao lado do executável e reinicie o app.

As conversas são lidas no computador. O servidor fica limitado a 127.0.0.1 e não é exposto à rede.
Se configurar um provedor na nuvem, os trechos enviados para análise por IA serão enviados a esse provedor.

