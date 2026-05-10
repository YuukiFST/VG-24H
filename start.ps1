param(
    [string]$Port = "8000",
    [switch]$NoBrowser
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ProjectRoot "backend"
$LogFile = Join-Path $ProjectRoot "server.log"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VG 24H - Portal de Servicos Publicos" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Mata processos antigos na porta
$listeners = netstat -ano | Select-String ":$Port"
foreach ($line in $listeners) {
    if ($line -match '\s+(\d+)$') {
        Stop-Process -Id $matches[1] -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep 1

"--- Servidor iniciado em $(Get-Date) ---" | Out-File $LogFile -Encoding UTF8

# Inicia o servidor Django redirecionando a saida direto para o log
$pythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"
$args = "-u manage.py runserver 0.0.0.0:$Port --noreload"
$cmdArgs = "/c `"$pythonExe -u manage.py runserver 0.0.0.0:$Port --noreload > `"$LogFile`" 2>&1`""
$proc = Start-Process -FilePath "cmd.exe" -ArgumentList $cmdArgs -WorkingDirectory $BackendDir -WindowStyle Hidden -PassThru

Write-Host "Aguardando servidor iniciar" -NoNewline

$timeout = 30
$started = $false

while ($timeout -gt 0) {
    if (Test-Path $LogFile) {
        # Le o conteudo do arquivo log sem travar
        $content = Get-Content $LogFile -ErrorAction SilentlyContinue
        if ($content -match "Starting development server") {
            $started = $true
            Write-Host " OK!" -ForegroundColor Green
            break
        }
    }
    
    Write-Host "." -NoNewline
    Start-Sleep 1
    $timeout--
}

if (-not $started) {
    Write-Host " TIMEOUT" -ForegroundColor Red
    Write-Host "Verifique o log: $LogFile" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Servidor VG 24H iniciado!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Local:   http://127.0.0.1:$Port/" -ForegroundColor Cyan

# Mostra o IP da rede local para acesso por outros dispositivos
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.PrefixOrigin -eq 'Dhcp' -or $_.PrefixOrigin -eq 'Manual' } | Select-Object -First 1).IPAddress
if ($lanIp) {
    Write-Host "  Rede:    http://${lanIp}:$Port/" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "  Log:     $LogFile" -ForegroundColor DarkGray
Write-Host ""

if (-not $NoBrowser) {
    Start-Process "http://127.0.0.1:$Port/"
    Write-Host "  Navegador aberto automaticamente." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Para parar o servidor, feche este terminal ou pressione Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# Mantem o script rodando (para o servidor nao morrer)
while ($true) {
    Start-Sleep 10
    if ($proc.HasExited) {
        Write-Host "Servidor encerrado." -ForegroundColor Red
        break
    }
}
