# ============================================================
#  iniciar.ps1 — Inicia a Clube USA API (Windows)
#  Uso: .\iniciar.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "============================================================"
Write-Host "  CLUBE USA — Iniciando API"
Write-Host "============================================================"
Write-Host ""

# Verifica se .env existe
if (-not (Test-Path "$ROOT\.env")) {
    Write-Host "[ERRO] Arquivo .env nao encontrado." -ForegroundColor Red
    Write-Host "       Copie .env.example para .env e preencha as variaveis." -ForegroundColor Yellow
    exit 1
}

# Verifica se python esta disponivel
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRO] Python nao encontrado. Instale em python.org" -ForegroundColor Red
    exit 1
}

# Instala dependencias se necessario
Write-Host "[1/3] Verificando dependencias..."
python -m pip install -r "$ROOT\requirements.txt" --quiet

# Gera chaves de seguranca se .env ainda tem placeholders
$envContent = Get-Content "$ROOT\.env" -Raw
if ($envContent -match "gere_com") {
    Write-Host ""
    Write-Host "[AVISO] O .env tem valores placeholder de seguranca." -ForegroundColor Yellow
    Write-Host "        Execute o comando abaixo para gerar as chaves:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "        python clubeusa\utils\security.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "        Copie os valores gerados para o .env e execute este script novamente."
    exit 0
}

Write-Host "[2/3] Ambiente: $env:ENVIRONMENT"
Write-Host "[3/3] Iniciando servidor na porta $env:PORT (ou 8000)..."
Write-Host ""
Write-Host "API disponivel em: http://localhost:8000"
Write-Host "Health check:      http://localhost:8000/health"
Write-Host "Painel admin:      http://localhost:8000/admin"
Write-Host ""
Write-Host "Pressione Ctrl+C para parar."
Write-Host "============================================================"
Write-Host ""

Set-Location "$ROOT\clubeusa"
python api\run.py
