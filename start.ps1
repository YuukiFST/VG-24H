param(
    [string]$Port = "8000",
    [switch]$NoBrowser
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ProjectRoot "backend"
$VenvDir = Join-Path $BackendDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$LogFile = Join-Path $ProjectRoot "server.log"
$LogErrFile = Join-Path $ProjectRoot "server_err.log"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VG 24H - Portal de Servicos Publicos" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Cria o arquivo .env a partir do template se nao existir
$EnvFile = Join-Path $BackendDir ".env"
$EnvExample = Join-Path $BackendDir ".env.example"
if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Write-Host "Arquivo .env nao encontrado. Criando a partir de .env.example..." -ForegroundColor Yellow
        Copy-Item $EnvExample $EnvFile
        Write-Host ".env criado! Edite o arquivo com suas credenciais." -ForegroundColor Green
    } else {
        Write-Host "Arquivo .env nao encontrado. Crie o arquivo backend\.env manualmente com as suas credenciais." -ForegroundColor Yellow
        Write-Host "Use o modelo abaixo como referencia (sem as aspas simples):" -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "  SECRET_KEY='sua_chave_aqui'" -ForegroundColor DarkGray
        Write-Host "  DEBUG=True" -ForegroundColor DarkGray
        Write-Host "  ALLOWED_HOSTS=localhost,127.0.0.1" -ForegroundColor DarkGray
        Write-Host "  POSTGRES_DB=seu_banco" -ForegroundColor DarkGray
        Write-Host "  POSTGRES_USER=seu_usuario" -ForegroundColor DarkGray
        Write-Host "  POSTGRES_PASSWORD=sua_senha" -ForegroundColor DarkGray
        Write-Host "  POSTGRES_HOST=seu_host" -ForegroundColor DarkGray
        Write-Host "  POSTGRES_PORT=5432" -ForegroundColor DarkGray
        Write-Host "  POSTGRES_SSL=require" -ForegroundColor DarkGray
        Write-Host "  CLOUDINARY_URL=sua_url_cloudinary" -ForegroundColor DarkGray
        Write-Host ""
        exit 1
    }
}

# Cria o virtual environment automaticamente se nao existir
if (-not (Test-Path $PythonExe)) {
    Write-Host "Ambiente virtual nao encontrado. Criando..." -ForegroundColor Yellow
    python -m venv $VenvDir
    if (-not $?) {
        Write-Host "Erro ao criar ambiente virtual. Instale o Python e tente novamente." -ForegroundColor Red
        exit 1
    }
    Write-Host "Instalando dependencias..." -ForegroundColor Yellow
    & $PythonExe -m pip install -r (Join-Path $BackendDir "requirements.txt")
    if (-not $?) {
        Write-Host "Erro ao instalar dependencias." -ForegroundColor Red
        exit 1
    }
    Write-Host "Ambiente virtual configurado!" -ForegroundColor Green
}

# Mata processos antigos na porta
$listeners = netstat -ano | Select-String ":$Port"
foreach ($line in $listeners) {
    if ($line -match '\s+(\d+)$') {
        Stop-Process -Id $matches[1] -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep 1

"--- Servidor iniciado em $(Get-Date) ---" | Out-File $LogFile -Encoding UTF8

# Inicia o servidor Django (stdout e stderr em arquivos separados)
$proc = Start-Process -FilePath $PythonExe `
    -ArgumentList "-u manage.py runserver 0.0.0.0:$Port --noreload" `
    -WorkingDirectory $BackendDir `
    -WindowStyle Hidden `
    -PassThru `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError $LogErrFile

Write-Host "Aguardando servidor iniciar" -NoNewline

$timeout = 30
$started = $false

while ($timeout -gt 0) {
    try {
        $req = [System.Net.HttpWebRequest]::Create("http://127.0.0.1:$Port/")
        $req.Timeout = 1000
        $resp = $req.GetResponse()
        $resp.Close()
        $started = $true
        Write-Host " OK!" -ForegroundColor Green
        break
    } catch {
        # Servidor ainda nao responde
    }

    Write-Host "." -NoNewline
    Start-Sleep 1
    $timeout--
}

if (-not $started) {
    Write-Host " TIMEOUT" -ForegroundColor Red
    Write-Host "Verifique o log: $LogFile" -ForegroundColor Yellow
    Get-Content $LogFile -Tail 10 -ErrorAction SilentlyContinue
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Servidor VG 24H iniciado!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Local:   http://127.0.0.1:$Port/" -ForegroundColor Cyan

$lanIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.PrefixOrigin -eq 'Dhcp' -or $_.PrefixOrigin -eq 'Manual' } | Select-Object -First 1).IPAddress
if ($lanIp) {
    Write-Host "  Rede:    http://${lanIp}:$Port/" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "  Log:     $LogFile" -ForegroundColor DarkGray
Write-Host "  Erros:   $LogErrFile" -ForegroundColor DarkGray
Write-Host ""

if (-not $NoBrowser) {
    Start-Process "http://127.0.0.1:$Port/"
    Write-Host "  Navegador aberto automaticamente." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Para parar o servidor, feche este terminal ou pressione Ctrl+C" -ForegroundColor Yellow
Write-Host ""

while ($true) {
    Start-Sleep 10
    if ($proc.HasExited) {
        Write-Host "Servidor encerrado." -ForegroundColor Red
        break
    }
}
