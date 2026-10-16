# Analisador de conversas e documentos

Aplicação local em Python e Streamlit para explorar conversas e documentos, localizar trechos e produzir análises assistidas por IA. A interface e as instruções enviadas ao modelo usam português.

## O que faz

- Lê arquivos TXT, Markdown, CSV, JSON, HTML, PDF, DOCX, XLSX e PPTX.
- Reconhece exportações de conversa com data, hora e participante, além de transcrições em linhas como `Ana: texto`.
- Trata os outros formatos como documentos, preservando referências às linhas do texto extraído. Não inventa participantes quando eles não estão identificados.
- Exibe métricas, frequência de palavras, busca por evidências e, para conversas datadas, filtros de período e estatísticas por participante.
- Oferece análise geral do conteúdo, identificação de interações potencialmente conflituosas, avaliação individual de episódios e síntese comparativa.
- Permite baixar evidências em CSV e o relatório em Markdown.

## Requisitos

- Windows e Python 3.10 ou mais recente.
- Para IA local: Ollama instalado e um modelo baixado. Sem IA, a leitura e as métricas locais continuam disponíveis.
- Para IA pela nuvem: uma chave de API compatível com a API de Chat Completions.

## Instalação no Windows

Abra o PowerShell na pasta `whatsapp-analyzer` e execute:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se o ambiente virtual já existir, ative-o e instale as dependências atualizadas:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configurar a IA (opcional)

### Ollama local (sem cobrança por chamada)

1. Instale o Ollama para Windows em <https://ollama.com/download>.
2. Abra um novo PowerShell e baixe/inicie o modelo recomendado:

```powershell
ollama run gemma3:4b
```

Na primeira execução, o Ollama baixa o modelo (cerca de 3,4 GB). Depois de aparecer o prompt do modelo, você pode sair com `/bye`; o serviço local fica disponível enquanto o Ollama estiver em execução.

O `.env` do projeto já está configurado para usar `gemma3:4b` em `http://localhost:11434/v1`. Reinicie o Streamlit depois de instalar/iniciar o Ollama. O modelo roda no seu computador; a velocidade depende do hardware.

### API GPT (configuração preservada)

As configurações anteriores da API foram preservadas no arquivo local `.env.openai` (ignorado pelo Git). Para voltar a usar essa configuração, copie-o sobre `.env`:

```powershell
Copy-Item .env.openai .env -Force
```

Se a chave salva tiver sido revogada, substitua o valor de `OPENAI_API_KEY` no `.env` por uma chave nova. Nunca compartilhe ou publique a chave. O `.gitignore` exclui os arquivos locais `.env` e `.env.openai`.

Depois de alterar `.env`, reinicie o Streamlit.

## Iniciar

Com o ambiente virtual ativado, execute na pasta do projeto:

```powershell
streamlit run app.py
```

O Streamlit abrirá a aplicação no navegador. Se o navegador não abrir automaticamente, use o endereço local mostrado no terminal.

## Usar a aplicação

1. Selecione um arquivo aceito na barra lateral.
2. Para exportações com datas, confira a opção de interpretar datas como dia/mês. A tela começa mostrando toda a conversa; use os campos **Início** e **Fim** para filtrar um período.
3. Consulte **Visão geral**, **Participantes**, **Ritmo** e **Evidências**. Arquivos sem uma estrutura de conversa reconhecida não têm estatísticas por participante ou período.
4. Na aba **Análise por IA**, solicite a análise geral das amostras.
5. Na aba **Interações**, solicite a identificação contextual. Selecione um resultado para avaliar suas condutas e, depois de analisar pelo menos dois episódios, você pode pedir uma síntese dos padrões entre eles.
6. Na aba **Relatório**, baixe o resultado em Markdown. As evidências também podem ser baixadas em CSV na aba correspondente.

## Como a análise de interações funciona

A detecção examina o período selecionado em blocos cronológicos com sobreposição, sem usar palavras isoladas como decisão de conflito. A interface informa o número estimado de blocos/chamadas antes de iniciar. Depois da detecção, a avaliação de um episódio e a síntese entre episódios são ações separadas, iniciadas por botões.

A avaliação individual considera início, provocação, desrespeito, escalada, argumentação, reciprocidade e reparação. As pontuações são estimativas interpretativas, não medidas científicas. O modelo pode errar, não determina intenção ou diagnóstico e não produz um veredito sobre as pessoas.

As citações são comparadas com o texto extraído e as linhas de origem. Citações que não correspondem ao material são removidas. Para PDF, DOCX, XLSX e PPTX, as referências se baseiam no texto extraído pelo leitor do formato, não necessariamente na paginação visual original.

## Formatos e limitações

| Formato | Leitura |
| --- | --- |
| TXT, Markdown, CSV, JSON e HTML | Texto extraído localmente |
| PDF | Texto incorporado no PDF |
| DOCX | Parágrafos e tabelas |
| XLSX | Valores das células das planilhas |
| PPTX | Texto das caixas de texto dos slides |

O programa não lê imagens, áudio ou vídeo. PDFs digitalizados que contêm apenas imagens precisam de OCR, que ainda não está incluído. Arquivos protegidos por senha, corrompidos ou fora da lista não são aceitos. A extração depende da estrutura e do texto realmente disponível em cada arquivo; por isso, não é possível garantir interpretação de qualquer tipo de arquivo.

## Privacidade e custos

O arquivo é lido localmente para extração e métricas. O texto só é enviado ao provedor configurado quando você clica em uma ação de IA. A análise geral envia amostras; a detecção de interações percorre os blocos do período selecionado e pode fazer várias chamadas. Avaliações individuais e sínteses também enviam conteúdo. O custo depende do tamanho do arquivo, do modelo e do provedor.

A aplicação não salva automaticamente os arquivos analisados na pasta `data/`. Evite enviar conteúdo sensível a um provedor sem antes verificar as regras de privacidade desse serviço.

## Estrutura do projeto

```text
whatsapp-analyzer/
├── app.py
├── requirements.txt
├── README.md
├── .env                 # configuração local; não publicar
├── .gitignore
├── src/
│   ├── analyzer.py
│   ├── chunker.py
│   ├── conflict_detector.py
│   ├── conflict_report.py
│   ├── document_loader.py
│   ├── episode_analyzer.py
│   ├── evidence_validator.py
│   ├── llm_client.py
│   ├── parser.py
│   ├── relationship_analyzer.py
│   ├── report.py
│   ├── responsibility_evaluator.py
│   └── statistics.py
├── tests/
└── data/                # reservado; conversas não são gravadas automaticamente
```

## Dependências principais

- `streamlit`: interface web local.
- `pandas`: tabelas e métricas.
- `pypdf`: extração de texto de PDF.
- `python-docx`: leitura de DOCX.
- `openpyxl`: leitura de XLSX.
- `python-pptx`: leitura de PPTX.

