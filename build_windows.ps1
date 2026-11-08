param([switch]$DependenciesReady)

$ErrorActionPreference = "Stop"

$ProjectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$DistRoot = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "dist"))
$AppOutput = [System.IO.Path]::GetFullPath((Join-Path $DistRoot "WhatsAppAnalyzer"))
$ZipOutput = [System.IO.Path]::GetFullPath((Join-Path $DistRoot "WhatsAppAnalyzer-windows.zip"))

if (-not $DistRoot.StartsWith($ProjectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "A pasta de saída precisa ficar dentro do projeto."
}

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonCommand) {
        throw "Python não encontrado. Instale Python 3.11 ou crie o ambiente .venv do projeto."
    }
    $Python = $PythonCommand.Source
}

Push-Location $ProjectRoot
try {
    if (-not $DependenciesReady) {
        & $Python -c "import streamlit, pandas, pypdf, docx, openpyxl, pptx, PyInstaller" *> $null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Instalando as dependências do aplicativo e do empacotador..."
            & $Python -m pip install -r requirements-build.txt
            if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar as dependências de compilação." }
        }
    }

    Write-Host "Empacotando o aplicativo para Windows..."
    & $Python -m PyInstaller `
        --noconfirm `
        --onedir `
        --console `
        --name WhatsAppAnalyzer `
        --collect-data streamlit `
        --collect-data altair `
        --copy-metadata streamlit `
        --add-data "app.py;." `
        --add-data "src;src" `
        launcher.py
    if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar o executável com PyInstaller." }

    New-Item -ItemType Directory -Path $AppOutput -Force | Out-Null
    $EnvPath = Join-Path $AppOutput ".env"
    if (-not (Test-Path -LiteralPath $EnvPath)) {
        Copy-Item -LiteralPath (Join-Path $ProjectRoot ".env.ollama.example") -Destination $EnvPath
    }
    Copy-Item -LiteralPath (Join-Path $ProjectRoot "README_WINDOWS.txt") -Destination $AppOutput -Force

    if (Test-Path -LiteralPath $ZipOutput) {
        Remove-Item -LiteralPath $ZipOutput -Force
    }
    Compress-Archive -Path (Join-Path $AppOutput "*") -DestinationPath $ZipOutput -Force
    Write-Host "Executável: $AppOutput\WhatsAppAnalyzer.exe"
    Write-Host "Pacote ZIP: $ZipOutput"
}
finally {
    Pop-Location
}

